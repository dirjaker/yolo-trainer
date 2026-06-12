"""YOLOv10 trainer using the ultralytics library."""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from ultralytics import YOLO

from worker.trainer.base import (
    BaseTrainer,
    TrainCallback,
    TrainConfig,
    TrainResult,
    ValidateResult,
    ExportResult,
)


class YOLOv10Trainer(BaseTrainer):
    """YOLOv10 trainer powered by the ultralytics package.

    Supports:
    - Standard training from pretrained weights
    - Resume training from checkpoints
    - Progress callbacks to update task status
    - Validation and multi-format export

    Note: YOLOv10 uses a different architecture with TAL (Task-Aligned Assigner)
    and may require specific ultralytics version (>= 8.2).
    """

    _MODEL_MAP: Dict[str, str] = {
        "yolov10n": "yolov10n.pt",
        "yolov10s": "yolov10s.pt",
        "yolov10m": "yolov10m.pt",
        "yolov10b": "yolov10b.pt",
        "yolov10l": "yolov10l.pt",
        "yolov10x": "yolov10x.pt",
    }

    def __init__(self, callback: Optional[TrainCallback] = None):
        super().__init__(callback)

    def _resolve_model(self, config: TrainConfig) -> str:
        """Resolve the model identifier to a weight file path."""
        if config.pretrained_weights and Path(config.pretrained_weights).exists():
            return config.pretrained_weights
        return self._MODEL_MAP.get(config.model_version.lower(), f"{config.model_version}.pt")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(self, config: TrainConfig) -> TrainResult:
        """Run YOLOv10 training."""
        try:
            model_source = self._resolve_model(config)
            model = YOLO(model_source)

            if self.callback:
                self.callback.on_train_start(config)

            start_time = time.time()

            # Determine resume checkpoint path
            resume_path = None
            if config.resume:
                last_ckpt = Path(config.output_dir) / config.project_name / "weights" / "last.pt"
                if last_ckpt.exists():
                    resume_path = str(last_ckpt)

            train_args: Dict[str, Any] = {
                "data": config.dataset_config,
                "epochs": config.epochs,
                "batch": config.batch_size,
                "imgsz": config.img_size,
                "lr0": config.learning_rate,
                "device": config.device,
                "workers": config.workers,
                "project": config.output_dir,
                "name": config.project_name,
                "patience": config.patience,
                "exist_ok": True,
                "verbose": True,
            }

            if resume_path:
                train_args["resume"] = resume_path
                train_args.pop("data", None)

            train_args.update(config.extra)

            # Bridge ultralytics events to our TrainCallback
            if self.callback:
                def _on_fit_epoch_end(trainer):
                    epoch = trainer.epoch
                    metrics = {}
                    if hasattr(trainer, "metrics") and trainer.metrics:
                        metrics = {k: float(v) for k, v in trainer.metrics.results_dict.items()}
                    self.callback.on_epoch_end(epoch, metrics)

                model.add_callback("on_fit_epoch_end", _on_fit_epoch_end)

            results = model.train(**train_args)

            train_time = time.time() - start_time

            best_map50 = 0.0
            best_map50_95 = 0.0
            metrics: Dict[str, Any] = {}
            if hasattr(results, "results_dict"):
                rd = results.results_dict
                best_map50 = float(rd.get("metrics/mAP50(B)", 0.0))
                best_map50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
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
        """Validate a trained YOLOv10 model."""
        try:
            model = YOLO(model_path)
            results = model.val(data=dataset_config)

            rd = results.results_dict if hasattr(results, "results_dict") else {}
            per_class: Dict[str, Dict[str, float]] = {}

            if hasattr(results, "class_result") and results.class_result:
                names = results.names if hasattr(results, "names") else {}
                for idx, cls_metrics in enumerate(results.class_result):
                    cls_name = names.get(idx, str(idx))
                    per_class[cls_name] = {
                        "precision": float(cls_metrics[0]),
                        "recall": float(cls_metrics[1]),
                        "map50": float(cls_metrics[2]),
                        "map50-95": float(cls_metrics[3]),
                    }

            return ValidateResult(
                success=True,
                map50=float(rd.get("metrics/mAP50(B)", 0.0)),
                map50_95=float(rd.get("metrics/mAP50-95(B)", 0.0)),
                precision=float(rd.get("metrics/precision(B)", 0.0)),
                recall=float(rd.get("metrics/recall(B)", 0.0)),
                f1=0.0,
                per_class=per_class,
            )
        except Exception as e:
            return ValidateResult(success=False, error=str(e))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export(self, model_path: str, export_format: str = "onnx") -> ExportResult:
        """Export a YOLOv10 model to the requested format."""
        try:
            model = YOLO(model_path)
            output_path = model.export(format=export_format)
            return ExportResult(
                success=True,
                output_path=str(output_path),
                format=export_format,
            )
        except Exception as e:
            return ExportResult(success=False, format=export_format, error=str(e))
