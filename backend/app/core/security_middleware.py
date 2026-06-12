"""安全中间件 —— CORS、请求频率限制、SQL 注入检测、XSS 防护。"""

import logging
import re
from typing import List, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


# ── SQL 注入检测 ──────────────────────────────────────────────────────────
_SQL_INJECTION_PATTERNS = [
    re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
    re.compile(r"(\bselect\b.*\bfrom\b)", re.IGNORECASE),
    re.compile(r"(\binsert\b.*\binto\b)", re.IGNORECASE),
    re.compile(r"(\bdelete\b.*\bfrom\b)", re.IGNORECASE),
    re.compile(r"(\bdrop\b.*\btable\b)", re.IGNORECASE),
    re.compile(r"(\bupdate\b.*\bset\b)", re.IGNORECASE),
    re.compile(r"(--|;|/\*|\*/|@@|@)", re.IGNORECASE),
    re.compile(r"(\bor\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(\band\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(\'\s*(or|and)\s+\')", re.IGNORECASE),
]

_XSS_PATTERNS = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*svg\b.*?\bon\w+", re.IGNORECASE),
]


def _detect_sql_injection(value: str) -> bool:
    """检测字符串中是否存在 SQL 注入模式。"""
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _detect_xss(value: str) -> bool:
    """检测字符串中是否存在 XSS 攻击模式。"""
    for pattern in _XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _check_value(value: str) -> List[str]:
    """对单个值进行安全检测，返回发现的威胁列表。"""
    threats: List[str] = []
    if _detect_sql_injection(value):
        threats.append("sql_injection")
    if _detect_xss(value):
        threats.append("xss")
    return threats


def _scan_mapping(data: dict) -> List[str]:
    """扫描字典中所有字符串值。"""
    threats: List[str] = []
    for k, v in data.items():
        if isinstance(v, str):
            found = _check_value(v)
            if found:
                threats.extend(f"{k}:{t}" for t in found)
    return threats


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件：SQL 注入检测 + XSS 防护 + 安全响应头。"""

    # 不需要安全扫描的路径（如静态文件、指标接口）
    EXEMPT_PATHS: Set[str] = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # 仅对非豁免路径进行扫描
        if path not in self.EXEMPT_PATHS:
            # 扫描查询参数
            threats = _scan_mapping(dict(request.query_params))

            # 扫描请求体（仅对 POST/PUT/PATCH）
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
                    "Security threat detected: path=%s threats=%s ip=%s",
                    path,
                    threats,
                    request.client.host if request.client else "unknown",
                )
                return Response(
                    content='{"detail":"请求包含不安全内容"}',
                    status_code=400,
                    media_type="application/json",
                )

        response = await call_next(request)

        # 安全响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
