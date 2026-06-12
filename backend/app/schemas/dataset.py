"""Dataset schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetFormat(str, Enum):
    """Supported dataset formats."""
    YOLO = "yolo"
    COCO = "coco"
    VOC = "voc"


class DatasetStatus(str, Enum):
    """Dataset processing status."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DatasetCreate(BaseModel):
    """Schema for creating a dataset."""
    name: str = Field(..., min_length=1, max_length=200, description="Dataset name")
    description: Optional[str] = Field(default=None, max_length=1000, description="Dataset description")
    format: DatasetFormat = Field(default=DatasetFormat.YOLO, description="Dataset format")


class DatasetResponse(BaseModel):
    """Schema for dataset response."""
    id: int
    name: str
    description: Optional[str] = None
    format: DatasetFormat
    classes: Optional[List[str]] = None
    stats: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    status: DatasetStatus = DatasetStatus.UPLOADING
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for paginated dataset list response."""
    items: List[DatasetResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
