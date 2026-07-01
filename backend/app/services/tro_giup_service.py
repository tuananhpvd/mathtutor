"""Dịch vụ 'Nhờ thầy/cô' (HS→GV) — A2.

HS bí một bài → tạo yêu cầu kèm ngữ cảnh; GV trả lời → câu trả lời chèn thành
một lượt 'giao_vien' trong khung hội thoại của bài + thông báo HS.
Không phụ thuộc LLM/web.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.lop import Lop
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.thong_bao import LoaiThongBao
from app.models.turn import Turn, VaiTroTurn
from app.models.user import User, VaiTro
from app.models.yeu_cau_tro_giup import TrangThaiTroGiup, YeuCauTroGiup
from app.services import thong_bao_service


def _gv_cua_hs(db: Session, hs_id: int) -> int | None:
    hs = db.get(User, hs_id)
    if hs is None or hs.lop_id is None:
        return None
    lop = db.get(Lop, hs.lop_id)
    return lop.gv_id if lop else None


def _mo_ta_bai(db: Session, problem_id: int) -> str:
    p = db.get(Problem, problem_id)
    if p is None:
        return "một bài tập"
    ten = p.chuyen_de or "bài tập"
    if p.dang:
        ten += f" › {p.dang.ten}"
    return ten


def tao_yeu_cau(db: Session, hs_id: int, session_id: int, noi_dung: str | None = None) -> dict:
    session = db.get(SessionModel, session_id)
    if session is None or session.hoc_sinh_id != hs_id:
        raise ValueError("Phiên không tồn tại")

    yc = YeuCauTroGiup(
        hoc_sinh_id=hs_id,
        session_id=session_id,
        problem_id=session.problem_id,
        buoc=session.buoc_hien_tai,
        y=session.y_hien_tai,
        noi_dung=(noi_dung or "").strip() or None,
    )
    db.add(yc)
    db.commit()
    db.refresh(yc)

    gv_id = _gv_cua_hs(db, hs_id)
    if gv_id:
        hs = db.get(User, hs_id)
        mo_ta = _mo_ta_bai(db, session.problem_id)
        chi_tiet = f"{hs.ho_ten} cần trợ giúp ở «{mo_ta}»"
        if yc.buoc:
            chi_tiet += f" (bước {yc.buoc}"
            chi_tiet += f", ý {yc.y})" if yc.y else ")"
        if yc.noi_dung:
            chi_tiet += f": {yc.noi_dung}"
        thong_bao_service.tao(
            db,
            nguoi_nhan_id=gv_id,
            noi_dung=chi_tiet,
            loai=LoaiThongBao.nho_tro_giup,
            nguoi_gui_id=hs_id,
            tieu_de="Học sinh nhờ trợ giúp",
            lien_ket_loai="session",
            lien_ket_id=session_id,
        )
    return {"id": yc.id}


def _dict(db: Session, yc: YeuCauTroGiup, hs_ten: dict | None = None) -> dict:
    hs = db.get(User, yc.hoc_sinh_id) if hs_ten is None else None
    return {
        "id": yc.id,
        "hoc_sinh_id": yc.hoc_sinh_id,
        "hoc_sinh_ten": (hs_ten or {}).get(yc.hoc_sinh_id) or (hs.ho_ten if hs else None),
        "session_id": yc.session_id,
        "problem_id": yc.problem_id,
        "bai": _mo_ta_bai(db, yc.problem_id),
        "buoc": yc.buoc,
        "y": yc.y,
        "noi_dung": yc.noi_dung,
        "trang_thai": yc.trang_thai.value,
        "tra_loi": yc.tra_loi,
        "tao_luc": yc.tao_luc.isoformat() if yc.tao_luc else None,
        "tra_loi_luc": yc.tra_loi_luc.isoformat() if yc.tra_loi_luc else None,
    }


def danh_sach_cho_gv(db: Session, gv_id: int, chi_cho_xu_ly: bool = False) -> list[dict]:
    lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()]
    if not lop_ids:
        return []
    hs = db.query(User).filter(User.vai_tro == VaiTro.hs, User.lop_id.in_(lop_ids)).all()
    hs_ten = {u.id: u.ho_ten for u in hs}
    hs_ids = list(hs_ten.keys())
    if not hs_ids:
        return []

    q = db.query(YeuCauTroGiup).filter(YeuCauTroGiup.hoc_sinh_id.in_(hs_ids))
    if chi_cho_xu_ly:
        q = q.filter(YeuCauTroGiup.trang_thai == TrangThaiTroGiup.cho_xu_ly)
    rows = q.order_by(YeuCauTroGiup.tao_luc.desc(), YeuCauTroGiup.id.desc()).all()
    return [_dict(db, r, hs_ten) for r in rows]


def tra_loi(db: Session, gv_id: int, yc_id: int, noi_dung: str) -> dict:
    yc = db.get(YeuCauTroGiup, yc_id)
    if yc is None:
        raise ValueError("Yêu cầu không tồn tại")
    if _gv_cua_hs(db, yc.hoc_sinh_id) != gv_id:
        raise ValueError("Không có quyền với yêu cầu này")
    noi_dung = (noi_dung or "").strip()
    if not noi_dung:
        raise ValueError("Nội dung trả lời không được để trống")

    # Chèn câu trả lời GV vào khung hội thoại của bài.
    db.add(Turn(session_id=yc.session_id, vai_tro=VaiTroTurn.giao_vien, noi_dung=noi_dung))
    yc.trang_thai = TrangThaiTroGiup.da_tra_loi
    yc.tra_loi = noi_dung
    yc.gv_id = gv_id
    yc.tra_loi_luc = datetime.now(timezone.utc)
    db.commit()

    thong_bao_service.tao(
        db,
        nguoi_nhan_id=yc.hoc_sinh_id,
        noi_dung=noi_dung,
        loai=LoaiThongBao.tra_loi,
        nguoi_gui_id=gv_id,
        tieu_de="Thầy/cô đã trả lời",
        lien_ket_loai="session",
        lien_ket_id=yc.session_id,
    )
    return {"id": yc.id, "trang_thai": yc.trang_thai.value}
