from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.auth.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User, VaiTro
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.dang_nhap == body.dang_nhap).first()
    if user is None or not verify_password(body.mat_khau, user.mat_khau_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )
    if user.trang_thai.value == "khoa":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa")

    token = create_access_token({"sub": str(user.id), "vai_tro": user.vai_tro.value})
    return LoginResponse(
        access_token=token,
        vai_tro=user.vai_tro.value,
        ho_ten=user.ho_ten,
        la_quan_ly=bool(user.la_quan_ly),
    )


# Route thử nghiệm cho từng vai trò
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
gv_router = APIRouter(prefix="/api/gv", tags=["gv"])
hs_router = APIRouter(prefix="/api/hs", tags=["hs"])


@admin_router.get("/ping", dependencies=[require_role(VaiTro.admin)])
def admin_ping(current_user: CurrentUser):
    return {"message": f"Xin chào Admin {current_user.ho_ten}"}


@gv_router.get("/ping", dependencies=[require_role(VaiTro.gv)])
def gv_ping(current_user: CurrentUser):
    return {"message": f"Xin chào GV {current_user.ho_ten}"}


@hs_router.get("/ping", dependencies=[require_role(VaiTro.hs)])
def hs_ping(current_user: CurrentUser):
    return {"message": f"Xin chào HS {current_user.ho_ten}"}
