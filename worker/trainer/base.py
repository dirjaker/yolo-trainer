"""Base trainer abstract class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TrainConfig:
    """Training configuration."""
    model_version: str = "yolov8n"
    dataset_config: str = ""
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.01
    device: str = "0"  # GPU id or "cpu"
    workers: int = 8
    resume: bool = False
    pretrained_weights: Optional[str] = None
    output_dir: str = "runs/train"
    project_name: str = "exp"
    patience: int = 50
    augment: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainResult:
    """Training result."""
    success: bool
    model_path: str
    best_map50: float = 0.0
    best_map50_95: float = 0.0
    total_epochs: int = 0
    train_time: float = 0.0  # seconds
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ValidateResult:
    """Validation result."""
    success: bool
    map50: float = 0.0
    map50_95: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    per_class: Dict[str, Dict[str, float]] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ExportResult:
    """Export result."""
    success: bool
    output_path: str = ""
    format: str = ""
    error: Optional[str] = None


class TrainCallback:
    """Callback interface for training progress updates."""

    def on_epoch_end(self, epoch: int, metrics: Dict[str, Any]) -> None:
        """Called at the end of each epoch."""
        pass

    def on_train_end(self, result: TrainResult) -> None:
        """Called when training completes."""
        pass

    def on_train_start(self, config: TrainConfig) -> None:
        """Called when training starts."""
        pass


class BaseTrainer(ABC):
    """Abstract base class for all YOLO trainers."""

    def __init__(self, callback: Optional[TrainCallback] = None):
        self.callback = callback

    @abstractmethod
    def train(self, config: TrainConfig) -> TrainResult:
        """Run training with the given configuration."""
        ...

    @abstractmethod
    def validate(self, model_path: str, dataset_config: Optional[str] = None) -> ValidateResult:
        """Validate a trained model."""
        ...

    @abstractmethod
    def export(self, model_path: str, export_format: str = "onnx") -> ExportResult:
        """Export model to the specified format."""
        ...
