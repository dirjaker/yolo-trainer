"""模型管理服务"""

import os
import shutil
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.model import Model


def get_model(db: Session, model_id: str) -> Optional[Model]:
    """获取模型详情

    Args:
        db: 数据库会话
        model_id: 模型 ID

    Returns:
        Model or None
    """
    return db.query(Model).filter(Model.id == model_id).first()


def list_models(
    db: Session,
    model_version: Optional[str] = None,
    tags: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Model], int]:
    """列出模型

    Args:
        db: 数据库会话
        model_version: 按版本筛选
        tags: 按标签筛选
        page: 页码
        page_size: 每页数量

    Returns:
        (list, total): 模型列表和总数
    """
    query = db.query(Model)
    if model_version:
        query = query.filter(Model.version == model_version)
    if tags:
        query = query.filter(Model.tags.contains(tags))

    total = query.count()
    models = (
        query.order_by(Model.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return models, total


def export_model(db: Session, model_id: str, export_config: dict) -> str:
    """导出模型

    Args:
        db: 数据库会话
        model_id: 模型 ID
        export_config: 导出配置，包含 format 等

    Returns:
        str: 导出任务 ID
    """
    from app.tasks.export_tasks import export_model_task

    export_id = str(uuid.uuid4())
    export_format = export_config.get("format", "onnx")

    export_model_task.delay(model_id, export_format, export_config)
    return export_id


def delete_model(db: Session, model_id: str) -> None:
    """删除模型

    Args:
        db: 数据库会话
        model_id: 模型 ID
    """
    model = get_model(db, model_id)
    if not model:
        return

    # 删除模型文件
    if model.file_path and os.path.exists(model.file_path):
        shutil.rmtree(os.path.dirname(model.file_path), ignore_errors=True)

    db.delete(model)
    db.commit()


def add_tags(db: Session, model_id: str, tags: List[str]) -> Optional[Model]:
    """为模型添加标签

    Args:
        db: 数据库会话
        model_id: 模型 ID
        tags: 标签列表

    Returns:
        Model or None
    """
    model = get_model(db, model_id)
    if not model:
        return None

    existing_tags = set(model.tags or [])
    existing_tags.update(tags)
    model.tags = list(existing_tags)
    db.commit()
    db.refresh(model)
    return model


def get_model_versions(db: Session, model_id: str) -> List[dict]:
    """获取模型的所有版本

    Args:
        db: 数据库会话
        model_id: 模型 ID

    Returns:
        list: 版本列表
    """
    model = get_model(db, model_id)
    if not model:
        return []

    # 获取同名模型的所有版本
    versions = (
        db.query(Model)
        .filter(Model.name == model.name)
        .order_by(Model.created_at.desc())
        .all()
    )
    return [
        {
            "id": v.id,
            "version": v.version,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "metrics": v.metrics,
        }
        for v in versions
    ]
