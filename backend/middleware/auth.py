"""Firebase Auth Middleware.

Provides the `get_current_user` FastAPI dependency which:
1. Validates the Firebase ID token.
2. Synchronises the Firebase user to the local PostgreSQL/SQLite database.
3. Pre-initialises usage stats and logs the login event.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import InvalidIdTokenError, RevokedIdTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.database import AuditLog, User, UserUsageStats

logger = logging.getLogger(__name__)


async def get_current_user(
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
        decoded_token = firebase_auth.verify_id_token(token, check_revoked=True)
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
        logger.warning("Token missing uid or email: %s", decoded_token)
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

    if user is None:
        # Create new user
        is_first_login = True
        user = User(
            firebase_uid=uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            last_login_at=now,
        )
        db.add(user)
        # Flush to generate user.id before referencing it in other tables
        await db.flush()
    else:
        # Update existing user
        user.email = email
        if display_name:
            user.display_name = display_name
        if photo_url:
            user.photo_url = photo_url
        user.last_login_at = now

    # 6. Upsert user_usage_stats (if first login)
    if is_first_login:
        stats = UserUsageStats(user_id=user.id)
        db.add(stats)

    # 7. Insert AuditLog
    audit_log = AuditLog(
        user_id=user.id,
        action="user.login",
    )
    db.add(audit_log)

    # The session is committed automatically by the `get_db` dependency's yield block
    # so we just return the user object here.
    return user
