"""Router for fetching result images."""

import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_db
from middleware.auth import get_current_user
from models.database import EnhancementJob, User

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{filename}")
async def get_result_image(
    filename: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Serve the SR result image file securely."""
    # Extract job_id from filename (assuming filename format: {job_id}.png)
    try:
        job_id_str = Path(filename).stem
        job_id = UUID(job_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    # Verify user owns the file via DB
    job_result = await db.execute(
        select(EnhancementJob).where(
            EnhancementJob.id == job_id, EnhancementJob.deleted_at.is_(None)
        )
    )
    job = job_result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Construct filepath
    user_results_dir = Path(settings.results_dir) / str(current_user.id)
    result_filepath = user_results_dir / filename

    if not result_filepath.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk"
        )

    return FileResponse(path=result_filepath, media_type="image/png")
