"""API mục tiêu học tập (B1): HS tự đặt, GV đặt cho HS, hệ thống gợi ý."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.muc_tieu import TaoMucTieuRequest
from app.services import muc_tieu_service
from app.services.gv_service import _so_huu_hs

router = APIRouter(prefix="/api/muc-tieu", tags=["muc-tieu"])
_HS = [require_role(VaiTro.hs)]
_GV = [require_role(VaiTro.gv)]


# ----- HS -----
@router.get("/hs", dependencies=_HS)
def hs_danh_sach(current_user: CurrentUser, db: Session = Depends(get_db)):
    return muc_tieu_service.danh_sach(db, current_user.id)


@router.get("/hs/de-xuat", dependencies=_HS)
def hs_de_xuat(current_user: CurrentUser, db: Session = Depends(get_db)):
    return muc_tieu_service.de_xuat(db, current_user.id)


@router.post("/hs", dependencies=_HS)
def hs_tao(body: TaoMucTieuRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return muc_tieu_service.tao(
            db, current_user.id, current_user.id, "hs", body.loai, body.tieu_de,
            body.chi_tieu_so, body.dang_id, body.chuyen_de, body.han,
            muc=[m.model_dump() for m in body.muc] if body.muc else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ----- GV -----
@router.get("/gv/{hoc_sinh_id}", dependencies=_GV)
def gv_danh_sach(hoc_sinh_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    if not _so_huu_hs(db, current_user.id, hoc_sinh_id):
        raise HTTPException(status_code=403, detail="Không có quyền với học sinh này")
    return muc_tieu_service.danh_sach(db, hoc_sinh_id)


@router.get("/gv/{hoc_sinh_id}/de-xuat", dependencies=_GV)
def gv_de_xuat(hoc_sinh_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    if not _so_huu_hs(db, current_user.id, hoc_sinh_id):
        raise HTTPException(status_code=403, detail="Không có quyền với học sinh này")
    return muc_tieu_service.de_xuat(db, hoc_sinh_id)


@router.post("/gv/{hoc_sinh_id}", dependencies=_GV)
def gv_tao(hoc_sinh_id: int, body: TaoMucTieuRequest, current_user: CurrentUser,
           db: Session = Depends(get_db)):
    if not _so_huu_hs(db, current_user.id, hoc_sinh_id):
        raise HTTPException(status_code=403, detail="Không có quyền với học sinh này")
    try:
        return muc_tieu_service.tao(
            db, hoc_sinh_id, current_user.id, "gv", body.loai, body.tieu_de,
            body.chi_tieu_so, body.dang_id, body.chuyen_de, body.han,
            muc=[m.model_dump() for m in body.muc] if body.muc else None, bao_hs=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ----- Chung -----
@router.delete("/{mt_id}", dependencies=[require_role(VaiTro.hs, VaiTro.gv)])
def xoa(mt_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        muc_tieu_service.xoa(db, current_user, mt_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}
