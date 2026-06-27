"""模型部署 API"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db_sync
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


def _verify_model_ownership_sync(model_id: uuid.UUID, user_id: uuid.UUID, db: Session):
    """校验模型是否属于当前用户（同步版本）。"""
    model = (
        db.query(ModelVersion)
        .join(Training, ModelVersion.training_id == Training.id)
        .filter(ModelVersion.id == model_id, Training.user_id == user_id)
        .first()
    )
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在或无权操作")
    return model


def _get_owned_deployment_sync(deploy_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Deployment:
    """获取部署并校验所有权（同步版本）。"""
    deployment = db.query(Deployment).filter(
        Deployment.id == deploy_id, Deployment.user_id == user_id
    ).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment


@router.post("/", response_model=DeploymentResponse, summary="创建部署任务")
def create_deployment(
    request: DeploymentCreate,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """创建模型部署任务（仅限自己的模型）。"""
    _verify_model_ownership_sync(request.model_id, current_user.id, db)
    deployment = deploy_service.create_deployment(
        db=db,
        model_id=str(request.model_id),
        name=request.name,
        config=request.config.model_dump(),
        user_id=current_user.id,
    )
    return deployment


@router.get("/", response_model=DeploymentListResponse, summary="获取部署列表")
def list_deployments(
    deploy_status: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    platform: Optional[str] = Query(None, description="按平台筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的部署列表。"""
    query = db.query(Deployment).filter(Deployment.user_id == current_user.id)
    if deploy_status:
        query = query.filter(Deployment.status == deploy_status)
    if platform:
        query = query.filter(Deployment.platform == platform)

    total = query.count()
    items = (
        query.order_by(Deployment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return DeploymentListResponse(items=items, total=total)


@router.get("/{deploy_id}", response_model=DeploymentResponse, summary="获取部署详情")
def get_deployment(
    deploy_id: uuid.UUID,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """获取部署详情（仅限自己的部署）。"""
    return _get_owned_deployment_sync(deploy_id, current_user.id, db)


@router.get("/{deploy_id}/status", response_model=DeploymentStatusResponse, summary="获取部署状态")
def get_deployment_status(
    deploy_id: uuid.UUID,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """获取部署运行状态（仅限自己的部署）。"""
    _get_owned_deployment_sync(deploy_id, current_user.id, db)
    status_data = deploy_service.get_deployment_status(db, str(deploy_id))
    if not status_data:
        raise HTTPException(status_code=404, detail="部署不存在")
    return status_data


@router.post("/{deploy_id}/stop", response_model=DeploymentResponse, summary="停止部署")
def stop_deployment(
    deploy_id: uuid.UUID,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """停止部署（仅限自己的部署）。"""
    _get_owned_deployment_sync(deploy_id, current_user.id, db)
    deployment = deploy_service.stop_deployment(db, str(deploy_id))
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment
