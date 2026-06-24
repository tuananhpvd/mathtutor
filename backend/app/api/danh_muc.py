"""API quản lý danh mục chuyên đề / dạng. GV + Admin."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.schemas.danh_muc import ChuyenDeCreate, ChuyenDeUpdate, DangCreate, DangUpdate
from app.services.danh_muc_service import (
    lay_toan_bo_danh_muc,
    sua_chuyen_de,
    sua_dang,
    tao_chuyen_de,
    tao_dang,
    xoa_chuyen_de,
    xoa_dang,
)

router = APIRouter(prefix="/api/danh-muc", tags=["danh-muc"])

_GV_ADMIN = [require_role(VaiTro.gv, VaiTro.admin)]
_ALL = [require_role(VaiTro.hs, VaiTro.gv, VaiTro.admin)]


# ---------- GET toàn bộ cây (tất cả vai trò) ----------

@router.get("", dependencies=_ALL)
def get_danh_muc(db: Session = Depends(get_db)):
    return lay_toan_bo_danh_muc(db)


# ---------- ChuyenDe CRUD ----------

@router.post("/chuyen-de", dependencies=_GV_ADMIN)
def them_chuyen_de(body: ChuyenDeCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        cd = tao_chuyen_de(db, body.ten, body.mo_ta, body.thu_tu, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": cd.id, "ten": cd.ten, "mo_ta": cd.mo_ta, "thu_tu": cd.thu_tu}


@router.patch("/chuyen-de/{cd_id}", dependencies=_GV_ADMIN)
def cap_nhat_chuyen_de(cd_id: int, body: ChuyenDeUpdate, db: Session = Depends(get_db)):
    try:
        cd = sua_chuyen_de(db, cd_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": cd.id, "ten": cd.ten, "mo_ta": cd.mo_ta, "thu_tu": cd.thu_tu}


@router.delete("/chuyen-de/{cd_id}", dependencies=_GV_ADMIN)
def xoa_chuyen_de_api(cd_id: int, db: Session = Depends(get_db)):
    try:
        xoa_chuyen_de(db, cd_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


# ---------- Dang CRUD ----------

@router.post("/dang", dependencies=_GV_ADMIN)
def them_dang(body: DangCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    try:
        d = tao_dang(db, body.chuyen_de_id, body.ten, body.mo_ta, body.thu_tu, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": d.id, "chuyen_de_id": d.chuyen_de_id, "ten": d.ten, "mo_ta": d.mo_ta, "thu_tu": d.thu_tu}


@router.patch("/dang/{dang_id}", dependencies=_GV_ADMIN)
def cap_nhat_dang(dang_id: int, body: DangUpdate, db: Session = Depends(get_db)):
    try:
        d = sua_dang(db, dang_id, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": d.id, "chuyen_de_id": d.chuyen_de_id, "ten": d.ten, "mo_ta": d.mo_ta, "thu_tu": d.thu_tu}


@router.delete("/dang/{dang_id}", dependencies=_GV_ADMIN)
def xoa_dang_api(dang_id: int, db: Session = Depends(get_db)):
    try:
        xoa_dang(db, dang_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
