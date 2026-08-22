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


# Default to user_key to rate limit per user
limiter = Limiter(key_func=get_user_key)
