"""API quản trị (Phase 10): thống kê, tài khoản, cấu hình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.admin import DatCauHinhRequest, DoiTrangThaiRequest, TaoTaiKhoanRequest
from app.services.admin_service import (
    danh_sach_tai_khoan,
    dat_cau_hinh,
    doi_trang_thai_tai_khoan,
    lay_cau_hinh,
    tao_tai_khoan,
    thong_ke,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])
_ADMIN = [require_role(VaiTro.admin)]


@router.get("/stats", dependencies=_ADMIN)
def stats(current_user: CurrentUser, db: Session = Depends(get_db)):
    return thong_ke(db)


@router.get("/users", dependencies=_ADMIN)
def users(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_tai_khoan(db)


@router.post("/users", dependencies=_ADMIN)
def tao_user(body: TaoTaiKhoanRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        u = tao_tai_khoan(db, body.ho_ten, body.dang_nhap, body.mat_khau, body.vai_tro, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": u.id, "dang_nhap": u.dang_nhap, "vai_tro": u.vai_tro.value}


@router.patch("/users/{user_id}/trang-thai", dependencies=_ADMIN)
def doi_trang_thai(
    user_id: int,
    body: DoiTrangThaiRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        u = doi_trang_thai_tai_khoan(db, user_id, body.trang_thai)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": u.id, "trang_thai": u.trang_thai.value}


@router.get("/config", dependencies=_ADMIN)
def get_config(current_user: CurrentUser, db: Session = Depends(get_db)):
    return lay_cau_hinh(db)


@router.patch("/config", dependencies=_ADMIN)
def set_config(body: DatCauHinhRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return dat_cau_hinh(db, body.khoa, body.gia_tri)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
