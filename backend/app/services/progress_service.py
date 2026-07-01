"""
Progress: cập nhật khi xong bài + truy vấn tiến độ HS/lớp.
Tính lại từ các session để idempotent (không cộng dồn trùng).
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.progress import Progress
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import User


def cap_nhat_tien_do(db: Session, hoc_sinh_id: int, chuyen_de: str) -> Progress:
    """Tính lại progress của (HS, chuyên đề) từ toàn bộ session liên quan."""
    rows = (
        db.query(SessionModel)
        .join(Problem, Problem.id == SessionModel.problem_id)
        .filter(
            SessionModel.hoc_sinh_id == hoc_sinh_id,
            SessionModel.bi_an == False,  # noqa: E712
            Problem.chuyen_de == chuyen_de,
        )
        .all()
    )
    so_bai_lam = len(rows)
    hoan_thanh = [s for s in rows if s.trang_thai == TrangThaiSession.hoan_thanh]
    so_bai_hoan_thanh = len(hoan_thanh)
    diem_list = [s.diem for s in hoan_thanh if s.diem is not None]
    ty_le = round(sum(diem_list) / len(diem_list), 4) if diem_list else 0.0
    tong_thoi_gian = sum(s.thoi_gian_giay or 0 for s in hoan_thanh)

    prog = (
        db.query(Progress)
        .filter(Progress.hoc_sinh_id == hoc_sinh_id, Progress.chuyen_de == chuyen_de)
        .first()
    )
    if prog is None:
        prog = Progress(hoc_sinh_id=hoc_sinh_id, chuyen_de=chuyen_de)
        db.add(prog)
    prog.so_bai_lam = so_bai_lam
    prog.so_bai_hoan_thanh = so_bai_hoan_thanh
    prog.ty_le_dung_trung_binh = ty_le
    prog.tong_thoi_gian_giay = tong_thoi_gian
    prog.cap_nhat_luc = datetime.now(timezone.utc)
    db.flush()
    return prog


def tien_do_cua_hs(db: Session, hoc_sinh_id: int) -> list[dict]:
    rows = db.query(Progress).filter(Progress.hoc_sinh_id == hoc_sinh_id).all()
    return [
        {
            "chuyen_de": p.chuyen_de,
            "so_bai_lam": p.so_bai_lam,
            "so_bai_hoan_thanh": p.so_bai_hoan_thanh,
            "ty_le_dung_trung_binh": p.ty_le_dung_trung_binh,
            "tong_thoi_gian_giay": p.tong_thoi_gian_giay,
        }
        for p in rows
    ]


_NHAN_KHO = {"de": "Dễ", "tb": "Trung bình", "kho": "Khó"}


def _khoi() -> dict:
    return {"tong": 0, "hoan_thanh": 0, "dang_lam": 0, "chua_lam": 0}


def hoc_sinh_thuoc_gv(db: Session, gv_id: int, hoc_sinh_id: int) -> bool:
    """True nếu học sinh thuộc một lớp do GV này phụ trách."""
    from app.models.lop import Lop

    hs = db.get(User, hoc_sinh_id)
    if hs is None or hs.lop_id is None:
        return False
    lop_ids = {lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()}
    return hs.lop_id in lop_ids


def thong_ke_chi_tiet(db: Session, hoc_sinh_id: int) -> dict:
    """Thống kê tiến độ chi tiết của HS trên toàn bộ bài đã duyệt.

    Trạng thái mỗi bài: hoan_thanh (có ≥1 phiên hoàn thành) > dang_lam (có phiên dở) > chua_lam.
    Gồm: tổng quan, theo thời gian (nhanh/chậm nhất mỗi mức độ), theo mức độ, theo chuyên đề→dạng.
    """
    from app.models.problem import TrangThaiDuyet

    problems = (
        db.query(Problem)
        .filter(Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet, Problem.bi_an == False)  # noqa: E712
        .all()
    )
    sessions = (
        db.query(SessionModel)
        .filter(SessionModel.hoc_sinh_id == hoc_sinh_id, SessionModel.bi_an == False)  # noqa: E712
        .all()
    )

    sess_by_pid: dict[int, list] = {}
    for s in sessions:
        sess_by_pid.setdefault(s.problem_id, []).append(s)

    tong_thoi_gian = sum(
        s.thoi_gian_giay or 0 for s in sessions
        if s.trang_thai == TrangThaiSession.hoan_thanh
    )

    def trang_thai_bai(pid: int) -> str:
        # Theo phiên MỚI NHẤT (khớp logic trang chọn bài), tránh lệch số liệu.
        ss = sess_by_pid.get(pid, [])
        if not ss:
            return "chua_lam"
        moi_nhat = max(ss, key=lambda s: s.cap_nhat_luc)
        if moi_nhat.trang_thai == TrangThaiSession.hoan_thanh:
            return "hoan_thanh"
        if moi_nhat.trang_thai == TrangThaiSession.dang_lam:
            return "dang_lam"
        return "chua_lam"

    def best_time(pid: int):
        ts = [s.thoi_gian_giay for s in sess_by_pid.get(pid, [])
              if s.trang_thai == TrangThaiSession.hoan_thanh and s.thoi_gian_giay is not None]
        return min(ts) if ts else None

    tong_quan = _khoi()
    theo_kho = {k: {"do_kho": k, "ten": _NHAN_KHO[k], **_khoi()} for k in ("de", "tb", "kho")}
    nhanh = {"de": None, "tb": None, "kho": None}
    cham = {"de": None, "tb": None, "kho": None}
    theo_dang_map: dict[str, dict] = {}
    cd_order: list[str] = []

    for p in problems:
        st = trang_thai_bai(p.id)
        dk = p.do_kho.value if hasattr(p.do_kho, "value") else p.do_kho

        tong_quan["tong"] += 1
        tong_quan[st] += 1
        if dk in theo_kho:
            theo_kho[dk]["tong"] += 1
            theo_kho[dk][st] += 1

        if st == "hoan_thanh" and dk in nhanh:
            bt = best_time(p.id)
            if bt is not None:
                nhanh[dk] = bt if nhanh[dk] is None else min(nhanh[dk], bt)
                cham[dk] = bt if cham[dk] is None else max(cham[dk], bt)

        cd = p.chuyen_de or "(Chưa phân loại)"
        dang_ten = p.dang.ten if p.dang else "(Chưa phân dạng)"
        if cd not in theo_dang_map:
            theo_dang_map[cd] = {}
            cd_order.append(cd)
        dmap = theo_dang_map[cd]
        if dang_ten not in dmap:
            dmap[dang_ten] = {"ten": dang_ten, **_khoi()}
        dmap[dang_ten]["tong"] += 1
        dmap[dang_ten][st] += 1

    theo_dang = [
        {"chuyen_de": cd, "dang": [dmap[d] for d in sorted(theo_dang_map[cd].keys())]}
        for cd in sorted(cd_order)
        for dmap in [theo_dang_map[cd]]
    ]

    # ── Nhiệm vụ hoàn thành ──────────────────────────────────────────────────
    from app.models.nhiem_vu import NhiemVuBai, NhiemVuHocSinh

    done_pids: set[int] = {
        pid for pid, ss in sess_by_pid.items()
        if any(s.trang_thai == TrangThaiSession.hoan_thanh for s in ss)
    }
    nv_hs_rows = (
        db.query(NhiemVuHocSinh)
        .filter(NhiemVuHocSinh.hoc_sinh_id == hoc_sinh_id)
        .all()
    )
    nv_ids = [x.nhiem_vu_id for x in nv_hs_rows]
    so_nhiem_vu = len(nv_ids)
    so_nhiem_vu_hoan_thanh = 0
    if nv_ids:
        bai_rows = db.query(NhiemVuBai).filter(NhiemVuBai.nhiem_vu_id.in_(nv_ids)).all()
        bai_by_nv: dict[int, list[int]] = {}
        for b in bai_rows:
            bai_by_nv.setdefault(b.nhiem_vu_id, []).append(b.problem_id)
        for nid in nv_ids:
            pids = bai_by_nv.get(nid, [])
            if pids and all(p in done_pids for p in pids):
                so_nhiem_vu_hoan_thanh += 1

    # ── Mục tiêu đạt ─────────────────────────────────────────────────────────
    from app.models.muc_tieu import MucTieu
    from app.services.muc_tieu_service import _ds_hoan_thanh, _tien_do

    muc_tieu_list = (
        db.query(MucTieu)
        .filter(MucTieu.hoc_sinh_id == hoc_sinh_id, MucTieu.da_huy == False)  # noqa: E712
        .all()
    )
    so_muc_tieu = len(muc_tieu_list)
    so_muc_tieu_dat = 0
    if muc_tieu_list:
        comp = _ds_hoan_thanh(db, hoc_sinh_id)
        so_muc_tieu_dat = sum(
            1 for mt in muc_tieu_list if _tien_do(mt, comp) >= mt.chi_tieu_so
        )

    return {
        "tong_quan": tong_quan,
        "thoi_gian": {
            "tong_thoi_gian_giay": tong_thoi_gian,
            "nhanh_nhat": nhanh,
            "cham_nhat": cham,
        },
        "theo_do_kho": [theo_kho["de"], theo_kho["tb"], theo_kho["kho"]],
        "theo_dang": theo_dang,
        "nhiem_vu": {"tong": so_nhiem_vu, "hoan_thanh": so_nhiem_vu_hoan_thanh},
        "muc_tieu": {"tong": so_muc_tieu, "dat": so_muc_tieu_dat},
    }


def tien_do_lop(db: Session, gv_id: int) -> list[dict]:
    """Tiến độ HS thuộc lớp do GV này phụ trách."""
    from app.models.lop import Lop

    lops = db.query(Lop).filter(Lop.gv_id == gv_id).all()
    lop_ten = {lop.id: lop.ten for lop in lops}
    lop_ids = list(lop_ten.keys())
    if not lop_ids:
        return []
    hoc_sinhs = db.query(User).filter(User.lop_id.in_(lop_ids)).all()

    ket_qua = []
    for hs in hoc_sinhs:
        ket_qua.append({
            "hoc_sinh_id": hs.id,
            "ho_ten": hs.ho_ten,
            "lop_id": hs.lop_id,
            "lop_ten": lop_ten.get(hs.lop_id),
            "tien_do": tien_do_cua_hs(db, hs.id),
        })
    return ket_qua
