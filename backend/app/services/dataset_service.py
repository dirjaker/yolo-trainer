"""数据集管理服务"""

import os
import shutil
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.tasks.training_tasks import process_dataset_task


def create_dataset(
    db: Session, user_id: str, dataset_data: dict, file_path: str
) -> Dataset:
    """创建数据集

    Args:
        db: 数据库会话
        user_id: 用户 ID
        dataset_data: 数据集元数据
        file_path: 上传文件路径

    Returns:
        Dataset: 创建的数据集对象
    """
    dataset = Dataset(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=dataset_data["name"],
        description=dataset_data.get("description"),
        format=dataset_data.get("format", "yolo"),
        classes=dataset_data.get("classes"),
        stats=None,
        file_path=file_path,
        status="pending",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # 异步处理数据集（解压、验证、统计）
    process_dataset_task.delay(dataset.id)

    return dataset


def get_dataset(db: Session, dataset_id: str) -> Optional[Dataset]:
    """获取数据集详情

    Args:
        db: 数据库会话
        dataset_id: 数据集 ID

    Returns:
        Dataset or None
    """
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def list_datasets(
    db: Session, user_id: str, page: int = 1, page_size: int = 20
) -> Tuple[List[Dataset], int]:
    """列出数据集

    Args:
        db: 数据库会话
        user_id: 用户 ID
        page: 页码
        page_size: 每页数量

    Returns:
        (list, total): 数据集列表和总数
    """
    query = db.query(Dataset).filter(Dataset.user_id == user_id)
    total = query.count()
    datasets = (
        query.order_by(Dataset.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return datasets, total


def delete_dataset(db: Session, dataset_id: str) -> None:
    """删除数据集

    Args:
        db: 数据库会话
        dataset_id: 数据集 ID
    """
    dataset = get_dataset(db, dataset_id)
    if not dataset:
        return

    # 删除数据集文件
    if dataset.file_path and os.path.exists(dataset.file_path):
        shutil.rmtree(os.path.dirname(dataset.file_path), ignore_errors=True)

    db.delete(dataset)
    db.commit()


def process_dataset(dataset_id: str) -> None:
    """异步处理数据集（解压、验证、统计）

    此函数由 Celery 任务调用。

    Args:
        dataset_id: 数据集 ID
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        dataset = get_dataset(db, dataset_id)
        if not dataset:
            return

        dataset.status = "processing"
        db.commit()

        # TODO: 实现数据集解压、验证和统计逻辑
        # 1. 解压上传的 zip 文件
        # 2. 验证数据集格式（YOLO VOC COCO 等）
        # 3. 统计类别分布、图片数量等

        stats = {
            "total_images": 0,
            "total_labels": 0,
            "class_distribution": {},
        }
        dataset.stats = stats
        dataset.status = "ready"
        db.commit()

    except Exception as e:
        dataset.status = "failed"
        db.commit()
        raise
    finally:
        db.close()
