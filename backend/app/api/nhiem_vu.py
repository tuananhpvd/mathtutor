"""API giao bài/nhiệm vụ (A3): GV tạo/duyệt/giao; HS xem nhiệm vụ của mình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.nhiem_vu import TaoNhiemVuRequest
from app.services import nhiem_vu_service

router = APIRouter(prefix="/api/nhiem-vu", tags=["nhiem-vu"])
_GV = [require_role(VaiTro.gv)]
_HS = [require_role(VaiTro.hs)]


@router.post("", dependencies=_GV)
def tao(body: TaoNhiemVuRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return nhiem_vu_service.tao_nhiem_vu(
            db, current_user.id, body.tieu_de, body.mo_ta, body.han_chot,
            body.problem_ids, body.hoc_sinh_ids, body.lop_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gv", dependencies=_GV)
def danh_sach_gv(current_user: CurrentUser, db: Session = Depends(get_db)):
    return nhiem_vu_service.danh_sach_gv(db, current_user.id)


@router.get("/de-xuat", dependencies=_GV)
def de_xuat(hoc_sinh_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return nhiem_vu_service.de_xuat_theo_diem_yeu(db, current_user.id, hoc_sinh_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{nv_id}", dependencies=_GV)
def xoa(nv_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        nhiem_vu_service.xoa_nhiem_vu(db, current_user.id, nv_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/hs", dependencies=_HS)
def danh_sach_hs(current_user: CurrentUser, db: Session = Depends(get_db)):
    return nhiem_vu_service.danh_sach_hs(db, current_user.id)
