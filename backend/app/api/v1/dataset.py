"""数据集管理路由。"""

import logging
import os
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import DatasetResponse, DatasetListResponse

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
UPLOAD_DIR = os.path.realpath(os.environ.get("UPLOAD_DIR", "/data/uploads/datasets"))
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_FORMATS = {"yolo", "coco", "voc"}
CHUNK_SIZE = 1024 * 1024  # 1MB


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(..., description="数据集压缩文件 (zip)"),
    name: str = Form(..., min_length=1, max_length=200, description="数据集名称"),
    description: str = Form(None, max_length=2000, description="数据集描述"),
    format: str = Form("yolo", description="数据集格式 (yolo, coco, voc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传数据集（multipart/form-data）。"""
    # 验证格式
    if format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}，允许: {ALLOWED_FORMATS}")

    # 验证文件类型
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持 .zip 格式的数据集文件")

    # 分块写入 + 大小限制
    dataset_id = uuid.uuid4()
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, f"{dataset_id}.zip")
    total_bytes = 0
    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    f.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE_MB}MB)",
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("文件上传失败: %s", e)
        raise HTTPException(status_code=500, detail="文件上传失败")

    # 验证是合法 ZIP
    import zipfile
    if not zipfile.is_zipfile(file_path):
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="文件不是合法的 ZIP 格式")

    # 创建数据集记录
    dataset = Dataset(
        id=dataset_id,
        user_id=current_user.id,
        name=name,
        description=description,
        format=format,
        file_path=file_path,
        status="uploading",
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    # 异步处理数据集
    try:
        from app.tasks.training_tasks import process_dataset_task
        process_dataset_task.delay(str(dataset.id))
    except Exception as e:
        logger.warning("Celery 任务提交失败（数据集 %s）: %s", dataset.id, e)

    return dataset


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取数据集列表。"""
    query = select(Dataset).where(Dataset.user_id == current_user.id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Dataset.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    datasets = list(result.scalars().all())

    return DatasetListResponse(items=datasets, total=total, page=page, page_size=page_size)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取数据集详情。"""
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除数据集及其文件。"""
    import shutil

    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据集不存在")

    # 删除文件（校验路径在允许目录内）
    if dataset.file_path and os.path.exists(dataset.file_path):
        real_path = os.path.realpath(dataset.file_path)
        if real_path.startswith(UPLOAD_DIR + os.sep):
            shutil.rmtree(os.path.dirname(real_path), ignore_errors=True)

    await db.delete(dataset)
