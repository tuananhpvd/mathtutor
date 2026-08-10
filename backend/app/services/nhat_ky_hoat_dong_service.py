"""
Nhật ký hoạt động Ban giám khảo (Admin, hướng A — tái dựng từ dữ liệu sẵn có, KHÔNG thêm
bảng audit mới). Vì các model hiện có KHÔNG lưu "ai sửa/duyệt/xóa lúc nào", nhật ký này chỉ
gom được các hành động có để lại dấu vết thời gian + người thực hiện trong CSDL — không phải
audit log đầy đủ. Xem docs/PROGRESS.md để biết giới hạn cụ thể.

Phạm vi: CHỈ Lớp Demo (tên "Lớp Demo") — GV chủ nhiệm + học sinh trong lớp đó. Không đụng tới
dữ liệu GV/HS thật.

Module này CHỈ ĐỌC — không có hàm ghi nào. An toàn tuyệt đối với dữ liệu hiện có.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.danh_muc import ChuyenDe, Dang
from app.models.de_thi import DeThi
from app.models.flag import Flag
from app.models.lop import Lop
from app.models.nhiem_vu import NhiemVu
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.turn import Turn, VaiTroTurn
from app.models.user import User, VaiTro
from app.models.yeu_cau_tro_giup import YeuCauTroGiup

TEN_LOP_GIAM_KHAO = "Lớp Demo"


def _nguoi(users_theo_id: dict[int, User], user_id: int | None) -> dict:
    u = users_theo_id.get(user_id) if user_id is not None else None
    if u is None:
        return {"dang_nhap": None, "ho_ten": "?", "vai_tro": None}
    return {"dang_nhap": u.dang_nhap, "ho_ten": u.ho_ten, "vai_tro": u.vai_tro.value}


def _pham_vi_lop(db: Session) -> tuple[Lop | None, dict[int, User]]:
    """Trả (lớp, {user_id: User}) gồm GV chủ nhiệm + toàn bộ HS trong Lớp Demo."""
    lop = db.query(Lop).filter(Lop.ten == TEN_LOP_GIAM_KHAO).first()
    if lop is None:
        return None, {}
    users = db.query(User).filter(
        (User.lop_id == lop.id) | (User.id == lop.gv_id)
    ).all()
    return lop, {u.id: u for u in users}


def lay_nhat_ky_hoat_dong(
    db: Session,
    tu_ngay: datetime | None = None,
    den_ngay: datetime | None = None,
    chi_tiet: bool = False,
    trang: int = 1,
    moi_trang: int = 100,
) -> dict:
    """Gom sự kiện từ nhiều bảng thành một dòng thời gian, mới nhất trước.

    chi_tiet=False (mặc định): chỉ hoạt động "cấp cao" (đăng ký, bắt đầu/hoàn thành bài, tạo
    câu hỏi/chuyên đề/dạng, giao nhiệm vụ, nhờ trợ giúp, đề thi, cờ tự phát sinh) — đủ để nắm
    bức tranh tổng, không rợp bởi hàng trăm lượt hội thoại từng câu.
    chi_tiet=True: thêm cả từng lượt hội thoại (turns) — dùng khi cần soi chi tiết 1 khoảng
    thời gian ngắn.
    """
    lop, users_theo_id = _pham_vi_lop(db)
    if lop is None:
        return {"rows": [], "tong": 0, "lop_tim_thay": False}

    hs_ids = [uid for uid, u in users_theo_id.items() if u.vai_tro == VaiTro.hs]
    gv_ids = [uid for uid, u in users_theo_id.items() if u.vai_tro == VaiTro.gv]
    tat_ca_ids = list(users_theo_id.keys())

    su_kien: list[dict] = []

    # ── Tạo tài khoản (tự đăng ký bằng mã lớp HOẶC do admin tạo) ──
    for u in users_theo_id.values():
        if u.tao_luc is None:
            continue
        su_kien.append({
            "thoi_diem": u.tao_luc, "dang_nhap": u.dang_nhap, "ho_ten": u.ho_ten,
            "vai_tro": u.vai_tro.value, "hanh_dong": "Tạo tài khoản",
            "chi_tiet": f"Vào lớp {lop.ten}",
        })

    # ── Phiên học: bắt đầu + hoàn thành ──
    if hs_ids:
        sessions = (
            db.query(SessionModel)
            .filter(SessionModel.hoc_sinh_id.in_(hs_ids))
            .all()
        )
        problem_ids = {s.problem_id for s in sessions}
        problems_theo_id = {
            p.id: p for p in db.query(Problem).filter(Problem.id.in_(problem_ids)).all()
        } if problem_ids else {}
        for s in sessions:
            de_bai = (problems_theo_id.get(s.problem_id).de_bai[:60]
                      if problems_theo_id.get(s.problem_id) else f"#{s.problem_id}")
            nguoi = _nguoi(users_theo_id, s.hoc_sinh_id)
            su_kien.append({
                "thoi_diem": s.bat_dau_luc, **nguoi,
                "hanh_dong": "Bắt đầu làm bài", "chi_tiet": de_bai,
            })
            if s.trang_thai == TrangThaiSession.hoan_thanh:
                diem = f", điểm {s.diem:.2f}" if s.diem is not None else ""
                su_kien.append({
                    "thoi_diem": s.cap_nhat_luc, **nguoi,
                    "hanh_dong": "Hoàn thành bài", "chi_tiet": f"{de_bai}{diem}",
                })

        # ── Từng lượt hội thoại (chỉ khi chi_tiet=True) ──
        if chi_tiet and sessions:
            session_ids = [s.id for s in sessions]
            hoc_sinh_theo_session = {s.id: s.hoc_sinh_id for s in sessions}
            turns = db.query(Turn).filter(Turn.session_id.in_(session_ids)).all()
            for t in turns:
                if t.vai_tro == VaiTroTurn.hoc_sinh:
                    nguoi = _nguoi(users_theo_id, hoc_sinh_theo_session.get(t.session_id))
                    hanh_dong = "Học sinh trả lời"
                else:
                    nguoi = {"dang_nhap": None, "ho_ten": "Gia sư AI", "vai_tro": None}
                    hanh_dong = "Gia sư phản hồi"
                su_kien.append({
                    "thoi_diem": t.thoi_diem, **nguoi, "hanh_dong": hanh_dong,
                    "chi_tiet": (t.noi_dung or "")[:80],
                })

    # ── Cờ cảnh báo tự phát sinh (gắn theo phiên → suy ra học sinh) ──
    if hs_ids:
        session_id_to_hs = dict(
            db.query(SessionModel.id, SessionModel.hoc_sinh_id)
            .filter(SessionModel.hoc_sinh_id.in_(hs_ids)).all()
        )
        if session_id_to_hs:
            flags = db.query(Flag).filter(Flag.session_id.in_(session_id_to_hs.keys())).all()
            for f in flags:
                nguoi = _nguoi(users_theo_id, session_id_to_hs.get(f.session_id))
                su_kien.append({
                    "thoi_diem": f.tao_luc, **nguoi,
                    "hanh_dong": "Hệ thống tự gắn cờ", "chi_tiet": f.loai_co.value,
                })

    # ── Nội dung GV tạo: câu hỏi, chuyên đề, dạng, nhiệm vụ, đề thi ──
    if gv_ids:
        for p in db.query(Problem).filter(Problem.nguoi_tao_id.in_(gv_ids)).all():
            if p.tao_luc is None:
                continue
            nguoi = _nguoi(users_theo_id, p.nguoi_tao_id)
            su_kien.append({
                "thoi_diem": p.tao_luc, **nguoi,
                "hanh_dong": "Tạo câu hỏi", "chi_tiet": p.de_bai[:60],
            })
        for cd in db.query(ChuyenDe).filter(ChuyenDe.nguoi_tao_id.in_(gv_ids)).all():
            nguoi = _nguoi(users_theo_id, cd.nguoi_tao_id)
            su_kien.append({
                "thoi_diem": cd.tao_luc, **nguoi,
                "hanh_dong": "Tạo chuyên đề", "chi_tiet": cd.ten,
            })
        for d in db.query(Dang).filter(Dang.nguoi_tao_id.in_(gv_ids)).all():
            nguoi = _nguoi(users_theo_id, d.nguoi_tao_id)
            su_kien.append({
                "thoi_diem": d.tao_luc, **nguoi,
                "hanh_dong": "Tạo dạng", "chi_tiet": d.ten,
            })
        for nv in db.query(NhiemVu).filter(NhiemVu.gv_id.in_(gv_ids)).all():
            nguoi = _nguoi(users_theo_id, nv.gv_id)
            su_kien.append({
                "thoi_diem": nv.tao_luc, **nguoi,
                "hanh_dong": "Giao nhiệm vụ", "chi_tiet": nv.tieu_de,
            })
        for dt in db.query(DeThi).filter(DeThi.nguoi_tao_id.in_(gv_ids)).all():
            nguoi = _nguoi(users_theo_id, dt.nguoi_tao_id)
            su_kien.append({
                "thoi_diem": dt.tao_luc, **nguoi,
                "hanh_dong": "Tạo đề thi", "chi_tiet": dt.ten,
            })
            if dt.phat_hanh_luc is not None:
                su_kien.append({
                    "thoi_diem": dt.phat_hanh_luc, **nguoi,
                    "hanh_dong": "Phát hành đề thi", "chi_tiet": dt.ten,
                })
            if dt.thu_hoi_luc is not None:
                su_kien.append({
                    "thoi_diem": dt.thu_hoi_luc, **nguoi,
                    "hanh_dong": "Thu hồi đề thi", "chi_tiet": dt.ten,
                })

    # ── Nhờ trợ giúp / GV trả lời ──
    if tat_ca_ids:
        for y in db.query(YeuCauTroGiup).filter(YeuCauTroGiup.hoc_sinh_id.in_(hs_ids)).all() if hs_ids else []:
            nguoi_hs = _nguoi(users_theo_id, y.hoc_sinh_id)
            su_kien.append({
                "thoi_diem": y.tao_luc, **nguoi_hs,
                "hanh_dong": "Nhờ thầy/cô trợ giúp", "chi_tiet": (y.noi_dung or "")[:60],
            })
            if y.tra_loi_luc is not None:
                nguoi_gv = _nguoi(users_theo_id, y.gv_id)
                su_kien.append({
                    "thoi_diem": y.tra_loi_luc, **nguoi_gv,
                    "hanh_dong": "Trả lời trợ giúp", "chi_tiet": (y.tra_loi or "")[:60],
                })

    # ── Lọc theo khoảng ngày (nếu có) rồi sắp mới nhất trước ──
    if tu_ngay is not None:
        su_kien = [s for s in su_kien if s["thoi_diem"] is not None and s["thoi_diem"] >= tu_ngay]
    if den_ngay is not None:
        su_kien = [s for s in su_kien if s["thoi_diem"] is not None and s["thoi_diem"] <= den_ngay]
    su_kien.sort(key=lambda s: s["thoi_diem"], reverse=True)

    tong = len(su_kien)
    moi_trang = max(1, min(moi_trang, 500))
    trang = max(1, trang)
    trang_hien = su_kien[(trang - 1) * moi_trang: trang * moi_trang]

    return {
        "rows": [
            {**s, "thoi_diem": s["thoi_diem"].isoformat() if s["thoi_diem"] else None}
            for s in trang_hien
        ],
        "tong": tong,
        "lop_tim_thay": True,
        "lop_ten": lop.ten,
    }
