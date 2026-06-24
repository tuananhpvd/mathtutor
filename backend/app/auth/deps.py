from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
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
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")

    user = db.get(User, user_id)
    if user is None or user.trang_thai.value == "khoa":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại hoặc bị khóa")
    return user


CurrentUser = Annotated[User, Depends(_get_current_user)]


def require_role(*roles: VaiTro):
    def _check(current_user: CurrentUser) -> User:
        if current_user.vai_tro not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Yêu cầu vai trò: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return Depends(_check)
