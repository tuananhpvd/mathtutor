"""API tóm tắt lý thuyết (Pha 1). GV soạn/quản lý; HS chỉ xem bản hien=True của GV chủ nhiệm."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, co_toan_quyen, require_role
from app.db.session import get_db
from app.models.danh_muc import ChuyenDe
from app.models.lop import Lop
from app.models.tom_tat_ly_thuyet import TomTatLyThuyet
from app.models.user import User, VaiTro
from app.schemas.tom_tat_ly_thuyet import TomTatCreate, TomTatUpdate
from app.services.tom_tat_ly_thuyet_service import (
    danh_sach_gv,
    danh_sach_hs,
    sua_tom_tat,
    tao_tom_tat,
    xoa_tom_tat,
)

router = APIRouter(prefix="/api/ly-thuyet", tags=["ly-thuyet"])

_GV_ADMIN = [require_role(VaiTro.gv, VaiTro.admin)]
_HS = [require_role(VaiTro.hs)]


def _gv_id_cua_lop_hs(db: Session, hs: User) -> int | None:
    if hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def _quyen_tren_cd(user: User, cd: ChuyenDe) -> bool:
    return co_toan_quyen(user) or cd.nguoi_tao_id == user.id


def _quyen_tren_tt(user: User, tt: TomTatLyThuyet) -> bool:
    return co_toan_quyen(user) or tt.nguoi_tao_id == user.id


# ---------- GV/Admin ----------

@router.get("/gv", dependencies=_GV_ADMIN)
def gv_danh_sach(current_user: CurrentUser, db: Session = Depends(get_db)):
    return danh_sach_gv(db, current_user.id)


@router.post("", dependencies=_GV_ADMIN)
def tao(body: TomTatCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    cd = db.get(ChuyenDe, body.chuyen_de_id)
    if cd is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyên đề")
    if not _quyen_tren_cd(current_user, cd):
        raise HTTPException(status_code=403, detail="Bạn không có quyền tạo tóm tắt cho chuyên đề này")
    try:
        # Chủ sở hữu tóm tắt luôn theo chủ chuyên đề (kể cả khi Quản lý tạo hộ) — nhất quán
        # với quy ước "Dạng thuộc cùng chủ sở hữu với chuyên đề" ở danh_muc.
        tt = tao_tom_tat(db, cd.nguoi_tao_id, body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": tt.id}


@router.patch("/{tt_id}", dependencies=_GV_ADMIN)
def sua(tt_id: int, body: TomTatUpdate, current_user: CurrentUser, db: Session = Depends(get_db)):
    tt = db.get(TomTatLyThuyet, tt_id)
    if tt is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tóm tắt")
    if not _quyen_tren_tt(current_user, tt):
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa tóm tắt này")
    try:
        sua_tom_tat(db, tt_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}


@router.delete("/{tt_id}", dependencies=_GV_ADMIN)
def xoa(tt_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
    tt = db.get(TomTatLyThuyet, tt_id)
    if tt is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tóm tắt")
    if not _quyen_tren_tt(current_user, tt):
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa tóm tắt này")
    xoa_tom_tat(db, tt_id)
    return {"ok": True}


# ---------- Học sinh ----------

@router.get("/hs", dependencies=_HS)
def hs_danh_sach(current_user: CurrentUser, chuyen_de_id: int | None = None,
                 dang_id: int | None = None, db: Session = Depends(get_db)):
    gv_id = _gv_id_cua_lop_hs(db, current_user)
    if gv_id is None:
        return []
    return danh_sach_hs(db, gv_id, chuyen_de_id, dang_id)
