"""API tiến độ học tập (Phase 6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.models.user import VaiTro
from app.services.progress_service import (
    hoc_sinh_thuoc_gv,
    thong_ke_chi_tiet,
    tien_do_cua_hs,
    tien_do_lop,
)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/me", dependencies=[require_role(VaiTro.hs)])
def tien_do_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_cua_hs(db, current_user.id)


@router.get("/me/thong-ke", dependencies=[require_role(VaiTro.hs)])
def thong_ke_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    return thong_ke_chi_tiet(db, current_user.id)


@router.get("/students", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tien_do_hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_lop(db, current_user.id)


@router.get("/students/{hoc_sinh_id}/thong-ke",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def thong_ke_hoc_sinh(hoc_sinh_id: int, current_user: CurrentUser,
                      db: Session = Depends(get_db)):
    # GV chỉ xem HS thuộc lớp mình; admin xem mọi HS.
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return thong_ke_chi_tiet(db, hoc_sinh_id)
