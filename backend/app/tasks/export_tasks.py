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
    self, model_id: str, fmt: str, config: Optional[dict] = None
) -> dict:
    """导出模型到指定格式。

    Args:
        model_id: 模型 ID
        fmt: 导出格式 (onnx, torchscript, tflite, coreml, tensorrt, openvino)
        config: 导出配置选项 (img_size, half, dynamic, simplify 等)
    """
    from app.core.database import SessionLocal
    from app.models.model import ModelVersion

    if fmt not in EXPORT_FORMATS:
        raise ValueError(
            f"不支持的导出格式: {fmt}。支持: {list(EXPORT_FORMATS.keys())}"
        )

    config = config or {}
    db = SessionLocal()
    try:
        model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not model:
            raise ValueError(f"模型 {model_id} 不存在")

        if not model.file_path or not os.path.isfile(model.file_path):
            raise FileNotFoundError(f"模型文件不存在: {model.file_path}")

        logger.info("导出模型 %s → %s", model_id, fmt)

        export_dir = os.path.join(os.path.dirname(model.file_path), "exports")
        os.makedirs(export_dir, exist_ok=True)

        fmt_config = EXPORT_FORMATS[fmt]

        # 真实导出
        try:
            from ultralytics import YOLO

            yolo_model = YOLO(model.file_path)
            exported_path = yolo_model.export(
                format=fmt,
                dynamic=config.get("dynamic", fmt_config["dynamic"]),
                imgsz=config.get("img_size", 640),
                half=config.get("half", False),
                simplify=config.get("simplify", fmt == "onnx"),
            )
            export_path = str(exported_path)
        except ImportError:
            raise RuntimeError("ultralytics 未安装，无法导出模型")
        except Exception as e:
            raise RuntimeError(f"导出失败: {e}")

        # 更新模型记录
        exports = (model.metrics or {}).get("exports", {})
        exports[fmt] = {"path": export_path, "config": config}
        if model.metrics:
            model.metrics["exports"] = exports
        else:
            model.metrics = {"exports": exports}
        db.commit()

        logger.info("模型 %s 导出 %s 完成 → %s", model_id, fmt, export_path)
        return {
            "status": "success",
            "model_id": model_id,
            "format": fmt,
            "export_path": export_path,
        }

    except Exception as exc:
        logger.error("模型 %s 导出 %s 失败: %s", model_id, fmt, exc)
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
