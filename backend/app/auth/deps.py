from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError as JWTError
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.db.session import get_db
from app.models.user import User, VaiTro

bearer_scheme = HTTPBearer()


def _get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: int = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ"
        ) from e

    user = db.get(User, user_id)
    if user is None or user.trang_thai.value == "khoa":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại hoặc bị khóa")
    # Thu hồi token: token mang "tv" (token_version lúc phát) — lệch với version hiện tại trong
    # DB nghĩa là mật khẩu đã đổi / tài khoản bị khóa-mở / buộc đăng xuất SAU khi token này phát.
    # Token đời trước (không có claim "tv") → .get mặc định 0, khớp token_version=0 của tài khoản
    # chưa từng đổi mật khẩu, nên KHÔNG bị đá văng oan lúc mới triển khai tính năng này.
    if payload.get("tv", 0) != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hiệu lực — vui lòng đăng nhập lại.",
        )
    return user


CurrentUser = Annotated[User, Depends(_get_current_user)]


def co_toan_quyen(user: User) -> bool:
    """Toàn quyền trên nội dung của MỌI GV: Admin hoặc tài khoản Quản lý."""
    return user.vai_tro == VaiTro.admin or bool(user.la_quan_ly)


def require_role(*roles: VaiTro):
    def _check(current_user: CurrentUser) -> User:
        if current_user.vai_tro not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Yêu cầu vai trò: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return Depends(_check)
