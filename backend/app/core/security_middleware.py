"""安全中间件 —— XSS 检测 + 安全响应头。

注：SQL 注入防护由 SQLAlchemy ORM 的参数化查询保障，无需在中间件层做正则检测（误报高且无效）。
"""

import logging
import re
from typing import List, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

_XSS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
]


def _detect_xss(value: str) -> bool:
    """检测字符串中是否存在 XSS 攻击模式。"""
    for pattern in _XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _scan_mapping(data: dict) -> List[str]:
    """扫描字典中所有字符串值。"""
    threats: List[str] = []
    for k, v in data.items():
        if isinstance(v, str) and _detect_xss(v):
            threats.append(f"{k}:xss")
    return threats


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件：XSS 防护 + 安全响应头。"""

    EXEMPT_PATHS: Set[str] = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        if path not in self.EXEMPT_PATHS:
            threats = _scan_mapping(dict(request.query_params))

            if request.method in ("POST", "PUT", "PATCH"):
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        body = await request.json()
                        if isinstance(body, dict):
                            threats.extend(_scan_mapping(body))
                    except Exception:
                        pass

            if threats:
                logger.warning(
                    "XSS threat detected: path=%s threats=%s ip=%s",
                    path, threats,
                    request.client.host if request.client else "unknown",
                )
                return Response(
                    content='{"detail":"请求包含不安全内容"}',
                    status_code=400,
                    media_type="application/json",
                )

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
