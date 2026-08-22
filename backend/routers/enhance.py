"""Router for the image enhancement endpoint."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_db
from middleware.auth import get_current_user
from models.database import AuditLog, EnhancementJob, User, UserUsageStats
from schemas.enhance import EnhancementJobResponse
from services.srgan import enhance_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhance", tags=["enhance"])


def _get_extension(filename: str | None) -> str:
    if not filename:
        return ".png"
    ext = Path(filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        return ".png"
    return ext


@router.post("", response_model=EnhancementJobResponse)
async def create_enhancement_job(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Upscale an uploaded low-resolution image using Real-ESRGAN."""
    # 1 & 2. Validate file presence and format
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No file attached"
        )

    ext = _get_extension(file.filename)
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Only JPEG and PNG are allowed.",
        )

    # Read bytes and validate size
    input_bytes = await file.read()
    if len(input_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_bytes} bytes",
        )

    # 2.5 Decode to get dimensions
    from services.image_utils import validate_and_decode
    try:
        img_arr = validate_and_decode(input_bytes, settings.max_upload_bytes)
        input_h, input_w = img_arr.shape[:2]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc)
        )

    # 3. Create EnhancementJob row (pending)
    job_id = str(uuid4())
    now = datetime.now(timezone.utc)
    
    # Needs a model_config_id. We'll query for the first available RealESRGAN model
    # (Since we seeded it in the migrations, it should exist, or we can just leave it None if nullable, but it's nullable=False)
    from models.database import ModelConfig
    model_config_result = await db.execute(select(ModelConfig).limit(1))
    model_config = model_config_result.scalar_one_or_none()
    if not model_config:
        logger.error("No ModelConfig found in database!")
        raise HTTPException(status_code=500, detail="Server configuration error")

    user_upload_dir = Path(settings.upload_dir) / str(current_user.id)
    input_filepath = user_upload_dir / f"{job_id}{ext}"

    job = EnhancementJob(
        id=job_id,
        user_id=current_user.id,
        model_config_id=model_config.id,
        original_filename=file.filename,
        input_file_path=str(input_filepath),
        input_size_bytes=len(input_bytes),
        input_width=input_w,
        input_height=input_h,
        input_format=ext.replace(".", "").upper(),
        status="pending",
        scale_factor=4.0,
    )
    db.add(job)
    await db.commit()

    # 4. Write input file
    user_upload_dir = Path(settings.upload_dir) / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    input_filepath = user_upload_dir / f"{job_id}{ext}"
    input_filepath.write_bytes(input_bytes)

    # 5. Update job status to processing
    job.status = "processing"
    await db.commit()

    # 6. Run enhancement (in a threadpool since it's CPU/GPU bound and blocking)
    try:
        # Run blocking inference in a separate thread so we don't block the async event loop
        result_bytes, metadata = await asyncio.to_thread(enhance_image, input_bytes)
    except Exception as exc:
        logger.error("Inference failed for job %s: %s", job_id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        
        # Update failed stats
        stats_res = await db.execute(select(UserUsageStats).where(UserUsageStats.user_id == current_user.id))
        stats = stats_res.scalar_one()
        stats.total_jobs += 1
        stats.failed_jobs += 1
        stats.last_job_at = datetime.now(timezone.utc)
        
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image enhancement failed due to an internal error.",
        ) from exc

    # 7. Write output to results
    user_results_dir = Path(settings.results_dir) / str(current_user.id)
    user_results_dir.mkdir(parents=True, exist_ok=True)
    result_filename = f"{job_id}.png"
    result_filepath = user_results_dir / result_filename
    result_filepath.write_bytes(result_bytes)

    result_url = f"/api/results/{result_filename}"

    # 8. Update job row -> completed
    job.status = "completed"
    job.input_width = metadata.get("input_width")
    job.input_height = metadata.get("input_height")
    job.output_width = metadata.get("output_width")
    job.output_height = metadata.get("output_height")
    job.output_file_path = str(result_filepath)
    job.output_size_bytes = len(result_bytes)
    job.processing_time_ms = metadata.get("processing_time_ms")

    # 9. Update stats
    stats_res = await db.execute(select(UserUsageStats).where(UserUsageStats.user_id == current_user.id))
    stats = stats_res.scalar_one()
    stats.total_jobs += 1
    stats.successful_jobs += 1
    stats.last_job_at = datetime.now(timezone.utc)

    # 10. Audit Log
    db.add(AuditLog(user_id=current_user.id, action="job.completed", ip_address=""))

    await db.commit()

    # 11. Return response
    return EnhancementJobResponse(
        job_id=job.id,
        status=job.status,
        result_url=result_url,
        input_w=job.input_width,
        input_h=job.input_height,
        output_w=job.output_width,
        output_h=job.output_height,
        processing_time_ms=job.processing_time_ms,
    )
