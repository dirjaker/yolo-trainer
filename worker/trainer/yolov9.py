"""YOLOv9 trainer using the ultralytics library."""

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


class YOLOv9Trainer(BaseTrainer):
    """YOLOv9 trainer powered by the ultralytics package.

    Supports:
    - Standard training from pretrained weights
    - Resume training from checkpoints
    - Progress callbacks to update task status
    - Validation and multi-format export
    """

    _MODEL_MAP: Dict[str, str] = {
        "yolov9t": "yolov9t.pt",
        "yolov9s": "yolov9s.pt",
        "yolov9m": "yolov9m.pt",
        "yolov9c": "yolov9c.pt",
        "yolov9e": "yolov9e.pt",
    }

    # 允许用户传入的额外训练参数（白名单）
    _SAFE_EXTRA_KEYS = {
        "mosaic", "mixup", "copy_paste", "erasing", "hsv_h", "hsv_s", "hsv_v",
        "degrees", "translate", "scale", "shear", "perspective", "flipud", "fliplr",
        "bgr", "auto_augment", "cos_lr", "close_mosaic", "label_smoothing",
        "nbs", "overlap_mask", "mask_ratio", "dropout", "val", "save", "save_json",
        "save_hybrid", "conf", "iou", "max_det", "half", "dnn", "plots",
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
        """Run YOLOv9 training."""
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

            # Merge extra args（仅允许白名单内的参数）
            if config.extra:
                safe_extra = {k: v for k, v in config.extra.items() if k in self._SAFE_EXTRA_KEYS}
                dropped = set(config.extra.keys()) - self._SAFE_EXTRA_KEYS
                if dropped:
                    import logging; logging.getLogger(__name__).warning("过滤掉不安全的训练参数: %s", dropped)
                train_args.update(safe_extra)

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
        """Validate a trained YOLOv9 model."""
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
        """Export a YOLOv9 model to the requested format."""
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
