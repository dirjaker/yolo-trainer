"""Model exporter - export YOLO models to various deployment formats."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ExportResult:
    """Export operation result."""
    success: bool
    output_path: str = ""
    format: str = ""
    model_size_mb: float = 0.0
    error: Optional[str] = None


# Supported export formats
SUPPORTED_FORMATS = {
    "onnx": "ONNX",
    "torchscript": "TorchScript",
    "tflite": "TFLite",
    "coreml": "CoreML",
    "engine": "TensorRT",
    "openvino": "OpenVINO",
    "paddle": "PaddlePaddle",
    "ncnn": "NCNN",
}


class ModelExporter:
    """Export a trained YOLO model to deployment formats.

    Uses the ultralytics export pipeline which supports a wide range of
    formats out of the box.
    """

    def export(
        self,
        model_path: str,
        export_format: str = "onnx",
        config: Optional[Dict[str, Any]] = None,
    ) -> ExportResult:
        """Export a model.

        Args:
            model_path: Path to the trained .pt model.
            export_format: Target format (onnx, torchscript, tflite, coreml, engine, etc.).
            config: Additional export options:
                - imgsz (int): Input image size, default 640.
                - half (bool): FP16 half-precision, default False.
                - dynamic (bool): Dynamic ONNX axes, default False.
                - simplify (bool): Simplify ONNX model, default True.
                - opset (int): ONNX opset version, default 17.
                - batch (int): Batch size, default 1.

        Returns:
            ExportResult with output path and metadata.
        """
        cfg = config or {}

        fmt = export_format.lower().strip()
        if fmt not in SUPPORTED_FORMATS:
            return ExportResult(
                success=False,
                format=fmt,
                error=(
                    f"Unsupported format '{fmt}'. "
                    f"Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
                ),
            )

        try:
            from ultralytics import YOLO

            model = YOLO(model_path)

            export_kwargs: Dict[str, Any] = {
                "format": fmt,
                "imgsz": cfg.get("imgsz", 640),
                "half": cfg.get("half", False),
                "dynamic": cfg.get("dynamic", False),
                "simplify": cfg.get("simplify", True),
                "batch": cfg.get("batch", 1),
            }

            if fmt == "onnx" and "opset" in cfg:
                export_kwargs["opset"] = cfg["opset"]

            output_path = model.export(**export_kwargs)

            # Get file size
            out_file = Path(output_path)
            size_mb = out_file.stat().st_size / (1024 * 1024) if out_file.exists() else 0.0

            return ExportResult(
                success=True,
                output_path=str(output_path),
                format=fmt,
                model_size_mb=round(size_mb, 2),
            )

        except Exception as e:
            return ExportResult(success=False, format=fmt, error=str(e))

    @staticmethod
    def list_formats() -> Dict[str, str]:
        """Return all supported export formats."""
        return dict(SUPPORTED_FORMATS)
