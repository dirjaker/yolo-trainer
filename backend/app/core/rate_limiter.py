"""基于 Redis 滑动窗口的请求频率限制器。Redis 不可用时降级放行。"""

import logging
import time
from typing import Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: Optional[redis.Redis] = None
_redis_available: bool = True  # 降级标记


async def _get_pool() -> Optional[redis.Redis]:
    global _pool, _redis_available
    if not _redis_available:
        return None
    if _pool is None:
        try:
            _pool = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await _pool.ping()
        except Exception:
            logger.warning("Redis 不可用，限流器降级为放行模式")
            _redis_available = False
            _pool = None
            return None
    try:
        await _pool.ping()
    except Exception:
        logger.warning("Redis 连接丢失，限流器降级为放行模式")
        _redis_available = False
        _pool = None
        return None
    return _pool


class RateLimiter:
    """滑动窗口限流器。Redis 不可用时自动降级，放行所有请求。"""

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        key_func=None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_func = key_func or self._default_key

    @staticmethod
    def _default_key(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def __call__(self, request: Request):
        """FastAPI 依赖注入入口。"""
        r = await _get_pool()
        if r is None:
            return  # Redis 不可用，降级放行

        client_key = self.key_func(request)
        redis_key = f"rate_limit:{client_key}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipe = r.pipeline(transaction=True)
            pipe.zremrangebyscore(redis_key, 0, window_start)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, self.window_seconds)
            results = await pipe.execute()
            request_count = results[1]

            if request_count >= self.max_requests:
                logger.warning("Rate limit exceeded for %s", client_key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试",
                )
        except HTTPException:
            raise
        except Exception:
            logger.warning("限流器 Redis 操作失败，降级放行", exc_info=True)


def get_rate_limiter(max_requests: int = 60, window_seconds: int = 60):
    """工厂函数，返回一个可注入的限流器。"""
    return RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
