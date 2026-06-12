"""Prometheus 指标 & 健康检查端点。"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.core.monitoring import metrics

settings = get_settings()
router = APIRouter()


@router.get("/metrics", summary="Prometheus 指标")
async def prometheus_metrics():
    """返回 Prometheus 文本格式的监控指标。"""
    return Response(
        content=metrics.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/health", summary="健康检查")
async def health_check():
    """应用健康检查端点。"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
