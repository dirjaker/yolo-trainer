"""用户认证服务（同步版本，供 Celery 任务和 Service 层使用）。"""

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

_settings = get_settings()


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_user(db: Session, user_data: dict) -> User:
    """创建新用户。

    Args:
        db: 数据库会话
        user_data: {username, password, email, is_superuser?}

    Returns:
        User: 创建的用户对象
    """
    hashed_password = get_password_hash(user_data["password"])
    user = User(
        username=user_data["username"],
        email=user_data.get("email"),
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=user_data.get("is_superuser", False),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户名密码。

    Returns:
        User if authenticated, None otherwise.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access token。

    Args:
        user_id: 用户 ID
        expires_delta: 过期时间增量

    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(
        to_encode,
        _settings.JWT_SECRET_KEY,
        algorithm=_settings.JWT_ALGORITHM,
    )
