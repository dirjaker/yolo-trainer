"""Model evaluator - computes mAP, Precision, Recall, F1 on a dataset."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class EvalResult:
    """Evaluation result container."""
    success: bool
    map50: float = 0.0
    map50_95: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    per_class: Dict[str, Dict[str, float]] = field(default_factory=dict)
    confusion_matrix: Optional[List[List[int]]] = None
    error: Optional[str] = None


class ModelEvaluator:
    """Evaluate a YOLO model on a given dataset.

    Works with both YOLOv5 and YOLOv8 models via the ultralytics interface.
    """

    def evaluate(
        self,
        model_path: str,
        dataset_config: Optional[str] = None,
        img_size: int = 640,
        batch_size: int = 16,
        device: str = "0",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.6,
    ) -> EvalResult:
        """Run full evaluation on a model.

        Args:
            model_path: Path to .pt, .onnx, or other model file.
            dataset_config: Path to dataset YAML (required for ground truth).
            img_size: Inference image size.
            batch_size: Batch size for evaluation.
            device: GPU id or 'cpu'.
            conf_threshold: Confidence threshold.
            iou_threshold: IoU threshold for NMS.

        Returns:
            EvalResult with mAP, precision, recall, F1, and per-class metrics.
        """
        try:
            from ultralytics import YOLO

            model = YOLO(model_path)

            results = model.val(
                data=dataset_config,
                imgsz=img_size,
                batch=batch_size,
                device=device,
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=True,
            )

            rd = results.results_dict if hasattr(results, "results_dict") else {}

            map50 = float(rd.get("metrics/mAP50(B)", rd.get("metrics/mAP_0.5", 0.0)))
            map50_95 = float(rd.get("metrics/mAP50-95(B)", rd.get("metrics/mAP_0.5:0.95", 0.0)))
            precision = float(rd.get("metrics/precision(B)", rd.get("metrics/precision", 0.0)))
            recall = float(rd.get("metrics/recall(B)", rd.get("metrics/recall", 0.0)))
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            # Per-class metrics
            per_class: Dict[str, Dict[str, float]] = {}
            if hasattr(results, "class_result") and results.class_result:
                names = results.names if hasattr(results, "names") else {}
                for idx, cls_metrics in enumerate(results.class_result):
                    cls_name = names.get(idx, str(idx))
                    p = float(cls_metrics[0])
                    r = float(cls_metrics[1])
                    per_class[cls_name] = {
                        "precision": p,
                        "recall": r,
                        "map50": float(cls_metrics[2]),
                        "map50-95": float(cls_metrics[3]),
                        "f1": 2 * p * r / (p + r) if (p + r) > 0 else 0.0,
                    }

            return EvalResult(
                success=True,
                map50=map50,
                map50_95=map50_95,
                precision=precision,
                recall=recall,
                f1=f1,
                per_class=per_class,
            )

        except Exception as e:
            return EvalResult(success=False, error=str(e))
