"""模型对比服务"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.compare import CompareResult
from app.models.model import ModelVersion


def create_compare(
    db: Session,
    model_ids: List[str],
    test_dataset_id: str,
    user_id,
    name: Optional[str] = None,
) -> CompareResult:
    """创建模型对比任务。

    Args:
        db: 数据库会话
        model_ids: 模型 ID 列表
        test_dataset_id: 测试数据集 ID
        user_id: 用户 ID
        name: 对比任务名称
    """
    compare = CompareResult(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name or f"compare-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        status="pending",
        model_ids=model_ids,
        test_dataset_id=uuid.UUID(test_dataset_id) if isinstance(test_dataset_id, str) else test_dataset_id,
    )
    db.add(compare)
    db.commit()
    db.refresh(compare)

    # 异步执行对比
    from app.tasks.compare_tasks import run_compare_task
    run_compare_task.delay(str(compare.id))

    return compare


def get_compare(db: Session, compare_id: str) -> Optional[CompareResult]:
    """获取对比结果。"""
    return db.query(CompareResult).filter(CompareResult.id == compare_id).first()


def list_compares(
    db: Session,
    user_id,
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    """列出当前用户的对比任务。"""
    query = db.query(CompareResult).filter(CompareResult.user_id == user_id)
    total = query.count()
    items = (
        query.order_by(CompareResult.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def run_compare(db: Session, compare_id: str) -> None:
    """执行模型对比（同步版本，供 Celery Task 调用）。"""
    compare = get_compare(db, compare_id)
    if not compare:
        return

    compare.status = "running"
    db.commit()

    try:
        results = []
        for model_id in compare.model_ids:
            model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
            if not model:
                continue

            metrics = _evaluate_model(model, compare.test_dataset_id)
            metrics["model_id"] = str(model.id)
            metrics["model_name"] = model.name
            metrics["model_version"] = model.model_version
            results.append(metrics)

        compare.results = results
        compare.status = "completed"
        compare.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        compare.status = "failed"
        compare.error_message = str(e)
        db.commit()


def _evaluate_model(model: ModelVersion, test_dataset_id: uuid.UUID) -> dict:
    """评估单个模型 —— 使用真实 YOLO 验证。

    优先使用训练时保存的指标，否则在测试集上运行 val()。
    """
    # 训练指标中已有 mAP 等数据
    if model.metrics and model.metrics.get("mAP50") is not None:
        return {
            "mAP50": model.metrics.get("mAP50", 0.0),
            "mAP50_95": model.metrics.get("mAP50-95", 0.0) or model.metrics.get("mAP50_95", 0.0),
            "precision": model.metrics.get("precision", 0.0),
            "recall": model.metrics.get("recall", 0.0),
            "f1_score": model.metrics.get("f1_score", 0.0),
            "inference_speed_ms": model.metrics.get("inference_speed_ms"),
            "model_size_mb": round(model.file_size / (1024 * 1024), 2) if model.file_size else None,
            "params_count": model.metrics.get("params_count"),
            "flops": model.metrics.get("flops"),
            "per_class_metrics": model.metrics.get("per_class_metrics"),
        }

    # 否则在测试集上运行真实的 val()
    try:
        from ultralytics import YOLO

        if not os.path.isfile(model.file_path):
            return _empty_metrics(model)

        # 解析数据集路径
        from pathlib import Path
        from app.models.dataset import Dataset
        from app.core.database import SessionLocal

        test_db = SessionLocal()
        try:
            dataset = test_db.query(Dataset).filter(Dataset.id == test_dataset_id).first()
            data_yaml = None
            if dataset:
                extract_dir = Path(dataset.file_path).with_suffix("")
                yamls = list(extract_dir.glob("*.yaml")) + list(extract_dir.glob("*.yml"))
                data_yaml = str(yamls[0]) if yamls else None
        finally:
            test_db.close()

        yolo_model = YOLO(model.file_path)
        val_kwargs = {}
        if data_yaml:
            val_kwargs["data"] = data_yaml
        results = yolo_model.val(**val_kwargs)

        rd = results.results_dict if hasattr(results, "results_dict") else {}
        return {
            "mAP50": float(rd.get("metrics/mAP50(B)", 0.0)),
            "mAP50_95": float(rd.get("metrics/mAP50-95(B)", 0.0)),
            "precision": float(rd.get("metrics/precision(B)", 0.0)),
            "recall": float(rd.get("metrics/recall(B)", 0.0)),
            "f1_score": 0.0,
            "inference_speed_ms": None,
            "model_size_mb": round(model.file_size / (1024 * 1024), 2) if model.file_size else None,
            "params_count": None,
            "flops": None,
            "per_class_metrics": None,
        }
    except Exception:
        return _empty_metrics(model)


def _empty_metrics(model: ModelVersion) -> dict:
    return {
        "mAP50": 0.0,
        "mAP50_95": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "inference_speed_ms": None,
        "model_size_mb": round(model.file_size / (1024 * 1024), 2) if model.file_size else None,
        "params_count": None,
        "flops": None,
        "per_class_metrics": None,
    }
