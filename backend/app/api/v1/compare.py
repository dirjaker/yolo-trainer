"""模型对比 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.database import get_db_sync
from app.models.user import User
from app.schemas.compare import (
    CompareCreate,
    CompareListResponse,
    CompareResponse,
)
from app.services import compare_service

router = APIRouter()


@router.post("/", response_model=CompareResponse, summary="创建模型对比任务")
def create_compare(
    request: CompareCreate,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """创建模型对比任务。

    - **model_ids**: 要对比的模型 ID 列表（至少 2 个）
    - **test_dataset_id**: 测试数据集 ID
    - **name**: 对比任务名称（可选）

    支持对比指标：mAP, Precision, Recall, F1, 推理速度, 模型大小
    """
    compare = compare_service.create_compare(
        db=db,
        model_ids=request.model_ids,
        test_dataset_id=request.test_dataset_id,
        name=request.name,
        user_id=current_user.id,
    )
    return compare


@router.get("/{compare_id}", response_model=CompareResponse, summary="获取对比结果")
def get_compare(
    compare_id: str,
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """获取模型对比结果（仅限自己的对比任务）。"""
    compare = compare_service.get_compare(db, compare_id)
    if not compare:
        raise HTTPException(status_code=404, detail="对比任务不存在")
    if compare.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此对比任务")
    return compare


@router.get("/", response_model=CompareListResponse, summary="获取对比任务列表")
def list_compares(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db_sync),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的对比任务列表。"""
    items, total = compare_service.list_compares(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    return CompareListResponse(items=items, total=total)
