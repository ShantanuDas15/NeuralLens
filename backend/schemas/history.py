"""Schemas for the job history API."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistoryItem(BaseModel):
    """Response model for a single item in the history list."""
    
    job_id: UUID
    status: str
    original_filename: str
    input_w: int | None = None
    input_h: int | None = None
    output_w: int | None = None
    output_h: int | None = None
    scale_factor: float
    processing_time_ms: int | None = None
    created_at: datetime
    result_url: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class HistoryPaginatedResponse(BaseModel):
    """Paginated response containing multiple history items."""
    
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int
