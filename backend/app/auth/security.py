from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def vo_hieu_hoa_token_cu(user) -> None:
    """Thu hồi MỌI JWT đã phát trước đó của `user`: tăng `token_version` lên 1. Lần kiểm tra
    tiếp theo (auth/deps.py) sẽ thấy token cũ mang version thấp hơn → 401.

    Dùng khi: đổi mật khẩu, khóa tài khoản, hoặc buộc đăng xuất mọi thiết bị. KHÔNG tự commit —
    caller commit chung transaction đang mở (thường ngay sau đó đã có db.commit()).
    Nhận `user` kiểu duck-typed (không import model User để tránh phụ thuộc vòng)."""
    user.token_version = (user.token_version or 0) + 1
