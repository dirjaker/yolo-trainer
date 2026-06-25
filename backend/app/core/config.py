import os
import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "YOLO Trainer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./yolo_trainer.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT — MUST be set via environment variable in production
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # API
    API_V1_STR: str = "/api/v1"

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 500

    def model_post_init(self, __context):
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = secrets.token_hex(32)


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    return settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "yolo-trainer"

    # Security
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    return settings
