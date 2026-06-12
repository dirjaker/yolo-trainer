"""Test / inference schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Bounding box coordinates."""
    x1: float = Field(..., description="Left coordinate")
    y1: float = Field(..., description="Top coordinate")
    x2: float = Field(..., description="Right coordinate")
    y2: float = Field(..., description="Bottom coordinate")


class Detection(BaseModel):
    """Single object detection result."""
    class_name: str = Field(..., description="Detected class name")
    class_id: int = Field(..., ge=0, description="Detected class ID")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: BBox = Field(..., description="Bounding box coordinates")


class TestResult(BaseModel):
    """Schema for test/inference result."""
    test_id: str = Field(..., description="Unique test run identifier")
    model_id: str = Field(..., description="Model ID used for inference")
    detections: List[Detection] = Field(default_factory=list, description="List of detections")
    inference_time_ms: float = Field(..., ge=0, description="Inference time in milliseconds")
