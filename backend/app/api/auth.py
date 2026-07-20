from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.auth.security import create_access_token, verify_password
from app.auth.throttle import (
    ghi_nhan_sai,
    ghi_nhan_sai_ma,
    qua_nguong,
    qua_nguong_ma,
    xoa_lich_su_sai,
)
from app.db.session import get_db
from app.models.user import User, VaiTro
from app.schemas.auth import (
    DangKyBangMaRequest,
    LoginRequest,
    LoginResponse,
    LopTuMaResponse,
)
from app.services import dang_ky_service
from app.services.dang_ky_service import LoiDangKy

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _ip(request: Request) -> str:
    """IP client để tính throttle. Uvicorn chạy sau ProxyHeadersMiddleware nên
    `request.client.host` đã là IP thật, không phải IP của proxy Render."""
    return request.client.host if request.client else "?"


def _chan_neu_do_ma(request: Request) -> None:
    if qua_nguong_ma(_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Nhập sai mã quá nhiều lần. Vui lòng thử lại sau ít phút.",
        )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    if qua_nguong(body.dang_nhap):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Sai mật khẩu quá nhiều lần. Vui lòng thử lại sau vài phút.",
        )

    user = db.query(User).filter(User.dang_nhap == body.dang_nhap).first()
    if user is None or not verify_password(body.mat_khau, user.mat_khau_hash):
        ghi_nhan_sai(body.dang_nhap)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
        )
    if user.trang_thai.value == "khoa":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa")

    xoa_lich_su_sai(body.dang_nhap)
    token = create_access_token({"sub": str(user.id), "vai_tro": user.vai_tro.value})
    return LoginResponse(
        access_token=token,
        vai_tro=user.vai_tro.value,
        ho_ten=user.ho_ten,
        la_quan_ly=bool(user.la_quan_ly),
    )


# Route thử nghiệm cho từng vai trò
@router.get("/lop-tu-ma", response_model=LopTuMaResponse)
def lop_tu_ma(ma: str, request: Request, db: Session = Depends(get_db)):
    """CÔNG KHAI — xem trước lớp ứng với mã để HS xác nhận đúng lớp trước khi tạo tài khoản
    (chống vào nhầm lớp). Chỉ trả tên lớp + tên GV, không lộ gì thêm."""
    _chan_neu_do_ma(request)
    try:
        lop = dang_ky_service.lop_theo_ma(db, ma)
    except LoiDangKy as e:
        if e.ma_sai:
            ghi_nhan_sai_ma(_ip(request))
        raise HTTPException(status_code=400, detail=str(e)) from e
    return LopTuMaResponse(
        lop_ten=lop.ten,
        gv_ten=lop.giao_vien.ho_ten if lop.giao_vien else None,
        ma_het_han=lop.ma_het_han,
    )


@router.post("/dang-ky", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def dang_ky(body: DangKyBangMaRequest, request: Request, db: Session = Depends(get_db)):
    """CÔNG KHAI — HS tự tạo tài khoản bằng mã lớp rồi vào học ngay (trả token luôn).

    Vai trò luôn cứng là `hs` và lớp lấy từ mã (xem `dang_ky_service`), nên endpoint này
    không thể bị lợi dụng để tạo tài khoản GV/Admin.
    """
    _chan_neu_do_ma(request)
    try:
        hs = dang_ky_service.dang_ky_bang_ma(
            db, body.ma, body.ho_ten, body.dang_nhap, body.mat_khau
        )
    except LoiDangKy as e:
        if e.ma_sai:
            ghi_nhan_sai_ma(_ip(request))
        raise HTTPException(status_code=400, detail=str(e)) from e

    token = create_access_token({"sub": str(hs.id), "vai_tro": hs.vai_tro.value})
    return LoginResponse(
        access_token=token,
        vai_tro=hs.vai_tro.value,
        ho_ten=hs.ho_ten,
        la_quan_ly=False,
    )


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
