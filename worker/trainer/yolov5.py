"""YOLOv5 trainer using the yolov5 package / repo."""

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from worker.trainer.base import (
    BaseTrainer,
    TrainCallback,
    TrainConfig,
    TrainResult,
    ValidateResult,
    ExportResult,
)


class YOLOv5Trainer(BaseTrainer):
    """YOLOv5 trainer.

    Uses the official yolov5 repository via the ``torch.hub`` or
    ``yolov5`` pip package interface.

    Supports:
    - Standard and fine-tuning training
    - Resume training from last.pt checkpoints
    - Validation with mAP metrics
    - Export to ONNX and other formats
    """

    _MODEL_MAP: Dict[str, str] = {
        "yolov5n": "yolov5n.pt",
        "yolov5s": "yolov5s.pt",
        "yolov5m": "yolov5m.pt",
        "yolov5l": "yolov5l.pt",
        "yolov5x": "yolov5x.pt",
    }

    def __init__(self, callback: Optional[TrainCallback] = None):
        super().__init__(callback)

    def _resolve_model(self, config: TrainConfig) -> str:
        if config.pretrained_weights and Path(config.pretrained_weights).exists():
            return config.pretrained_weights
        return self._MODEL_MAP.get(config.model_version.lower(), f"{config.model_version}.pt")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(self, config: TrainConfig) -> TrainResult:
        """Run YOLOv5 training using torch.hub."""
        try:
            import torch

            if self.callback:
                self.callback.on_train_start(config)

            model_source = self._resolve_model(config)
            start_time = time.time()

            # Load model via torch hub (ultralytics/yolov5 repo)
            model = torch.hub.load(
                "ultralytics/yolov5",
                "custom",
                path=model_source,
                force_reload=False,
                autoshape=False,
            )

            resume_path = ""
            if config.resume:
                last_ckpt = Path(config.output_dir) / config.project_name / "weights" / "last.pt"
                if last_ckpt.exists():
                    resume_path = str(last_ckpt)

            # Build training arguments
            train_args: Dict[str, Any] = {
                "data": config.dataset_config,
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "imgsz": config.img_size,
                "lr0": config.learning_rate,
                "device": config.device,
                "workers": config.workers,
                "project": config.output_dir,
                "name": config.project_name,
                "patience": config.patience,
                "exist_ok": True,
            }

            if resume_path:
                train_args["resume"] = resume_path

            train_args.update(config.extra)

            # Run training
            results = model.train(**train_args)

            train_time = time.time() - start_time

            # Parse results
            best_map50 = 0.0
            best_map50_95 = 0.0
            metrics: Dict[str, Any] = {}

            if hasattr(results, "results_dict"):
                rd = results.results_dict
                best_map50 = float(rd.get("metrics/mAP_0.5", 0.0))
                best_map50_95 = float(rd.get("metrics/mAP_0.5:0.95", 0.0))
                metrics = {k: float(v) for k, v in rd.items()}

            best_weights = Path(config.output_dir) / config.project_name / "weights" / "best.pt"

            result = TrainResult(
                success=True,
                model_path=str(best_weights),
                best_map50=best_map50,
                best_map50_95=best_map50_95,
                total_epochs=config.epochs,
                train_time=train_time,
                metrics=metrics,
            )

            if self.callback:
                self.callback.on_train_end(result)

            return result

        except Exception as e:
            return TrainResult(success=False, model_path="", error=str(e))

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self, model_path: str, dataset_config: Optional[str] = None) -> ValidateResult:
        """Validate a trained YOLOv5 model."""
        try:
            import torch

            model = torch.hub.load(
                "ultralytics/yolov5",
                "custom",
                path=model_path,
                force_reload=False,
            )

            val_args: Dict[str, Any] = {}
            if dataset_config:
                val_args["data"] = dataset_config

            results = model.val(**val_args)

            rd = results.results_dict if hasattr(results, "results_dict") else {}

            return ValidateResult(
                success=True,
                map50=float(rd.get("metrics/mAP_0.5", 0.0)),
                map50_95=float(rd.get("metrics/mAP_0.5:0.95", 0.0)),
                precision=float(rd.get("metrics/precision", 0.0)),
                recall=float(rd.get("metrics/recall", 0.0)),
                f1=0.0,
            )
        except Exception as e:
            return ValidateResult(success=False, error=str(e))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export(self, model_path: str, export_format: str = "onnx") -> ExportResult:
        """Export a YOLOv5 model to the requested format."""
        try:
            import torch

            model = torch.hub.load(
                "ultralytics/yolov5",
                "custom",
                path=model_path,
                force_reload=False,
            )

            output_path = model.export(format=export_format)
            return ExportResult(
                success=True,
                output_path=str(output_path),
                format=export_format,
            )
        except Exception as e:
            return ExportResult(success=False, format=export_format, error=str(e))
