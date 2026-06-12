"""基于 Redis 滑动窗口的请求频率限制器。"""

import logging
import time
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: Optional[redis.Redis] = None


async def _get_pool() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _pool


class RateLimiter:
    """滑动窗口限流器。

    Args:
        max_requests: 时间窗口内允许的最大请求数
        window_seconds: 时间窗口大小（秒）
        key_func: 从 Request 中提取唯一标识的函数，默认使用客户端 IP
    """

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
        client_key = self.key_func(request)
        redis_key = f"rate_limit:{client_key}"

        r = await _get_pool()
        now = time.time()
        window_start = now - self.window_seconds

        pipe = r.pipeline(transaction=True)
        # 移除窗口外的记录
        pipe.zremrangebyscore(redis_key, 0, window_start)
        # 统计窗口内请求数
        pipe.zcard(redis_key)
        # 添加当前请求
        pipe.zadd(redis_key, {str(now): now})
        # 设置过期时间
        pipe.expire(redis_key, self.window_seconds)
        results = await pipe.execute()

        request_count = results[1]

        if request_count >= self.max_requests:
            logger.warning("Rate limit exceeded for %s", client_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
            )


def get_rate_limiter(max_requests: int = 60, window_seconds: int = 60):
    """工厂函数，返回一个可注入的限流器。"""
    return RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
