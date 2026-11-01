"""Router for the image enhancement endpoint."""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.session import get_db
from middleware.auth import get_current_user
from middleware.rate_limit import limiter
from models.database import (
    AuditLog,
    EnhancementJob,
    ModelConfig,
    User,
    UserUsageStats,
)
from schemas.enhance import EnhancementJobResponse
from services.image_utils import inspect_image
from services.srgan import InferenceOOMError, enhance_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhance", tags=["enhance"])

# Max concurrent inferences (prevents OOM on GPU/CPU)
inference_semaphore = asyncio.Semaphore(1)

_EXT_FOR_FORMAT = {"JPEG": ".jpg", "PNG": ".png"}
_READ_CHUNK = 64 * 1024


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    """Read an upload in chunks, aborting as soon as it exceeds `limit` bytes."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(_READ_CHUNK):
        total += len(chunk)
        if total > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {limit} bytes",
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def _record_stats(db: AsyncSession, user_id: str, *, success: bool) -> None:
    """Update the user's usage counters, creating the row if it is missing."""
    result = await db.execute(
        select(UserUsageStats).where(UserUsageStats.user_id == user_id)
    )
    stats = result.scalar_one_or_none()
    if stats is None:
        stats = UserUsageStats(user_id=user_id)
        db.add(stats)
    stats.total_jobs = (stats.total_jobs or 0) + 1
    if success:
        stats.successful_jobs = (stats.successful_jobs or 0) + 1
    else:
        stats.failed_jobs = (stats.failed_jobs or 0) + 1
    stats.last_job_at = datetime.now(timezone.utc)


def _remove_files(*paths: Path | None) -> None:
    for path in paths:
        if path is None:
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Could not remove %s: %s", path, exc)


async def _mark_failed(
    db: AsyncSession, job_id: str, user_id: str, message: str
) -> None:
    """Record a failed job. Never raises: the caller is already handling an error."""
    try:
        await db.rollback()  # discard any half-applied changes
        job = await db.get(EnhancementJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error_message = message[:500]
        await _record_stats(db, user_id, success=False)
        await db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Could not record failure for job %s", job_id)


@router.post("", response_model=EnhancementJobResponse)
@limiter.limit("5/minute")
async def create_enhancement_job(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    scale: Annotated[int, Form()] = 4,
):
    """Upscale an uploaded low-resolution image using Real-ESRGAN."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No file attached"
        )

    if scale not in [2, 4, 8]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scale factor must be 2, 4, or 8.",
        )

    # Read with a hard cap, then validate from the header only (no pixel decode).
    input_bytes = await _read_limited(file, settings.max_upload_bytes)

    try:
        img_format, input_w, input_h = inspect_image(input_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc

    if input_w * input_h > settings.max_input_pixels:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Image is {input_w}x{input_h}; maximum is "
                f"{settings.max_input_pixels} pixels."
            ),
        )
    if input_w * input_h * scale * scale > settings.max_output_pixels:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Output at {scale}x would be too large. Try a smaller image or scale.",
        )

    ext = _EXT_FOR_FORMAT[img_format]

    model_config_result = await db.execute(
        select(ModelConfig).where(ModelConfig.scale_factor == scale)
    )
    model_config = model_config_result.scalar_one_or_none()
    if not model_config:
        logger.error("No ModelConfig found in database!")
        raise HTTPException(status_code=500, detail="Server configuration error")

    job_id = str(uuid4())
    user_id = str(current_user.id)
    input_filepath = Path(settings.upload_dir) / user_id / f"{job_id}{ext}"
    result_filepath = Path(settings.results_dir) / user_id / f"{job_id}.png"

    job = EnhancementJob(
        id=job_id,
        user_id=current_user.id,
        model_config_id=model_config.id,
        original_filename=file.filename,
        input_file_path=str(input_filepath),
        input_size_bytes=len(input_bytes),
        input_width=input_w,
        input_height=input_h,
        input_format=img_format,
        status="pending",
        scale_factor=scale,
    )
    db.add(job)
    await db.commit()

    # Everything after the job row exists is inside one handler, so any failure
    # (disk, inference, DB) ends with the job marked failed and files removed.
    try:
        input_filepath.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(input_filepath.write_bytes, input_bytes)

        job.status = "processing"
        await db.commit()

        try:
            await asyncio.wait_for(
                inference_semaphore.acquire(), timeout=settings.queue_timeout_seconds
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Server is busy. Please retry shortly.",
                headers={"Retry-After": "30"},
            ) from None
        try:
            result_bytes, metadata = await asyncio.to_thread(
                enhance_image, input_bytes, scale
            )
        finally:
            inference_semaphore.release()

        result_filepath.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(result_filepath.write_bytes, result_bytes)

        job.status = "completed"
        job.input_width = metadata.get("input_width")
        job.input_height = metadata.get("input_height")
        job.output_width = metadata.get("output_width")
        job.output_height = metadata.get("output_height")
        job.output_file_path = str(result_filepath)
        job.output_size_bytes = len(result_bytes)
        job.processing_time_ms = metadata.get("processing_time_ms")
        job.completed_at = datetime.now(timezone.utc)

        await _record_stats(db, current_user.id, success=True)
        db.add(
            AuditLog(
                user_id=current_user.id,
                action="job.completed",
                ip_address=request.client.host if request.client else "",
            )
        )
        await db.commit()
    except Exception as exc:
        logger.error("Enhancement failed for job %s: %s", job_id, exc)
        _remove_files(input_filepath, result_filepath)
        await _mark_failed(db, job_id, current_user.id, str(exc))

        if isinstance(exc, HTTPException):
            raise
        if isinstance(exc, InferenceOOMError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image too large for current server capacity.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image enhancement failed due to an internal error.",
        ) from exc

    return EnhancementJobResponse(
        job_id=job.id,
        status=job.status,
        result_url=f"/api/results/{job_id}.png",
        input_w=job.input_width,
        input_h=job.input_height,
        output_w=job.output_width,
        output_h=job.output_height,
        processing_time_ms=job.processing_time_ms,
    )
