"""Activity service — logging and querying activity events."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.activity import Activity


def log_activity(
    db: Session,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
) -> Activity:
    """Persist an activity log entry."""
    activity = Activity(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activities(
    db: Session,
    *,
    user_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Activity], int]:
    """Query activities with optional filters and pagination."""
    query = db.query(Activity)

    if user_id is not None:
        query = query.filter(Activity.user_id == user_id)
    if resource_type is not None:
        query = query.filter(Activity.resource_type == resource_type)
    if start_date is not None:
        query = query.filter(Activity.created_at >= start_date)
    if end_date is not None:
        query = query.filter(Activity.created_at <= end_date)

    total = query.count()
    items = (
        query.order_by(desc(Activity.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
