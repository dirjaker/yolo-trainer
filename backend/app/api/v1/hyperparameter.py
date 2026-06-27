"""Hyperparameter search API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.hyperparameter import HyperparameterSearch, HyperparameterTrial
from app.models.user import User
from app.schemas.hyperparameter import (
    HyperparameterSearchCreate,
    HyperparameterSearchResponse,
    HyperparameterSearchListResponse,
    TrialResponse,
)

router = APIRouter()


@router.post("/searches", response_model=HyperparameterSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_search(
    search_in: HyperparameterSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建超参搜索任务。"""
    search_space_dict = {
        k: v.model_dump() for k, v in search_in.search_space.items()
    }
    search_config_dict = search_in.search_config.model_dump()

    search = HyperparameterSearch(
        name=search_in.name,
        model_version=search_in.model_version,
        dataset_id=search_in.dataset_id,
        user_id=current_user.id,
        status="pending",
        method=search_in.search_config.method.value,
        search_space=search_space_dict,
        search_config=search_config_dict,
        n_trials=search_in.search_config.n_trials,
        base_config=search_in.base_config or {},
    )
    db.add(search)
    await db.flush()
    await db.refresh(search)

    # Submit async Celery task
    try:
        from app.tasks.hyperparameter_tasks import run_hyperparameter_search_task

        task_config = {
            "search_id": str(search.id),
            "model_version": search_in.model_version,
            "dataset_id": search_in.dataset_id,
            "search_space": search_space_dict,
            "search_config": search_config_dict,
            "base_config": search_in.base_config or {},
        }
        run_hyperparameter_search_task.delay(str(search.id), task_config)
    except Exception:
        pass  # Don't block creation if Celery is unavailable

    return search


@router.get("/searches", response_model=HyperparameterSearchListResponse)
async def list_searches(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取超参搜索任务列表。"""
    query = select(HyperparameterSearch).where(HyperparameterSearch.user_id == current_user.id)

    if status_filter:
        query = query.where(HyperparameterSearch.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(HyperparameterSearch.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    searches = list(result.scalars().all())

    return HyperparameterSearchListResponse(items=searches, total=total, page=page, page_size=page_size)


@router.get("/searches/{search_id}", response_model=HyperparameterSearchResponse)
async def get_search(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取超参搜索结果。"""
    result = await db.execute(
        select(HyperparameterSearch).where(
            HyperparameterSearch.id == search_id,
            HyperparameterSearch.user_id == current_user.id,
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="搜索任务不存在")
    return search


@router.get("/searches/{search_id}/trials", response_model=list[TrialResponse])
async def get_trials(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取搜索任务的所有试验。"""
    # Verify search belongs to user
    search_result = await db.execute(
        select(HyperparameterSearch).where(
            HyperparameterSearch.id == search_id,
            HyperparameterSearch.user_id == current_user.id,
        )
    )
    search = search_result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="搜索任务不存在")

    trials_result = await db.execute(
        select(HyperparameterTrial)
        .where(HyperparameterTrial.search_id == search_id)
        .order_by(HyperparameterTrial.trial_number)
    )
    return list(trials_result.scalars().all())


@router.post("/searches/{search_id}/cancel", response_model=HyperparameterSearchResponse)
async def cancel_search(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消超参搜索任务。"""
    result = await db.execute(
        select(HyperparameterSearch).where(
            HyperparameterSearch.id == search_id,
            HyperparameterSearch.user_id == current_user.id,
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="搜索任务不存在")

    if search.status not in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法取消状态为 {search.status} 的搜索任务",
        )

    search.status = "cancelled"
    await db.flush()
    await db.refresh(search)
    return search
