"""训练任务路由。"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.training import Training
from app.models.user import User
from app.schemas.training import TrainingCreate, TrainingResponse, TrainingListResponse

router = APIRouter()


@router.post("/", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_training(
    training_in: TrainingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建训练任务。"""
    config_dict = training_in.config.model_dump() if training_in.config else {}

    training = Training(
        name=training_in.name,
        model_version=training_in.model_version,
        dataset_id=training_in.dataset_id,
        user_id=current_user.id,
        status="pending",
        config=config_dict,
    )
    db.add(training)
    await db.flush()
    await db.refresh(training)

    # 异步提交训练任务到 Celery
    try:
        from app.tasks.training_tasks import train_model_task

        train_config = {
            "model_version": training.model_version,
            "dataset_id": str(training.dataset_id),
            **config_dict,
        }
        train_model_task.delay(str(training.id), train_config)
    except Exception:
        # Celery 不可用时不阻塞创建
        pass

    return training


@router.get("/", response_model=TrainingListResponse)
async def list_trainings(
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    model_version: Optional[str] = Query(None, description="按模型版本筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取训练任务列表。"""
    query = select(Training).where(Training.user_id == current_user.id)

    if status_filter:
        query = query.where(Training.status == status_filter)
    if model_version:
        query = query.where(Training.model_version == model_version)

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询
    query = query.order_by(Training.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    trainings = list(result.scalars().all())

    return TrainingListResponse(items=trainings, total=total, page=page, page_size=page_size)


@router.get("/{training_id}", response_model=TrainingResponse)
async def get_training(
    training_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取训练任务详情。"""
    result = await db.execute(
        select(Training).where(Training.id == training_id, Training.user_id == current_user.id)
    )
    training = result.scalar_one_or_none()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在")
    return training


@router.post("/{training_id}/stop", response_model=TrainingResponse)
async def stop_training(
    training_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """停止训练任务。"""
    result = await db.execute(
        select(Training).where(Training.id == training_id, Training.user_id == current_user.id)
    )
    training = result.scalar_one_or_none()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在")

    if training.status not in ("pending", "queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法停止状态为 {training.status} 的训练任务",
        )

    training.status = "cancelled"
    await db.flush()
    await db.refresh(training)
    return training


@router.get("/{training_id}/logs")
async def get_training_logs(
    training_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取训练日志。"""
    result = await db.execute(
        select(Training).where(Training.id == training_id, Training.user_id == current_user.id)
    )
    training = result.scalar_one_or_none()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在")

    # TODO: 从日志文件或 Redis 中读取实时日志
    # 目前返回占位响应
    return {"training_id": str(training.id), "logs": []}


@router.get("/{training_id}/metrics")
async def get_training_metrics(
    training_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取训练指标（用于前端绘图）。"""
    result = await db.execute(
        select(Training).where(Training.id == training_id, Training.user_id == current_user.id)
    )
    training = result.scalar_one_or_none()
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在")

    return {
        "training_id": str(training.id),
        "status": training.status,
        "progress": training.progress,
        "metrics": training.metrics or {},
    }
