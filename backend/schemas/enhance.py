"""Schemas for enhancement API responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EnhancementJobResponse(BaseModel):
    """Response model for a single enhancement job."""

    job_id: UUID
    status: str
    result_url: str | None = None
    input_w: int | None = None
    input_h: int | None = None
    output_w: int | None = None
    output_h: int | None = None
    processing_time_ms: int | None = None

    model_config = ConfigDict(from_attributes=True)
