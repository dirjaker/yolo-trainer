"""Model schemas."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Model export formats."""
    ONNX = "onnx"
    TORCHSCRIPT = "torchscript"
    TFLITE = "tflite"
    PADDLE = "paddle"
    COREML = "coreml"


class ModelResponse(BaseModel):
    """Schema for model response."""
    id: uuid.UUID
    training_id: uuid.UUID
    name: str
    version: str
    model_version: str
    description: Optional[str] = None
    # file_path 不暴露给客户端
    file_size: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Schema for paginated model list response."""
    items: List[ModelResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class ModelExport(BaseModel):
    """Schema for model export request."""
    format: ExportFormat = Field(..., description="Export format")
    img_size: int = Field(default=640, ge=32, le=4096, description="Image size for export")
    simplify: bool = Field(default=True, description="Simplify model (for ONNX)")
    dynamic: bool = Field(default=False, description="Dynamic input shapes (for ONNX)")
