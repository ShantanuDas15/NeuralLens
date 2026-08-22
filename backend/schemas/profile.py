"""Schemas for the user profile API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserStatsModel(BaseModel):
    """Usage statistics embedded inside the user profile."""
    
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    last_job_at: Optional[datetime] = None


class ProfileResponse(BaseModel):
    """Response model for the user profile endpoint."""
    
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    auth_provider: str
    member_since: datetime
    stats: UserStatsModel
    
    model_config = ConfigDict(from_attributes=True)
