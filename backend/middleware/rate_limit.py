"""Rate limiting middleware using slowapi."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_user_key(request: Request) -> str:
    """Return the user ID if authenticated, else fallback to IP."""
    user = getattr(request.state, "user", None)
    if user:
        return user.firebase_uid
    return get_remote_address(request)


def build_limiter(default_limit: str = "") -> Limiter:
    """Create the limiter; ``default_limit`` ("120/minute") applies to every route.

    Routes decorated with ``@limiter.limit`` keep their own, stricter limit and
    are keyed per user. The default is enforced by ``SlowAPIMiddleware`` before
    authentication runs, so it is necessarily keyed per client IP.
    """
    return Limiter(
        key_func=get_user_key,
        default_limits=[default_limit] if default_limit else [],
    )


def _default_limit() -> str:
    from config import settings  # noqa: PLC0415

    return settings.default_rate_limit


limiter = build_limiter(_default_limit())
