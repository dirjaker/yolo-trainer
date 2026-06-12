"""数据库连接 —— 连接池配置 + 重试机制。"""

import asyncio
import logging
from functools import wraps
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── 重试装饰器 ───────────────────────────────────────────────────────────
def retry_on_db_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """数据库操作重试装饰器，支持指数退避。

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            current_delay = delay
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        logger.warning(
                            "DB operation failed (attempt %d/%d), retrying in %.1fs: %s",
                            attempt, max_retries, current_delay, exc,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error("DB operation failed after %d attempts: %s", max_retries, exc)
            raise last_exc  # type: ignore
        return wrapper
    return decorator


# ── 连接池 ───────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,       # 每 30 分钟回收连接，避免被服务端断开
    connect_args={
        "command_timeout": 10,
        "server_settings": {"application_name": "yolo_trainer"},
    },
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入 —— 获取数据库会话。"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表结构。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialised.")
