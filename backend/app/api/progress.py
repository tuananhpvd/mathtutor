"""API tiến độ học tập (Phase 6)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_role
from app.db.session import get_db
from app.llm.client import get_llm_client
from app.models.user import VaiTro
from app.services.admin_service import lay_cau_hinh
from app.services.bao_cao_service import bao_cao_hoc_sinh, bao_cao_lop
from app.services.hieu_qua_service import csv_hieu_qua_lop, hieu_qua_hs, hieu_qua_lop
from app.services.llm_quota_service import LOAI_PHAN_TICH, LOI_HET_QUOTA, ap_quota_tac_vu
from app.services.phan_tich_service import (
    ban_do_nang_luc,
    cap_nhat_phan_tich,
    lay_phan_tich,
    so_sanh_cac_lop_gv,
    tong_hop_lop_gv,
)
from app.services.progress_service import (
    hoc_sinh_thuoc_gv,
    kho_khan_theo_ngay,
    nhip_hoc_theo_ngay,
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


@router.get("/me/hieu-qua", dependencies=[require_role(VaiTro.hs)])
def hieu_qua_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    """HS tự xem chuỗi 8 tuần của chính mình (cùng dữ liệu GV xem qua /students/{id}/hieu-qua)."""
    return hieu_qua_hs(db, current_user.id)


@router.get("/me/nhip-ngay", dependencies=[require_role(VaiTro.hs)])
def nhip_ngay_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Nhịp học 30 ngày của chính HS (bài hoàn thành + phút học mỗi ngày) — biểu đồ vùng."""
    return nhip_hoc_theo_ngay(db, [current_user.id])


@router.get("/students/{hoc_sinh_id}/nhip-ngay",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def nhip_ngay_hoc_sinh(hoc_sinh_id: int, current_user: CurrentUser,
                       db: Session = Depends(get_db)):
    """GV xem nhịp học 30 ngày của 1 HS lớp mình (panel Tiến độ chi tiết)."""
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return nhip_hoc_theo_ngay(db, [hoc_sinh_id])


def _kiem_lop(db: Session, current_user, lop_id: int | None) -> None:
    """Chặn GV xem lớp không phải của mình (Admin xem lớp nào cũng được)."""
    if lop_id is None:
        return
    from app.models.lop import Lop

    lop = db.get(Lop, lop_id)
    if lop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp")
    if current_user.vai_tro == VaiTro.gv and lop.gv_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền với lớp này")


def _hs_ids_pham_vi(db: Session, current_user, lop_id: int | None) -> list[int]:
    """id HS trong phạm vi THỐNG KÊ (đã kiểm quyền lớp). lop_id có giá trị → chỉ lớp đó;
    None → mọi lớp GV phụ trách (chỉ dùng cho các số liệu cố ý gộp)."""
    _kiem_lop(db, current_user, lop_id)
    from app.models.lop import Lop
    from app.models.user import User

    if lop_id is not None:
        lop_ids = [lop_id]
    else:
        lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == current_user.id).all()]
    return (
        [u.id for u in db.query(User).filter(User.lop_id.in_(lop_ids)).all()]
        if lop_ids else []
    )


@router.get("/lop/nhip-ngay", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def nhip_ngay_lop(current_user: CurrentUser, lop_id: int | None = None,
                  db: Session = Depends(get_db)):
    """Nhịp học 30 ngày của MỘT lớp (lop_id); None → mọi lớp GV phụ trách."""
    return nhip_hoc_theo_ngay(db, _hs_ids_pham_vi(db, current_user, lop_id))


@router.get("/lop/kho-khan-ngay", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def kho_khan_ngay_lop(current_user: CurrentUser, lop_id: int | None = None,
                      db: Session = Depends(get_db)):
    """"Nhiệt kế khó khăn" 30 ngày: cờ + yêu cầu Nhờ thầy/cô mỗi ngày, theo MỘT lớp."""
    return kho_khan_theo_ngay(db, _hs_ids_pham_vi(db, current_user, lop_id))


@router.post("/me/phan-tich/cap-nhat", dependencies=[require_role(VaiTro.hs)])
def cap_nhat_phan_tich_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    cau_hinh = lay_cau_hinh(db)
    llm = ap_quota_tac_vu(db, cau_hinh, current_user.id, get_llm_client(cau_hinh),
                          LOAI_PHAN_TICH)
    if llm is None:
        raise HTTPException(status_code=429, detail=LOI_HET_QUOTA)
    return cap_nhat_phan_tich(db, current_user.id, llm)


@router.get("/students", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tien_do_hoc_sinh(current_user: CurrentUser, lop_id: int | None = None,
                     db: Session = Depends(get_db)):
    """Tiến độ HS của MỘT lớp (lop_id); None → mọi lớp GV phụ trách."""
    _kiem_lop(db, current_user, lop_id)
    return tien_do_lop(db, current_user.id, lop_id)


@router.get("/lop/tong-hop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def tong_hop_lop(current_user: CurrentUser, lop_id: int | None = None,
                 db: Session = Depends(get_db)):
    """Điểm yếu chung + HS cần chú ý của MỘT lớp (lop_id) — gộp nhiều lớp làm chìm khác biệt
    giữa các lớp nên không còn là mặc định."""
    _kiem_lop(db, current_user, lop_id)
    return tong_hop_lop_gv(db, current_user.id, lop_id)


@router.get("/lop/so-sanh", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def so_sanh_lop(current_user: CurrentUser, db: Session = Depends(get_db)):
    """Mỗi lớp một dòng trên cùng bộ chỉ số — thay cho số liệu gộp mọi lớp, vẫn so sánh được
    lớp nào đang đuối mà không làm chìm khác biệt giữa các lớp."""
    return so_sanh_cac_lop_gv(db, current_user.id)


@router.get("/me/ban-do", dependencies=[require_role(VaiTro.hs)])
def ban_do_cua_toi(current_user: CurrentUser, db: Session = Depends(get_db)):
    """C3 — bản đồ năng lực cá nhân (heatmap chuyên đề × độ khó)."""
    return ban_do_nang_luc(db, [current_user.id])


@router.get("/ban-do/lop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def ban_do_lop(current_user: CurrentUser, lop_id: int | None = None,
               db: Session = Depends(get_db)):
    """C3 — bản đồ năng lực của MỘT lớp (lop_id); None → dồn chung mọi lớp GV phụ trách.
    GV chỉ xem được lớp của mình, Admin xem lớp nào cũng được."""
    return ban_do_nang_luc(db, _hs_ids_pham_vi(db, current_user, lop_id))


@router.get("/students/{hoc_sinh_id}/ban-do",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def ban_do_hoc_sinh(hoc_sinh_id: int, current_user: CurrentUser,
                    db: Session = Depends(get_db)):
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    return ban_do_nang_luc(db, [hoc_sinh_id])


@router.get("/hieu-qua/lop", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def hieu_qua_phuong_phap_lop(current_user: CurrentUser, lop_id: int | None = None,
                             db: Session = Depends(get_db)):
    """C2 — số liệu chứng minh hiệu quả phương pháp gợi mở (tất định, không LLM).

    KHÁC các thống kê còn lại: ở đây `lop_id=None` (gộp mọi lớp) là một tùy chọn HỢP LỆ —
    hiệu quả phương pháp Socratic là thuộc tính của CÁCH DẠY chứ không của lớp, gộp cho mẫu
    lớn hơn nên tín hiệu ổn định hơn."""
    _kiem_lop(db, current_user, lop_id)
    return hieu_qua_lop(db, current_user.id, lop_id)


@router.get("/hieu-qua/lop/csv", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def hieu_qua_phuong_phap_lop_csv(current_user: CurrentUser, lop_id: int | None = None,
                                 db: Session = Depends(get_db)):
    """Xuất CSV bảng hiệu quả từng HS (kèm BOM UTF-8 để Excel mở đúng tiếng Việt).
    Theo đúng phạm vi đang xem trên màn hình (lop_id) — tránh file xuất ra lại gộp mọi lớp."""
    from fastapi.responses import Response

    _kiem_lop(db, current_user, lop_id)
    noi_dung = "﻿" + csv_hieu_qua_lop(db, current_user.id, lop_id)
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


# ---------- Xuất báo cáo kết quả cho phụ huynh (GV in ra PDF) ----------

def _cho_phep_xuat(db: Session, current_user) -> bool:
    """Admin luôn được; GV phụ thuộc cấu hình 'cho_phep_gv_xuat_bao_cao'."""
    if current_user.vai_tro == VaiTro.admin:
        return True
    return bool(lay_cau_hinh(db).get("cho_phep_gv_xuat_bao_cao"))


def _chan_neu_tat(db: Session, current_user) -> None:
    if not _cho_phep_xuat(db, current_user):
        raise HTTPException(status_code=403, detail="Tính năng xuất báo cáo đang tắt")


def _parse_ngay(s: str | None, cuoi_ngay: bool = False) -> datetime | None:
    """Chuỗi 'YYYY-MM-DD' → datetime; cuoi_ngay=True lấy cuối ngày (bao trọn ngày den_ngay)."""
    if not s:
        return None
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Ngày không hợp lệ (cần YYYY-MM-DD)") from e
    return d.replace(hour=23, minute=59, second=59) if cuoi_ngay else d


@router.get("/bao-cao/cho-phep", dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def bao_cao_cho_phep(current_user: CurrentUser, db: Session = Depends(get_db)):
    """FE hỏi trước để ẩn/hiện nút xuất (backend vẫn chốt lại 403 ở các endpoint dưới)."""
    return {"cho_phep": _cho_phep_xuat(db, current_user)}


@router.get("/students/{hoc_sinh_id}/bao-cao",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def bao_cao_hoc_sinh_api(hoc_sinh_id: int, current_user: CurrentUser,
                         tu_ngay: str | None = None, den_ngay: str | None = None,
                         db: Session = Depends(get_db)):
    _chan_neu_tat(db, current_user)
    if current_user.vai_tro == VaiTro.gv and not hoc_sinh_thuoc_gv(
        db, current_user.id, hoc_sinh_id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền xem học sinh này")
    try:
        return bao_cao_hoc_sinh(db, hoc_sinh_id,
                                _parse_ngay(tu_ngay), _parse_ngay(den_ngay, cuoi_ngay=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/lop/{lop_id}/bao-cao",
            dependencies=[require_role(VaiTro.gv, VaiTro.admin)])
def bao_cao_lop_api(lop_id: int, current_user: CurrentUser,
                    tu_ngay: str | None = None, den_ngay: str | None = None,
                    db: Session = Depends(get_db)):
    from app.models.lop import Lop

    _chan_neu_tat(db, current_user)
    lop = db.get(Lop, lop_id)
    if lop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp")
    if current_user.vai_tro == VaiTro.gv and lop.gv_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền với lớp này")
    return bao_cao_lop(db, lop_id,
                       _parse_ngay(tu_ngay), _parse_ngay(den_ngay, cuoi_ngay=True))
