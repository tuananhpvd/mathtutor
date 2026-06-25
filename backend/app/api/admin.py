"""API quản trị (Phase 10): thống kê, tài khoản, cấu hình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.admin import (
    DatCauHinhRequest,
    DoiTrangThaiRequest,
    GanLopRequest,
    SuaLopRequest,
    SuaTaiKhoanRequest,
    TaoLopRequest,
    TaoTaiKhoanRequest,
)
from app.services.admin_service import (
    danh_sach_giao_vien,
    danh_sach_hoc_sinh,
    danh_sach_lop,
    danh_sach_lop_chi_tiet,
    danh_sach_tai_khoan,
    dat_cau_hinh,
    doi_trang_thai_tai_khoan,
    gan_lop_tai_khoan,
    lay_cau_hinh,
    sua_lop,
    sua_tai_khoan,
    tao_lop,
    tao_tai_khoan,
    thong_ke,
    xoa_lop,
    xoa_tai_khoan,
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


@router.patch("/users/{user_id}", dependencies=_ADMIN)
def sua_user(user_id: int, body: SuaTaiKhoanRequest, current_user: CurrentUser,
             db: Session = Depends(get_db)):
    try:
        u = sua_tai_khoan(db, user_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": u.id, "ho_ten": u.ho_ten, "dang_nhap": u.dang_nhap, "vai_tro": u.vai_tro.value}


@router.delete("/users/{user_id}", dependencies=_ADMIN)
def xoa_user(user_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        xoa_tai_khoan(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/lop", dependencies=_ADMIN)
def lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_lop(db)


@router.get("/lop-chi-tiet", dependencies=_ADMIN)
def lop_chi_tiet(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_lop_chi_tiet(db)


@router.post("/lop", dependencies=_ADMIN)
def them_lop(body: TaoLopRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        lop_ = tao_lop(db, body.ten, body.gv_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": lop_.id, "ten": lop_.ten, "gv_id": lop_.gv_id}


@router.patch("/lop/{lop_id}", dependencies=_ADMIN)
def cap_nhat_lop(lop_id: int, body: SuaLopRequest, current_user: CurrentUser,
                 db: Session = Depends(get_db)):
    try:
        lop_ = sua_lop(db, lop_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": lop_.id, "ten": lop_.ten, "gv_id": lop_.gv_id}


@router.delete("/lop/{lop_id}", dependencies=_ADMIN)
def xoa_lop_ep(lop_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        xoa_lop(db, lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/giao-vien", dependencies=_ADMIN)
def giao_vien(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_giao_vien(db)


@router.get("/hoc-sinh", dependencies=_ADMIN)
def hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_hoc_sinh(db)


@router.patch("/users/{user_id}/lop", dependencies=_ADMIN)
def gan_lop(user_id: int, body: GanLopRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        u = gan_lop_tai_khoan(db, user_id, body.lop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": u.id, "lop_id": u.lop_id}


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
