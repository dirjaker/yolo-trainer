"""Trainer module - factory for creating trainer instances."""

from typing import Optional

from worker.trainer.base import BaseTrainer, TrainCallback


def get_trainer(model_version: str, callback: Optional[TrainCallback] = None) -> BaseTrainer:
    """Factory function to get the appropriate trainer for a model version.

    Args:
        model_version: Model version string, e.g. "yolov8n", "yolov5s".
        callback: Optional callback for training progress updates.

    Returns:
        A BaseTrainer subclass instance.

    Raises:
        ValueError: If the model version is not supported.
    """
    version = model_version.lower().strip()

    if version.startswith("yolov8"):
        from worker.trainer.yolov8 import YOLOv8Trainer
        return YOLOv8Trainer(callback=callback)
    elif version.startswith("yolov5"):
        from worker.trainer.yolov5 import YOLOv5Trainer
        return YOLOv5Trainer(callback=callback)
    elif version.startswith("yolov9"):
        from worker.trainer.yolov9 import YOLOv9Trainer
        return YOLOv9Trainer(callback=callback)
    elif version.startswith("yolov10"):
        from worker.trainer.yolov10 import YOLOv10Trainer
        return YOLOv10Trainer(callback=callback)
    else:
        raise ValueError(
            f"Unsupported model version: {model_version}. "
            f"Supported: yolov5*, yolov8*, yolov9*, yolov10*"
        )
