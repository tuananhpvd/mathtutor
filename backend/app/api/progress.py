"""API tiến độ học tập (Phase 6)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.llm.client import get_llm_client
from app.models.user import VaiTro
from app.services.admin_service import lay_cau_hinh
from app.services.hieu_qua_service import csv_hieu_qua_lop, hieu_qua_hs, hieu_qua_lop
from app.services.llm_quota_service import LOAI_PHAN_TICH, LOI_HET_QUOTA, ap_quota_tac_vu
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
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, current_user.id, get_llm_client(cau_hinh),
                          LOAI_PHAN_TICH)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    return cap_nhat_phan_tich(db, current_user.id, llm)


@router.get("/students", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tien_do_hoc_sinh(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tien_do_lop(db, current_user.id)


@router.get("/lop/tong-hop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tong_hop_lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    return tong_hop_lop_gv(db, current_user.id)


@router.get("/hieu-qua/lop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def hieu_qua_phuong_phap_lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    """C2 — số liệu chứng minh hiệu quả phương pháp gợi mở, cấp lớp (tất định, không LLM)."""
    return hieu_qua_lop(db, current_user.id)


@router.get("/hieu-qua/lop/csv", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def hieu_qua_phuong_phap_lop_csv(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Xuất CSV bảng hiệu quả từng HS (kèm BOM UTF-8 để Excel mở đúng tiếng Việt)."""
    from fastapi.responses import Response

    noi_dung = "﻿" + csv_hieu_qua_lop(db, current_user.id)
    return Response(
        content=noi_dung,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="hieu-qua-phuong-phap.csv"'},
    )


@router.get("/students/{hoc_sinh_id}/hieu-qua",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def hieu_qua_phuong_phap_hs(hoc_sinh_id: int, current_user: CurrentUser,
                            db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return hieu_qua_hs(db, hoc_sinh_id)


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
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, hoc_sinh_id, get_llm_client(cau_hinh), LOAI_PHAN_TICH)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    return cap_nhat_phan_tich(db, hoc_sinh_id, llm)
