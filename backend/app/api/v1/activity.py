"""Activity API routes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityListResponse
from app.services import activity_service

router = APIRouter()


@router.get("/activities", response_model=ActivityListResponse)
def list_activities(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve activity logs with optional filters and pagination."""
    items, total = activity_service.get_activities(
        db,
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return ActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
