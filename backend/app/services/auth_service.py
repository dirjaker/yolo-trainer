"""用户认证服务"""

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user_data: dict) -> User:
    """创建新用户

    Args:
        db: 数据库会话
        user_data: 用户数据，包含 username, password, email 等

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
    """验证用户身份

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        User or None: 验证成功返回用户对象，失败返回 None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌

    Args:
        user_id: 用户 ID
        expires_delta: 过期时间增量

    Returns:
        str: JWT 令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
