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
        .filter(SessionModel.hoc_sinh_id == hoc_sinh_id, Problem.chuyen_de == chuyen_de)
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


def tien_do_lop(db: Session, gv_id: int) -> list[dict]:
    """Tiến độ HS thuộc lớp do GV này phụ trách."""
    from app.models.lop import Lop

    lop_ids = [lop.id for lop in db.query(Lop).filter(Lop.gv_id == gv_id).all()]
    if not lop_ids:
        return []
    hoc_sinhs = db.query(User).filter(User.lop_id.in_(lop_ids)).all()

    ket_qua = []
    for hs in hoc_sinhs:
        ket_qua.append({
            "hoc_sinh_id": hs.id,
            "ho_ten": hs.ho_ten,
            "tien_do": tien_do_cua_hs(db, hs.id),
        })
    return ket_qua
