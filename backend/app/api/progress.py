"""API tiến độ học tập (Phase 6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.llm.client import get_llm_client
from app.models.user import VaiTro
from app.services.admin_service import lay_cau_hinh
from app.services.phan_tich_service import (
    cap_nhat_phan_tich,
    lay_phan_tich,
    tong_hop_lop_gv,
)
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


@router.get("/me/phan-tich", dependencies=[require_role(VaiTro.hs)])
def phan_tich_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    return lay_phan_tich(db, current_user.id)


@router.post("/me/phan-tich/cap-nhat", dependencies=[require_role(VaiTro.hs)])
def cap_nhat_phan_tich_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    return cap_nhat_phan_tich(db, current_user.id, get_llm_client(lay_cau_hinh(db)))


@router.get("/students", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tien_do_hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_lop(db, current_user.id)


@router.get("/lop/tong-hop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tong_hop_lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tong_hop_lop_gv(db, current_user.id)


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


@router.get("/students/{hoc_sinh_id}/phan-tich",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def phan_tich_hoc_sinh(hoc_sinh_id: int, current_user: CurrentUser,
                       db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return lay_phan_tich(db, hoc_sinh_id)


@router.post("/students/{hoc_sinh_id}/phan-tich/cap-nhat",
             dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def cap_nhat_phan_tich_hoc_sinh(hoc_sinh_id: int, current_user: CurrentUser,
                                db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return cap_nhat_phan_tich(db, hoc_sinh_id, get_llm_client(lay_cau_hinh(db)))
