import os
import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "YOLO Trainer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./yolo_trainer.db"

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── JWT Authentication ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days (dev)

    # ── File Upload ──────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 2048  # 2 GB

    # ── MinIO / Object Storage (optional) ─────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "yolo-trainer"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# 启动时安全校验
_settings = get_settings()
if _settings.JWT_SECRET_KEY == "dev-secret-change-in-production" and not _settings.DEBUG:
    raise RuntimeError(
        "JWT_SECRET_KEY 仍为默认值，禁止在生产环境启动。"
        "请设置环境变量 JWT_SECRET_KEY。"
    )
