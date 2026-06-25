"""模型部署 API"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.deployment import Deployment
from app.models.model import ModelVersion
from app.models.training import Training
from app.models.user import User
from app.schemas.deploy import (
    DeploymentCreate,
    DeploymentListResponse,
    DeploymentResponse,
    DeploymentStatusResponse,
)
from app.services import deploy_service

router = APIRouter()


async def _verify_model_ownership(model_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    """校验模型是否属于当前用户。"""
    result = await db.execute(
        select(ModelVersion)
        .join(Training, ModelVersion.training_id == Training.id)
        .where(ModelVersion.id == model_id, Training.user_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在或无权操作")
    return model


@router.post("/", response_model=DeploymentResponse, summary="创建部署任务")
async def create_deployment(
    request: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建模型部署任务（仅限自己的模型）。"""
    await _verify_model_ownership(request.model_id, current_user.id, db)
    deployment = deploy_service.create_deployment(
        db=db,
        model_id=str(request.model_id),
        name=request.name,
        config=request.config.model_dump(),
        user_id=current_user.id,
    )
    return deployment


@router.get("/", response_model=DeploymentListResponse, summary="获取部署列表")
async def list_deployments(
    deploy_status: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    platform: Optional[str] = Query(None, description="按平台筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的部署列表。"""
    query = select(Deployment).where(Deployment.user_id == current_user.id)
    if deploy_status:
        query = query.where(Deployment.status == deploy_status)
    if platform:
        query = query.where(Deployment.platform == platform)

    from sqlalchemy import func
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Deployment.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return DeploymentListResponse(items=items, total=total)


async def _get_owned_deployment(deploy_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Deployment:
    """获取部署并校验所有权。"""
    result = await db.execute(
        select(Deployment).where(Deployment.id == deploy_id, Deployment.user_id == user_id)
    )
    deployment = result.scalar_one_or_none()
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment


@router.get("/{deploy_id}", response_model=DeploymentResponse, summary="获取部署详情")
async def get_deployment(
    deploy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部署详情（仅限自己的部署）。"""
    return await _get_owned_deployment(deploy_id, current_user.id, db)


@router.get("/{deploy_id}/status", response_model=DeploymentStatusResponse, summary="获取部署状态")
async def get_deployment_status(
    deploy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部署运行状态（仅限自己的部署）。"""
    deployment = await _get_owned_deployment(deploy_id, current_user.id, db)
    status_data = deploy_service.get_deployment_status(db, str(deploy_id))
    if not status_data:
        raise HTTPException(status_code=404, detail="部署不存在")
    return status_data


@router.post("/{deploy_id}/stop", response_model=DeploymentResponse, summary="停止部署")
async def stop_deployment(
    deploy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """停止部署（仅限自己的部署）。"""
    await _get_owned_deployment(deploy_id, current_user.id, db)
    deployment = deploy_service.stop_deployment(db, str(deploy_id))
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment
