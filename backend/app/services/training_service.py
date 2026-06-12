"""训练任务服务"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.training import Training
from app.tasks.training_tasks import train_model_task


def create_training(db: Session, user_id: str, training_data: dict) -> Training:
    """创建训练任务

    Args:
        db: 数据库会话
        user_id: 用户 ID
        training_data: 训练配置数据

    Returns:
        Training: 创建的训练任务对象
    """
    training = Training(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=training_data["name"],
        model_version=training_data["model_version"],
        dataset_id=training_data["dataset_id"],
        status="pending",
        config=training_data.get("config", {}),
        metrics=None,
    )
    db.add(training)
    db.commit()
    db.refresh(training)

    # 异步提交训练任务
    config = {
        "model_version": training.model_version,
        "dataset_id": training.dataset_id,
        **training.config,
    }
    train_model_task.delay(training.id, config)

    return training


def get_training(db: Session, training_id: str) -> Optional[Training]:
    """获取训练任务详情

    Args:
        db: 数据库会话
        training_id: 训练任务 ID

    Returns:
        Training or None
    """
    return db.query(Training).filter(Training.id == training_id).first()


def list_trainings(
    db: Session,
    user_id: str,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Training], int]:
    """列出训练任务

    Args:
        db: 数据库会话
        user_id: 用户 ID
        status: 按状态筛选
        page: 页码
        page_size: 每页数量

    Returns:
        (list, total): 训练任务列表和总数
    """
    query = db.query(Training).filter(Training.user_id == user_id)
    if status:
        query = query.filter(Training.status == status)

    total = query.count()
    trainings = (
        query.order_by(Training.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return trainings, total


def stop_training(db: Session, training_id: str) -> Optional[Training]:
    """停止训练任务

    Args:
        db: 数据库会话
        training_id: 训练任务 ID

    Returns:
        Training or None
    """
    training = get_training(db, training_id)
    if not training:
        return None
    if training.status not in ("pending", "running"):
        return training

    training.status = "stopped"
    db.commit()
    db.refresh(training)
    return training


def update_training_status(
    db: Session,
    training_id: str,
    status: str,
    metrics: Optional[dict] = None,
    model_id: Optional[str] = None,
) -> Optional[Training]:
    """更新训练任务状态

    Args:
        db: 数据库会话
        training_id: 训练任务 ID
        status: 新状态
        metrics: 训练指标
        model_id: 关联的模型 ID

    Returns:
        Training or None
    """
    training = get_training(db, training_id)
    if not training:
        return None

    training.status = status
    if metrics is not None:
        training.metrics = metrics
    if model_id is not None:
        training.model_id = model_id
    db.commit()
    db.refresh(training)
    return training
