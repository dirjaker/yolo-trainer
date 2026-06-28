"""YOLO Trainer — FastAPI 应用入口。"""

import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.monitoring import metrics
from app.core.security_middleware import SecurityMiddleware

settings = get_settings()

# ── 日志初始化 ────────────────────────────────────────────────────────────
setup_logging(level="DEBUG" if settings.DEBUG else "INFO", json_format=not settings.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时清理资源。"""
    # ---- startup ----
    from app.core.database import init_db

    await init_db()
    logger.info("Application startup complete.")
    yield
    # ---- shutdown ----
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 YOLO 的目标检测模型训练平台 API",
    docs_url=None,  # 自定义 /docs，使用本地静态资源
    redoc_url=None,
    lifespan=lifespan,
)


# ── 安全中间件（按声明的逆序执行，SecurityMiddleware 先拦截） ─────────────
app.add_middleware(SecurityMiddleware)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# ── 请求指标中间件 ───────────────────────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    metrics.record_api_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )
    return response


# ── API 路由 ────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── 监控 & 健康检查路由（独立于 /api/v1） ────────────────────────────────
from app.api.v1.metrics import router as metrics_router  # noqa: E402

app.include_router(metrics_router, tags=["监控"])

# ── 静态文件（Swagger UI 本地化，不依赖 CDN） ─────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.responses import HTMLResponse  # noqa: E402


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """本地 Swagger UI，不依赖外部 CDN。"""
    return HTMLResponse(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link type="text/css" rel="stylesheet" href="/static/swagger-ui.css">
    <link rel="icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <title>{settings.APP_NAME} - Swagger UI</title>
</head>
<body>
<div id="swagger-ui"></div>
<script src="/static/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({{
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
    layout: "BaseLayout"
}})
</script>
</body>
</html>""")

# ── 前端静态文件（SPA 模式，与 API 共用端口） ─────────────────────────────
import os as _os  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

FRONTEND_DIST = _Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse  # noqa: F811

    class _SPAMiddleware:
        """将非 API/非静态请求回退到 index.html（Vue Router history 模式）。"""

        def __init__(self, app, dist_dir):
            self.app = app
            self.dist_dir = dist_dir

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                path = scope["path"]
                # API 和静态资源请求直接放行
                if path.startswith(("/api/", "/static/", "/docs", "/openapi.json", "/health", "/metrics")):
                    await self.app(scope, receive, send)
                    return
                # 尝试返回静态文件
                file_path = self.dist_dir / path.lstrip("/")
                if file_path.is_file():
                    from starlette.responses import FileResponse
                    from starlette.staticfiles import StaticFiles
                    await StaticFiles(directory=str(self.dist_dir))(scope, receive, send)
                    return
                # SPA fallback: 返回 index.html
                index_path = self.dist_dir / "index.html"
                if index_path.exists():
                    from starlette.responses import FileResponse
                    response = FileResponse(str(index_path))
                    await response(scope, receive, send)
                    return
            await self.app(scope, receive, send)

    app.add_middleware(_SPAMiddleware, dist_dir=FRONTEND_DIST)
    logger.info(f"Frontend SPA serving from: {FRONTEND_DIST}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "10003"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
