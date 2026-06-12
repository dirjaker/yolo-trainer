"""API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.training import router as training_router
from app.api.v1.model import router as model_router
from app.api.v1.dataset import router as dataset_router
from app.api.v1.test import router as test_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(training_router, prefix="/training", tags=["训练"])
api_router.include_router(model_router, prefix="/models", tags=["模型"])
api_router.include_router(dataset_router, prefix="/datasets", tags=["数据集"])
api_router.include_router(test_router, prefix="/test", tags=["测试"])
