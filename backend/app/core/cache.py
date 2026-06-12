"""Redis 缓存层 —— 支持 get/set/delete/exists 及装饰器。"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 全局 Redis 连接池（惰性初始化）
_pool: Optional[redis.Redis] = None


async def _get_pool() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


class RedisCache:
    """异步 Redis 缓存封装。"""

    def __init__(self, prefix: str = "cache", default_ttl: int = 300):
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        r = await _get_pool()
        raw = await r.get(self._make_key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        r = await _get_pool()
        ttl = ttl or self.default_ttl
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        await r.set(self._make_key(key), value, ex=ttl)

    async def delete(self, key: str) -> None:
        r = await _get_pool()
        await r.delete(self._make_key(key))

    async def exists(self, key: str) -> bool:
        r = await _get_pool()
        return bool(await r.exists(self._make_key(key)))


# 默认缓存实例
cache = RedisCache()


def cached(ttl: int = 300, prefix: str = "cache", key_builder: Optional[Callable] = None):
    """异步函数缓存装饰器。

    用法::

        @cached(ttl=60)
        async def get_user(user_id: int):
            ...
    """
    _cache = RedisCache(prefix=prefix, default_ttl=ttl)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                raw = f"{func.__module__}:{func.__qualname__}:{args}:{kwargs}"
                cache_key = hashlib.md5(raw.encode()).hexdigest()

            hit = await _cache.get(cache_key)
            if hit is not None:
                logger.debug("Cache HIT: %s", cache_key)
                return hit

            logger.debug("Cache MISS: %s", cache_key)
            result = await func(*args, **kwargs)
            await _cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
