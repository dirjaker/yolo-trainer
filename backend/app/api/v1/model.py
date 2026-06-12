"""模型管理路由。"""

import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.model import ModelVersion
from app.models.user import User
from app.schemas.model import ModelExport, ModelResponse, ModelListResponse

router = APIRouter()


@router.get("/", response_model=ModelListResponse)
async def list_models(
    model_version: Optional[str] = Query(None, description="按模型架构版本筛选 (yolov8n, yolov8s 等)"),
    tags: Optional[List[str]] = Query(None, description="按标签筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取模型列表。"""
    query = select(ModelVersion)

    if model_version:
        query = query.where(ModelVersion.model_version == model_version)
    if tags:
        # PostgreSQL JSONB 包含查询
        for tag in tags:
            query = query.where(ModelVersion.tags.contains([tag]))

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    query = query.order_by(ModelVersion.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    models = list(result.scalars().all())

    return ModelListResponse(items=models, total=total, page=page, page_size=page_size)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取模型详情。"""
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")
    return model


@router.post("/{model_id}/export")
async def export_model(
    model_id: uuid.UUID,
    export_in: ModelExport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出模型为指定格式（ONNX、TorchScript 等）。"""
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    try:
        from app.tasks.export_tasks import export_model_task

        export_config = export_in.model_dump()
        export_model_task.delay(str(model_id), export_in.format.value, export_config)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="导出服务暂不可用，请稍后重试",
        )

    return {"message": "导出任务已提交", "model_id": str(model_id), "format": export_in.format.value}


@router.post("/{model_id}/tags", response_model=ModelResponse)
async def add_tags(
    model_id: uuid.UUID,
    tags: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为模型添加标签。"""
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    existing_tags = set(model.tags or [])
    existing_tags.update(tags)
    model.tags = list(existing_tags)
    await db.flush()
    await db.refresh(model)
    return model


@router.get("/{model_id}/versions")
async def get_model_versions(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取模型的所有版本历史。"""
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 获取同名模型的所有版本
    versions_result = await db.execute(
        select(ModelVersion)
        .where(ModelVersion.name == model.name)
        .order_by(ModelVersion.created_at.desc())
    )
    versions = versions_result.scalars().all()

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


@router.get("/{model_id}/download")
async def download_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载模型文件。"""
    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    if not model.file_path or not os.path.isfile(model.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型文件不存在")

    filename = os.path.basename(model.file_path)
    return FileResponse(
        path=model.file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除模型及其文件。"""
    import shutil

    result = await db.execute(select(ModelVersion).where(ModelVersion.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 删除模型文件
    if model.file_path and os.path.exists(model.file_path):
        shutil.rmtree(os.path.dirname(model.file_path), ignore_errors=True)

    await db.delete(model)
