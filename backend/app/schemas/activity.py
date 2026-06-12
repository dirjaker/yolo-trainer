"""Activity schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    """Schema for activity response."""
    id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    """Schema for activity list response."""
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
