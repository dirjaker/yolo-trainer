"""Hyperparameter search schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class SearchMethod(str, Enum):
    """Hyperparameter search method."""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"


class SearchStatus(str, Enum):
    """Search job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrialStatus(str, Enum):
    """Individual trial status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PRUNED = "pruned"


class SearchSpaceParam(BaseModel):
    """A single hyperparameter in the search space.

    For grid/random search, provide `values` for discrete or
    `low`/`high`/`log`/`step` for continuous.
    """
    type: str = Field(
        default="float",
        description="Parameter type: float, int, categorical",
    )
    low: Optional[float] = Field(default=None, description="Lower bound (continuous)")
    high: Optional[float] = Field(default=None, description="Upper bound (continuous)")
    values: Optional[List[Any]] = Field(default=None, description="Discrete values (categorical or grid)")
    log: bool = Field(default=False, description="Sample in log scale")
    step: Optional[float] = Field(default=None, description="Step size for grid search")


class SearchConfig(BaseModel):
    """Configuration for hyperparameter search."""
    method: SearchMethod = Field(default=SearchMethod.BAYESIAN, description="Search method")
    n_trials: int = Field(default=20, ge=1, le=500, description="Number of trials to run")
    metric: str = Field(default="metrics/mAP50-95(B)", description="Metric to optimize")
    direction: str = Field(default="maximize", description="Optimization direction: maximize or minimize")
    epochs_per_trial: int = Field(default=50, ge=1, le=1000, description="Epochs per trial")
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds for entire search")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class HyperparameterSearchCreate(BaseModel):
    """Schema for creating a hyperparameter search job."""
    name: str = Field(..., min_length=1, max_length=200, description="Search job name")
    model_version: str = Field(
        default="yolov8n",
        description="YOLO model version (yolov5*, yolov8*, yolov9*, yolov10*)",
    )
    dataset_id: str = Field(..., description="Dataset ID to use for training")
    search_space: Dict[str, SearchSpaceParam] = Field(
        ...,
        description="Search space definition. Keys are param names, values define ranges.",
        examples=[{
            "learning_rate": {"type": "float", "low": 1e-5, "high": 1e-1, "log": True},
            "batch_size": {"type": "int", "values": [8, 16, 32, 64]},
            "img_size": {"type": "int", "values": [416, 640, 800]},
        }],
    )
    search_config: SearchConfig = Field(default_factory=SearchConfig, description="Search configuration")
    base_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Base training config (fixed params not in search space)",
    )


class TrialResponse(BaseModel):
    """Schema for a single trial result."""
    id: str
    search_id: str
    trial_number: int
    status: TrialStatus = TrialStatus.PENDING
    params: Optional[Dict[str, Any]] = None
    metric_value: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    error: Optional[str] = None

    class Config:
        from_attributes = True


class HyperparameterSearchResponse(BaseModel):
    """Schema for search job response."""
    id: str
    name: str
    model_version: str
    dataset_id: str
    status: SearchStatus = SearchStatus.PENDING
    method: SearchMethod = SearchMethod.BAYESIAN
    search_space: Optional[Dict[str, Any]] = None
    search_config: Optional[Dict[str, Any]] = None
    n_trials: int = 0
    completed_trials: int = 0
    best_metric: Optional[float] = None
    best_params: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HyperparameterSearchListResponse(BaseModel):
    """Schema for paginated search list response."""
    items: List[HyperparameterSearchResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
