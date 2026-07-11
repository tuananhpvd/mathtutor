"""Dịch vụ 'Nhờ thầy/cô' (HS→GV) — A2.

HS bí một bài → tạo yêu cầu kèm ngữ cảnh; GV trả lời → câu trả lời chèn thành
một lượt 'giao_vien' trong khung hội thoại của bài + thông báo HS.
Không phụ thuộc LLM/web.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.guard.safety import kiem_tra_an_toan
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


def _noi_dung_cau_hoi(db: Session, problem_id: int) -> dict:
    """Trả de_bai + loai_cau + nội dung hiển thị (phương án / ý) — không lộ đáp án đúng."""
    p = db.get(Problem, problem_id)
    if p is None:
        return {}
    meta = p.meta or {}
    loai = p.loai_cau.value if p.loai_cau else None
    if loai == "TN4PA":
        meta_hien_thi = {"phuong_an": meta.get("phuong_an") or {}}
    elif loai == "TNDS":
        meta_hien_thi = {
            "y": [{"ky_hieu": y.get("ky_hieu", ""), "noi_dung_y": y.get("noi_dung_y", "")}
                  for y in meta.get("y") or []]
        }
    else:
        meta_hien_thi = {}
    return {"de_bai": p.de_bai, "loai_cau": loai, "meta_hien_thi": meta_hien_thi}


def tao_yeu_cau(db: Session, hs_id: int, session_id: int, noi_dung: str | None = None) -> dict:
    session = db.get(SessionModel, session_id)
    if session is None or session.hoc_sinh_id != hs_id:
        raise ValueError("Phiên không tồn tại")

    noi_dung_sach = (noi_dung or "").strip() or None
    # Lọc an toàn nhưng KHÔNG chặn — khác với chat với AI, nội dung này gửi thẳng cho GV
    # (con người), nên dù bị lớp lọc phát hiện (vd từ khoá nhạy cảm) vẫn cho gửi tới GV,
    # tránh trường hợp đây là lời kêu cứu thật của HS mà bị âm thầm chặn. Chỉ gắn cờ +
    # nâng mức khẩn cấp của thông báo để GV chú ý ngay.
    ly_do_khong_an_toan = None
    khan_cap = False
    if noi_dung_sach:
        from app.services.admin_service import lay_tu_khoa_an_toan

        tu_khoa = lay_tu_khoa_an_toan(db)
        ks = kiem_tra_an_toan(
            noi_dung_sach,
            tu_khoa["tu_khoa_khan_cap"],
            tu_khoa["tu_khoa_khong_phu_hop"],
            tu_khoa["tu_khoa_ngoai_pham_vi"],
        )
        if not ks.an_toan:
            ly_do_khong_an_toan = ks.ly_do
            khan_cap = ks.khan_cap

    yc = YeuCauTroGiup(
        hoc_sinh_id=hs_id,
        session_id=session_id,
        problem_id=session.problem_id,
        buoc=session.buoc_hien_tai,
        y=session.y_hien_tai,
        noi_dung=noi_dung_sach,
    )
    db.add(yc)
    # Lưu turn HS để khi tải lại session vẫn thấy ngữ cảnh nhờ thầy/cô.
    chat_nd = f"🙋 Nhờ thầy/cô: {noi_dung_sach}" if noi_dung_sach else "🙋 Em cần thầy/cô giúp đỡ ở bước này."
    db.add(Turn(session_id=session_id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung=chat_nd))
    db.commit()
    db.refresh(yc)

    if ly_do_khong_an_toan:
        from app.models.flag import Flag, LoaiCo

        tien_to = "🆘 KHẨN CẤP" if khan_cap else "Không phù hợp"
        db.add(Flag(
            session_id=session_id,
            loai_co=LoaiCo.noi_dung_khong_phu_hop,
            ghi_chu=f"Trong yêu cầu 'Nhờ thầy/cô' ({tien_to}): {ly_do_khong_an_toan} — nội "
                    f"dung: “{(noi_dung_sach or '')[:200]}”",
        ))
        db.commit()

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
            # Nâng mức khẩn cấp nếu nội dung bị lớp lọc an toàn phát hiện — GV nhận ra
            # ngay từ tiêu đề thông báo, không cần mở ra mới biết cần chú ý đặc biệt.
            # 🆘 (khủng hoảng/tự hại) > ⚠️ (nội dung không phù hợp thường) > bình thường.
            tieu_de=(
                "🆘 Học sinh cần quan tâm khẩn cấp" if khan_cap
                else "⚠️ Học sinh nhờ trợ giúp — nội dung cần chú ý" if ly_do_khong_an_toan
                else "Học sinh nhờ trợ giúp"
            ),
            # Trỏ thẳng vào ĐÚNG yêu cầu (không phải session) — 1 session có thể có nhiều
            # yêu cầu "Nhờ thầy/cô" (HS hỏi nhiều lần), trỏ theo yc.id mới chính xác tuyệt
            # đối GV bấm vào thông báo nào sẽ mở đúng câu đó ở "Hỗ trợ học sinh".
            lien_ket_loai="yeu_cau_tro_giup",
            lien_ket_id=yc.id,
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
        **_noi_dung_cau_hoi(db, yc.problem_id),
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


def xoa_yeu_cau(db: Session, gv_id: int, yc_id: int) -> None:
    yc = db.get(YeuCauTroGiup, yc_id)
    if yc is None:
        raise ValueError("Yêu cầu không tồn tại")
    if _gv_cua_hs(db, yc.hoc_sinh_id) != gv_id:
        raise ValueError("Không có quyền với yêu cầu này")
    db.delete(yc)
    db.commit()
