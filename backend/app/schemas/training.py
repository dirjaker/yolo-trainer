"""Training schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TrainingStatus(str, Enum):
    """Training job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingConfig(BaseModel):
    """Training configuration parameters."""
    epochs: int = Field(default=100, ge=1, le=10000, description="Number of training epochs")
    batch_size: int = Field(default=16, ge=1, le=512, description="Batch size")
    img_size: int = Field(default=640, ge=32, le=4096, description="Image size for training")
    learning_rate: float = Field(default=0.01, gt=0, le=1.0, description="Initial learning rate")
    optimizer: str = Field(default="SGD", description="Optimizer (SGD, Adam, AdamW, etc.)")
    device: str = Field(default="0", description="Training device (cpu, 0, 0,1, etc.)")
    workers: int = Field(default=8, ge=0, le=32, description="Number of data loading workers")
    patience: int = Field(default=50, ge=0, le=1000, description="Early stopping patience")
    amp: bool = Field(default=True, description="Use Automatic Mixed Precision")


ALLOWED_MODEL_VERSIONS = Literal[
    "yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x",
    "yolov5n", "yolov5s", "yolov5m", "yolov5l", "yolov5x",
    "yolov9t", "yolov9s", "yolov9m", "yolov9c", "yolov9e",
    "yolov10n", "yolov10s", "yolov10m", "yolov10b", "yolov10l", "yolov10x",
]


class TrainingCreate(BaseModel):
    """Schema for creating a training job."""
    name: str = Field(..., min_length=1, max_length=200, description="Training job name")
    model_version: ALLOWED_MODEL_VERSIONS = Field(
        default="yolov8n",
        description="YOLO model version",
    )
    dataset_id: uuid.UUID = Field(..., description="Dataset ID to use for training")
    config: Optional[TrainingConfig] = Field(default=None, description="Training configuration")


class TrainingResponse(BaseModel):
    """Schema for training job response."""
    id: uuid.UUID
    name: str
    model_version: str
    dataset_id: uuid.UUID
    status: TrainingStatus = TrainingStatus.PENDING
    config: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Training progress percentage")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingListResponse(BaseModel):
    """Schema for paginated training list response."""
    items: List[TrainingResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
