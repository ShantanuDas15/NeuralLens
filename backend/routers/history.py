"""Router for the job history endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from db.session import get_db
from middleware.auth import get_current_user
from models.database import EnhancementJob, User
from schemas.history import HistoryPaginatedResponse

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryPaginatedResponse)
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """Retrieve the user's completed enhancement jobs with pagination."""
    # Base query for completed and non-deleted jobs for the current user
    base_query = select(EnhancementJob).where(
        EnhancementJob.user_id == current_user.id,
        EnhancementJob.status == "completed",
        EnhancementJob.deleted_at.is_(None),
    )

    # 1. Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # 2. Get paginated items
    offset = (page - 1) * page_size
    items_query = (
        base_query.order_by(EnhancementJob.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items_result = await db.execute(items_query)
    jobs = items_result.scalars().all()

    # 3. Format response
    # The HistoryItem schema will extract fields matching from the ORM object automatically
    # because of from_attributes=True, but we need to alias `id` to `job_id`.
    # Pydantic doesn't do that by default unless we set aliases, or we can just map it here.
    items = []
    for job in jobs:
        items.append(
            {
                "job_id": job.id,
                "status": job.status,
                "original_filename": job.original_filename,
                "input_w": job.input_width,
                "input_h": job.input_height,
                "output_w": job.output_width,
                "output_h": job.output_height,
                "scale_factor": job.scale_factor,
                "processing_time_ms": job.processing_time_ms,
                "created_at": job.created_at,
                "result_url": (
                    f"/api/results/{job.id}.png" if job.status == "completed" else None
                ),
            }
        )

    return HistoryPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_job(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Soft-delete an enhancement job (sets deleted_at)."""
    # Find the job ensuring it belongs to the current user
    result = await db.execute(
        select(EnhancementJob).where(
            EnhancementJob.id == job_id,
            EnhancementJob.user_id == current_user.id,
            EnhancementJob.deleted_at.is_(None)
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found or already deleted"
        )

    # Soft delete
    job.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    
    return None
