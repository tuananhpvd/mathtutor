"""Service: GV đặt lại tiến độ HS (trực tiếp, không cần admin duyệt)."""

from sqlalchemy.orm import Session

from app.models.phan_tich import PhanTich
from app.models.session import Session as SessionModel
from app.models.user import User, VaiTro
from app.services.progress_service import cap_nhat_tien_do


def _kiem_tra_gv_so_huu(db: Session, gv_id: int, hs_id: int) -> None:
    from app.models.lop import Lop

    hs = db.get(User, hs_id)
    if hs is None or hs.vai_tro != VaiTro.hs:
        raise ValueError("Không tìm thấy học sinh")
    if hs.lop_id is None:
        raise ValueError("Học sinh chưa thuộc lớp nào")
    lop = db.get(Lop, hs.lop_id)
    if lop is None or lop.gv_id != gv_id:
        raise ValueError("Không có quyền với học sinh này")


def dat_lai_tien_do(db: Session, hs_id: int, gv_id: int) -> dict:
    _kiem_tra_gv_so_huu(db, gv_id, hs_id)

    sessions = db.query(SessionModel).filter(
        SessionModel.hoc_sinh_id == hs_id,
        SessionModel.bi_an == False,  # noqa: E712
    ).all()

    so_phien = len(sessions)
    chuyen_de_lien_quan: set[str] = set()

    for s in sessions:
        s.bi_an = True
        from app.models.problem import Problem
        p = db.get(Problem, s.problem_id)
        if p:
            chuyen_de_lien_quan.add(p.chuyen_de)

    db.flush()

    for cd in chuyen_de_lien_quan:
        cap_nhat_tien_do(db, hs_id, cd)

    db.query(PhanTich).filter(PhanTich.hoc_sinh_id == hs_id).delete(synchronize_session=False)

    db.commit()
    return {"so_phien_da_an": so_phien}
