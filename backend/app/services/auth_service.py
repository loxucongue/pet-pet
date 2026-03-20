"""认证服务，负责 JWT token 的签发与校验。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: int) -> str:
    """生成用户访问 token。"""

    if not settings.secret_key:
        raise ValueError("SECRET_KEY 未配置，无法生成访问 token。")

    expire_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> int:
    """校验 token 并返回 user_id。"""

    if not settings.secret_key:
        raise ValueError("SECRET_KEY 未配置，无法校验访问 token。")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("token 无效或已过期。") from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("token 缺少用户标识。")

    try:
        return int(user_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("token 中的用户标识无效。") from exc

