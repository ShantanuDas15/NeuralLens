"""Router for the user profile endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.session import get_db
from middleware.auth import get_current_user
from models.database import User, UserUsageStats
from schemas.profile import ProfileResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve the user's profile and aggregated usage statistics."""
    
    # In auth.py, we only yielded the `User` object. We need to fetch the stats.
    # We do a direct query for the stats since it's a 1-to-1 mapping.
    stats_result = await db.execute(
        select(UserUsageStats).where(UserUsageStats.user_id == current_user.id)
    )
    stats = stats_result.scalar_one_or_none()
    
    if not stats:
        # Fallback if somehow stats didn't get created
        stats_dict = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "last_job_at": None
        }
    else:
        stats_dict = {
            "total_jobs": stats.total_jobs,
            "successful_jobs": stats.successful_jobs,
            "failed_jobs": stats.failed_jobs,
            "last_job_at": stats.last_job_at
        }
        
    return {
        "uid": current_user.firebase_uid,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "photo_url": current_user.photo_url,
        "auth_provider": "firebase",  # hardcoded as specified or derived if needed
        "member_since": current_user.created_at,
        "stats": stats_dict
    }
