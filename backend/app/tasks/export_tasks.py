"""模型导出 Celery 任务"""

import logging
import os
from typing import Optional

from celery import shared_task

logger = logging.getLogger(__name__)


EXPORT_FORMATS = {
    "onnx": {"ext": ".onnx", "dynamic": True},
    "torchscript": {"ext": ".torchscript", "dynamic": False},
    "tflite": {"ext": ".tflite", "dynamic": False},
    "coreml": {"ext": ".mlpackage", "dynamic": False},
    "tensorrt": {"ext": ".engine", "dynamic": False},
    "openvino": {"ext": "_openvino_model", "dynamic": False},
}


@shared_task(bind=True, name="tasks.export_model", max_retries=2)
def export_model_task(
    self, model_id: str, format: str, config: Optional[dict] = None
) -> dict:
    """导出模型到指定格式

    Args:
        model_id: 模型 ID
        format: 导出格式 (onnx, torchscript, tflite, coreml, tensorrt, openvino)
        config: 导出配置选项

    Returns:
        dict: 导出结果，包含导出文件路径
    """
    from app.core.database import SessionLocal
    from app.models.model import Model
    from app.services.model_service import get_model

    if format not in EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported export format: {format}. "
            f"Supported: {list(EXPORT_FORMATS.keys())}"
        )

    config = config or {}
    db = SessionLocal()

    try:
        model = get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        if not model.file_path or not os.path.exists(model.file_path):
            raise FileNotFoundError(f"Model weights not found at {model.file_path}")

        logger.info(f"Exporting model {model_id} to {format}")

        export_dir = os.path.join(os.path.dirname(model.file_path), "exports")
        os.makedirs(export_dir, exist_ok=True)

        format_config = EXPORT_FORMATS[format]

        # TODO: 集成实际的模型导出逻辑
        # from ultralytics import YOLO
        # yolo_model = YOLO(model.file_path)
        # exported_path = yolo_model.export(
        #     format=format,
        #     dynamic=config.get("dynamic", format_config["dynamic"]),
        #     imgsz=config.get("img_size", 640),
        #     half=config.get("half", False),
        #     simplify=True if format == "onnx" else False,
        # )

        # 模拟导出路径
        export_path = os.path.join(
            export_dir, f"{model_id}{format_config['ext']}"
        )

        # 更新模型记录
        exports = model.metrics.get("exports", {}) if model.metrics else {}
        exports[format] = {
            "path": export_path,
            "config": config,
        }
        if model.metrics:
            model.metrics["exports"] = exports
        else:
            model.metrics = {"exports": exports}
        db.commit()

        logger.info(f"Model {model_id} exported to {format}: {export_path}")
        return {
            "status": "success",
            "model_id": model_id,
            "format": format,
            "export_path": export_path,
        }

    except Exception as exc:
        logger.error(f"Model {model_id} export to {format} failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
