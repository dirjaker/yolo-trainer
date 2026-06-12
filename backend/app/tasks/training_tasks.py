"""训练相关 Celery 任务"""

import logging
from typing import Optional

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="tasks.train_model", max_retries=3)
def train_model_task(self, training_id: str, config: dict) -> dict:
    """执行模型训练

    Args:
        training_id: 训练任务 ID
        config: 训练配置，包含 model_version, dataset_id, epochs, batch_size 等

    Returns:
        dict: 训练结果
    """
    from app.core.database import SessionLocal
    from app.services.training_service import update_training_status

    db = SessionLocal()
    try:
        update_training_status(db, training_id, "running")
        logger.info(f"Training {training_id} started with config: {config}")

        # 调用 YOLO 训练引擎
        model_version = config.get("model_version", "yolov8n")
        dataset_id = config.get("dataset_id")
        epochs = config.get("epochs", 100)
        batch_size = config.get("batch_size", 16)
        img_size = config.get("img_size", 640)

        # TODO: 集成实际的 YOLO 训练逻辑
        # from ultralytics import YOLO
        # model = YOLO(f"{model_version}.pt")
        # results = model.train(
        #     data=dataset_config_path,
        #     epochs=epochs,
        #     batch=batch_size,
        #     imgsz=img_size,
        # )

        # 模拟训练结果
        metrics = {
            "mAP50": 0.85,
            "mAP50-95": 0.65,
            "precision": 0.82,
            "recall": 0.78,
            "epochs_completed": epochs,
        }

        # 保存模型并更新状态
        model_id = _save_training_results(db, training_id, config, metrics)
        update_training_status(db, training_id, "completed", metrics, model_id)

        logger.info(f"Training {training_id} completed successfully")
        return {"status": "success", "model_id": model_id, "metrics": metrics}

    except Exception as exc:
        logger.error(f"Training {training_id} failed: {exc}")
        update_training_status(db, training_id, "failed")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@shared_task(bind=True, name="tasks.evaluate_model", max_retries=2)
def evaluate_model_task(self, model_id: str, dataset_id: str) -> dict:
    """评估模型

    Args:
        model_id: 模型 ID
        dataset_id: 评估数据集 ID

    Returns:
        dict: 评估结果
    """
    from app.core.database import SessionLocal
    from app.models.model import Model as ModelDB
    from app.services.model_service import get_model

    db = SessionLocal()
    try:
        model = get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        logger.info(f"Evaluating model {model_id} on dataset {dataset_id}")

        # TODO: 集成实际的 YOLO 评估逻辑
        # from ultralytics import YOLO
        # yolo_model = YOLO(model.file_path)
        # results = yolo_model.val(data=dataset_config_path)

        # 模拟评估结果
        eval_metrics = {
            "mAP50": 0.87,
            "mAP50-95": 0.68,
            "precision": 0.84,
            "recall": 0.80,
            "inference_time_ms": 12.5,
            "fps": 80,
        }

        # 更新模型指标
        model.metrics = {**(model.metrics or {}), "evaluation": eval_metrics}
        db.commit()

        logger.info(f"Model {model_id} evaluation completed")
        return {"status": "success", "metrics": eval_metrics}

    except Exception as exc:
        logger.error(f"Model {model_id} evaluation failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


def _save_training_results(
    db, training_id: str, config: dict, metrics: dict
) -> str:
    """保存训练结果，创建模型记录

    Args:
        db: 数据库会话
        training_id: 训练任务 ID
        config: 训练配置
        metrics: 训练指标

    Returns:
        str: 模型 ID
    """
    import uuid

    from app.models.model import Model

    model_id = str(uuid.uuid4())
    model_version = config.get("model_version", "yolov8n")

    # TODO: 将实际的模型文件路径设为正确位置
    file_path = f"/models/{model_id}/weights/best.pt"

    model = Model(
        id=model_id,
        training_id=training_id,
        version=model_version,
        name=f"{model_version}_{training_id[:8]}",
        description=f"Trained from {model_version} on dataset {config.get('dataset_id')}",
        file_path=file_path,
        metrics=metrics,
        tags=[model_version],
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    return model_id


@shared_task(bind=True, name="tasks.process_dataset")
def process_dataset_task(self, dataset_id: str) -> None:
    """处理数据集（解压、验证、统计）

    Args:
        dataset_id: 数据集 ID
    """
    from app.services.dataset_service import process_dataset

    try:
        process_dataset(dataset_id)
    except Exception as exc:
        logger.error(f"Dataset {dataset_id} processing failed: {exc}")
        raise
