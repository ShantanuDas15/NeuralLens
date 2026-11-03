"""Firebase Auth Middleware.

Provides the `get_current_user` FastAPI dependency which:
1. Validates the Firebase ID token.
2. Synchronises the Firebase user to the local PostgreSQL/SQLite database.
3. Pre-initialises usage stats and logs the login event.
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import InvalidIdTokenError, RevokedIdTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.database import AuditLog, User, UserUsageStats

logger = logging.getLogger(__name__)

# A session counts as a new "login" (one audit row, one last_login_at write)
# only after this much quiet. Every API call is token-authenticated, so
# recording each one would write to the DB on every request, thumbnails included.
LOGIN_REFRESH_INTERVAL = timedelta(hours=1)


def _is_stale(last_login_at: datetime | None, now: datetime) -> bool:
    if last_login_at is None:
        return True
    if last_login_at.tzinfo is None:  # SQLite returns naive datetimes
        last_login_at = last_login_at.replace(tzinfo=timezone.utc)
    return now - last_login_at >= LOGIN_REFRESH_INTERVAL


async def get_current_user(
    request: Request,
    authorization: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Verify Firebase ID token and return the synchronised local User object.

    Raises 401 if the token is invalid, expired, revoked, or malformed.
    """
    # 1. Extract token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'.",
        )

    token = authorization.split("Bearer ")[1].strip()

    # 2 & 3. Verify token with Firebase Admin SDK
    try:
        decoded_token = await asyncio.to_thread(
            firebase_auth.verify_id_token, token, check_revoked=True
        )
    except (InvalidIdTokenError, RevokedIdTokenError, ValueError) as exc:
        logger.warning("Firebase auth failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    # 4. Extract uid and email
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    if not uid or not email:
        logger.warning(
            "Token missing uid or email (claims present: %s)", sorted(decoded_token)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token must contain uid and email.",
        )

    display_name = decoded_token.get("name")
    photo_url = decoded_token.get("picture")

    # 5. Upsert User
    now = datetime.now(timezone.utc)
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalar_one_or_none()

    is_first_login = False
    record_login = False

    if user is None:
        # The SPA fires several requests at once on first sign-in, so two of
        # them can reach this insert together. The unique constraint makes one
        # lose; the savepoint lets it recover and use the winner's row.
        user = User(
            firebase_uid=uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            last_login_at=now,
        )
        try:
            async with db.begin_nested():
                db.add(user)
                # Flush to generate user.id before referencing it elsewhere
                await db.flush()
            is_first_login = True
            record_login = True
        except IntegrityError:
            result = await db.execute(select(User).where(User.firebase_uid == uid))
            user = result.scalar_one_or_none()
            if user is None:
                # Same email, different Firebase account.
                logger.warning("Email already linked to another account")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists.",
                ) from None
    else:
        user.email = email
        if display_name:
            user.display_name = display_name
        if photo_url:
            user.photo_url = photo_url
        if _is_stale(user.last_login_at, now):
            user.last_login_at = now
            record_login = True

    # 6. Initialise usage stats (first login only)
    if is_first_login:
        db.add(UserUsageStats(user_id=user.id))

    # 7. Audit log (first login, or a fresh session after a quiet period)
    if record_login:
        db.add(AuditLog(user_id=user.id, action="user.login"))

    # The session is committed automatically by the `get_db` dependency's yield block
    # so we just return the user object here.
    request.state.user = user
    return user
