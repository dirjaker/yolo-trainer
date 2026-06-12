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
    name: Optional[str] = None,
) -> CompareResult:
    """创建模型对比任务

    Args:
        db: 数据库会话
        model_ids: 模型 ID 列表
        test_dataset_id: 测试数据集 ID
        name: 对比任务名称

    Returns:
        CompareResult: 对比结果对象
    """
    compare = CompareResult(
        id=uuid.uuid4(),
        name=name or f"compare-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        status="pending",
        model_ids=model_ids,
        test_dataset_id=uuid.UUID(test_dataset_id) if isinstance(test_dataset_id, str) else test_dataset_id,
    )
    db.add(compare)
    db.commit()
    db.refresh(compare)

    # 异步执行对比任务
    from app.tasks.compare_tasks import run_compare_task

    run_compare_task.delay(str(compare.id))

    return compare


def get_compare(db: Session, compare_id: str) -> Optional[CompareResult]:
    """获取对比结果

    Args:
        db: 数据库会话
        compare_id: 对比任务 ID

    Returns:
        CompareResult or None
    """
    return db.query(CompareResult).filter(CompareResult.id == compare_id).first()


def list_compares(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[CompareResult], int]:
    """列出对比任务

    Args:
        db: 数据库会话
        page: 页码
        page_size: 每页数量

    Returns:
        (list, total): 对比任务列表和总数
    """
    query = db.query(CompareResult)
    total = query.count()
    items = (
        query.order_by(CompareResult.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def run_compare(db: Session, compare_id: str) -> None:
    """执行模型对比（同步版本，供 Celery Task 调用）

    Args:
        db: 数据库会话
        compare_id: 对比任务 ID
    """
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
    """评估单个模型

    Args:
        model: 模型对象
        test_dataset_id: 测试数据集 ID

    Returns:
        dict: 评估指标
    """
    # 如果模型已有指标，直接使用
    if model.metrics:
        return {
            "mAP50": model.metrics.get("mAP50", 0.0),
            "mAP50_95": model.metrics.get("mAP50_95", 0.0),
            "precision": model.metrics.get("precision", 0.0),
            "recall": model.metrics.get("recall", 0.0),
            "f1_score": model.metrics.get("f1_score", 0.0),
            "inference_speed_ms": model.metrics.get("inference_speed_ms"),
            "model_size_mb": round(model.file_size / (1024 * 1024), 2) if model.file_size else None,
            "params_count": model.metrics.get("params_count"),
            "flops": model.metrics.get("flops"),
            "per_class_metrics": model.metrics.get("per_class_metrics"),
        }

    # 否则在测试集上运行评估
    try:
        from ultralytics import YOLO

        if not os.path.exists(model.file_path):
            raise FileNotFoundError(f"模型文件不存在: {model.file_path}")

        yolo_model = YOLO(model.file_path)
        # TODO: 获取测试数据集路径并运行评估
        # results = yolo_model.val(data=test_dataset_path)

        # 暂时返回默认值
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

    except ImportError:
        # ultralytics 未安装，返回文件大小等基础信息
        return {
            "mAP50": None,
            "mAP50_95": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "inference_speed_ms": None,
            "model_size_mb": round(model.file_size / (1024 * 1024), 2) if model.file_size else None,
            "params_count": None,
            "flops": None,
            "per_class_metrics": None,
        }
