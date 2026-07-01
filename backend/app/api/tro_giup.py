"""API 'Nhờ thầy/cô' (A2): HS tạo yêu cầu; GV xem hàng đợi & trả lời."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.tro_giup import TaoYeuCauRequest, TraLoiRequest
from app.services import tro_giup_service

router = APIRouter(prefix="/api/tro-giup", tags=["tro-giup"])
_HS = [require_role(VaiTro.hs)]
_GV = [require_role(VaiTro.gv)]


@router.post("", dependencies=_HS)
def tao_yeu_cau(body: TaoYeuCauRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        return tro_giup_service.tao_yeu_cau(db, current_user.id, body.session_id, body.noi_dung)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gv", dependencies=_GV)
def danh_sach_gv(current_user: CurrentUser, chi_cho_xu_ly: bool = False,
                 db: Session = Depends(get_db)):
    return tro_giup_service.danh_sach_cho_gv(db, current_user.id, chi_cho_xu_ly)


@router.post("/{yc_id}/tra-loi", dependencies=_GV)
def tra_loi(yc_id: int, body: TraLoiRequest, current_user: CurrentUser,
            db: Session = Depends(get_db)):
    try:
        return tro_giup_service.tra_loi(db, current_user.id, yc_id, body.noi_dung)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{yc_id}", dependencies=_GV)
def xoa_yeu_cau(yc_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        tro_giup_service.xoa_yeu_cau(db, current_user.id, yc_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
