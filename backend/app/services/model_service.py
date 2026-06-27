"""模型管理服务（同步版本，供 Celery 任务与 sync API 使用）。"""

import os
import shutil
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.model import ModelVersion


def get_model(db: Session, model_id: str) -> Optional[ModelVersion]:
    """获取模型详情。"""
    return db.query(ModelVersion).filter(ModelVersion.id == model_id).first()


def list_models(
    db: Session,
    user_id: Optional[str] = None,
    model_version: Optional[str] = None,
    tags: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[ModelVersion], int]:
    """列出模型（可选按用户/版本/标签筛选）。"""
    from app.models.training import Training

    query = db.query(ModelVersion).join(Training, ModelVersion.training_id == Training.id)
    if user_id:
        query = query.filter(Training.user_id == user_id)
    if model_version:
        query = query.filter(ModelVersion.model_version == model_version)
    if tags:
        for tag in tags:
            query = query.filter(ModelVersion.tags.contains([tag]))
    total = query.count()
    models = (
        query.order_by(ModelVersion.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return models, total


def export_model(db: Session, model_id: str, export_config: dict) -> str:
    """提交模型导出异步任务。"""
    from app.tasks.export_tasks import export_model_task

    export_format = export_config.get("format", "onnx")
    export_model_task.delay(model_id, export_format, export_config)
    return str(uuid.uuid4())


def delete_model(db: Session, model_id: str) -> None:
    """删除模型及其文件。"""
    model = get_model(db, model_id)
    if not model:
        return
    if model.file_path and os.path.exists(model.file_path):
        safe_dir = os.path.dirname(os.path.realpath(model.file_path))
        allowed = ["/data/models", "/data/uploads", "/data/training"]
        if any(safe_dir.startswith(d) for d in allowed):
            shutil.rmtree(safe_dir, ignore_errors=True)
    db.delete(model)
    db.commit()


def add_tags(db: Session, model_id: str, tags: List[str]) -> Optional[ModelVersion]:
    """为模型添加标签。"""
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
    """获取同名模型的所有版本历史。"""
    model = get_model(db, model_id)
    if not model:
        return []
    versions = (
        db.query(ModelVersion)
        .filter(ModelVersion.name == model.name)
        .order_by(ModelVersion.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(v.id),
            "version": v.version,
            "model_version": v.model_version,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "metrics": v.metrics,
        }
        for v in versions
    ]
