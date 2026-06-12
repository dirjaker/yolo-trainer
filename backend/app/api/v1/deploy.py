"""模型部署 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.deploy import (
    DeploymentCreate,
    DeploymentListResponse,
    DeploymentResponse,
    DeploymentStatusResponse,
)
from app.services import deploy_service

router = APIRouter()


@router.post("/", response_model=DeploymentResponse, summary="创建部署任务")
async def create_deployment(
    request: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建模型部署任务

    - **model_id**: 要部署的模型 ID
    - **name**: 部署名称
    - **config**: 部署配置
      - platform: 部署平台 (onnx_runtime / tensorrt / torchserve)
      - port: 服务端口
      - workers: 工作进程数
      - batch_size: 批量大小
      - gpu: 是否使用 GPU
    """
    deployment = deploy_service.create_deployment(
        db=db,
        model_id=request.model_id,
        name=request.name,
        config=request.config.model_dump(),
    )
    return deployment


@router.get("/", response_model=DeploymentListResponse, summary="获取部署列表")
async def list_deployments(
    status: Optional[str] = Query(None, description="按状态筛选"),
    platform: Optional[str] = Query(None, description="按平台筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取部署列表

    - **status**: 按状态筛选 (pending / deploying / running / stopped / failed)
    - **platform**: 按平台筛选 (onnx_runtime / tensorrt / torchserve)
    """
    items, total = deploy_service.list_deployments(
        db, status=status, platform=platform, page=page, page_size=page_size
    )
    return DeploymentListResponse(items=items, total=total)


@router.get("/{deploy_id}", response_model=DeploymentResponse, summary="获取部署详情")
async def get_deployment(
    deploy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取部署详情

    - **deploy_id**: 部署 ID
    """
    deployment = deploy_service.get_deployment(db, deploy_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment


@router.get("/{deploy_id}/status", response_model=DeploymentStatusResponse, summary="获取部署状态")
async def get_deployment_status(
    deploy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取部署运行状态

    - **deploy_id**: 部署 ID

    返回部署的健康状态、运行时长、请求计数、平均延迟等信息
    """
    status = deploy_service.get_deployment_status(db, deploy_id)
    if not status:
        raise HTTPException(status_code=404, detail="部署不存在")
    return status


@router.post("/{deploy_id}/stop", response_model=DeploymentResponse, summary="停止部署")
async def stop_deployment(
    deploy_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """停止部署

    - **deploy_id**: 部署 ID
    """
    deployment = deploy_service.stop_deployment(db, deploy_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="部署不存在")
    return deployment
