"""YOLO Trainer — FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时清理资源。"""
    # ---- startup ----
    from app.core.database import init_db

    await init_db()
    yield
    # ---- shutdown ----


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 YOLO 的目标检测模型训练平台 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由 ────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── 静态文件服务（可选） ─────────────────────────────────────────────────
import os

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/data/uploads")
if os.path.isdir(UPLOAD_DIR):
    app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点。"""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
