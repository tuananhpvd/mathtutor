"""Dịch vụ mục tiêu học tập (B1).

HS tự đặt / GV đặt cho HS / hệ thống gợi ý theo điểm yếu. Mục tiêu theo tuần hoặc
theo chủ đề (dạng). Tiến độ tính động từ phiên hoàn thành. Không phụ thuộc LLM/web.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.danh_muc import Dang
from app.models.muc_tieu import MucTieu
from app.models.problem import Problem
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.thong_bao import LoaiThongBao
from app.models.user import User
from app.services import thong_bao_service
from app.services.gv_service import _so_huu_hs

LOAI_HOP_LE = {"tuan", "chu_de"}


def _naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def _ds_hoan_thanh(db: Session, hs_id: int) -> list[tuple[int, int | None, datetime | None]]:
    """[(problem_id, dang_id, cap_nhat_luc_naive)] các phiên HOÀN THÀNH (không bị ẩn)."""
    sessions = (
        db.query(SessionModel)
        .filter(
            SessionModel.hoc_sinh_id == hs_id,
            SessionModel.trang_thai == TrangThaiSession.hoan_thanh,
            SessionModel.bi_an == False,  # noqa: E712
        )
        .all()
    )
    pids = {s.problem_id for s in sessions}
    problems = (
        {p.id: p for p in db.query(Problem).filter(Problem.id.in_(pids)).all()} if pids else {}
    )
    out = []
    for s in sessions:
        p = problems.get(s.problem_id)
        out.append((s.problem_id, p.dang_id if p else None, _naive(s.cap_nhat_luc)))
    return out


def _tien_do(mt: MucTieu, comp: list[tuple[int, int | None, datetime | None]]) -> int:
    moc = _naive(mt.moc_bat_dau)
    if mt.loai == "tuan":
        den = (moc + timedelta(days=7)) if moc else None
        pids = {
            pid for (pid, _d, luc) in comp
            if luc and moc and den and moc <= luc < den
        }
        return len(pids)
    # chu_de
    pids = {
        pid for (pid, d, luc) in comp
        if d == mt.dang_id and (moc is None or (luc and luc >= moc))
    }
    return len(pids)


def _dict(mt: MucTieu, hien_tai: int, dang_ten: str | None, nguoi_tao_ten: str | None) -> dict:
    return {
        "id": mt.id,
        "loai": mt.loai,
        "nguon": mt.nguon,
        "tieu_de": mt.tieu_de,
        "dang_id": mt.dang_id,
        "dang_ten": dang_ten,
        "chuyen_de": mt.chuyen_de,
        "chi_tieu_so": mt.chi_tieu_so,
        "hien_tai": min(hien_tai, mt.chi_tieu_so),
        "da_dat": hien_tai >= mt.chi_tieu_so,
        "han": mt.han.isoformat() if mt.han else None,
        "nguoi_tao_ten": nguoi_tao_ten,
        "tao_luc": mt.tao_luc.isoformat() if mt.tao_luc else None,
    }


def danh_sach(db: Session, hs_id: int) -> list[dict]:
    goals = (
        db.query(MucTieu)
        .filter(MucTieu.hoc_sinh_id == hs_id, MucTieu.da_huy == False)  # noqa: E712
        .order_by(MucTieu.tao_luc.desc(), MucTieu.id.desc())
        .all()
    )
    if not goals:
        return []
    comp = _ds_hoan_thanh(db, hs_id)
    dang_ids = {g.dang_id for g in goals if g.dang_id}
    dang_ten = (
        {d.id: d.ten for d in db.query(Dang).filter(Dang.id.in_(dang_ids)).all()}
        if dang_ids else {}
    )
    nguoi_ids = {g.nguoi_tao_id for g in goals if g.nguoi_tao_id}
    nguoi_ten = (
        {u.id: u.ho_ten for u in db.query(User).filter(User.id.in_(nguoi_ids)).all()}
        if nguoi_ids else {}
    )
    out = []
    for g in goals:
        out.append(_dict(
            g, _tien_do(g, comp), dang_ten.get(g.dang_id), nguoi_ten.get(g.nguoi_tao_id)
        ))
    # Chưa đạt lên trước, mới-trước trong nhóm.
    out.sort(key=lambda x: x["da_dat"])
    return out


def tao(
    db: Session,
    hoc_sinh_id: int,
    nguoi_tao_id: int,
    nguon: str,
    loai: str,
    tieu_de: str | None,
    chi_tieu_so: int,
    dang_id: int | None = None,
    chuyen_de: str | None = None,
    han: datetime | None = None,
    bao_hs: bool = False,
) -> dict:
    if loai not in LOAI_HOP_LE:
        raise ValueError("Loại mục tiêu không hợp lệ")
    if chi_tieu_so is None or chi_tieu_so < 1:
        raise ValueError("Chỉ tiêu phải từ 1 trở lên")

    dang = None
    if loai == "chu_de":
        if not dang_id:
            raise ValueError("Mục tiêu theo chủ đề cần chọn một dạng")
        dang = db.get(Dang, dang_id)
        if dang is None:
            raise ValueError("Dạng không tồn tại")

    tieu_de = (tieu_de or "").strip()
    if not tieu_de:
        if loai == "tuan":
            tieu_de = f"Hoàn thành {chi_tieu_so} bài trong tuần này"
        else:
            tieu_de = f"Hoàn thành {chi_tieu_so} bài dạng «{dang.ten}»"

    mt = MucTieu(
        hoc_sinh_id=hoc_sinh_id,
        nguoi_tao_id=nguoi_tao_id,
        nguon=nguon,
        loai=loai,
        tieu_de=tieu_de,
        dang_id=dang_id if loai == "chu_de" else None,
        chuyen_de=(dang.chuyen_de.ten if dang else (chuyen_de or None)),
        chi_tieu_so=chi_tieu_so,
        han=han,
    )
    db.add(mt)
    db.commit()
    db.refresh(mt)

    if bao_hs:
        thong_bao_service.tao(
            db, nguoi_nhan_id=hoc_sinh_id,
            noi_dung=f"Thầy/cô đặt mục tiêu cho em: «{tieu_de}».",
            loai=LoaiThongBao.nhiem_vu, nguoi_gui_id=nguoi_tao_id,
            tieu_de="Mục tiêu mới",
        )
    return {"id": mt.id}


def de_xuat(db: Session, hoc_sinh_id: int) -> list[dict]:
    """Gợi ý mục tiêu (chưa lưu) từ điểm yếu + một mục tiêu tuần mặc định."""
    from app.services.phan_tich_service import ho_so_nang_luc

    ho_so = ho_so_nang_luc(db, hoc_sinh_id)
    goi_y: list[dict] = []
    for r in (ho_so.get("diem_yeu") or [])[:3]:
        if not r.get("dang_id"):
            continue
        ten_dang = r["ten"].split("›")[-1].strip()
        goi_y.append({
            "loai": "chu_de",
            "tieu_de": f"Hoàn thành 3 bài dạng «{ten_dang}» để cải thiện",
            "chi_tieu_so": 3,
            "dang_id": r["dang_id"],
            "chuyen_de": r.get("chuyen_de"),
        })
    goi_y.append({
        "loai": "tuan", "tieu_de": "Hoàn thành 5 bài trong tuần này",
        "chi_tieu_so": 5, "dang_id": None, "chuyen_de": None,
    })
    return goi_y


def xoa(db: Session, user, mt_id: int) -> None:
    """HS xóa mục tiêu của mình; GV xóa mục tiêu của HS thuộc lớp mình."""
    from app.models.user import VaiTro

    mt = db.get(MucTieu, mt_id)
    if mt is None:
        raise ValueError("Mục tiêu không tồn tại")
    duoc = (
        (user.vai_tro == VaiTro.hs and mt.hoc_sinh_id == user.id)
        or (user.vai_tro == VaiTro.gv and _so_huu_hs(db, user.id, mt.hoc_sinh_id))
    )
    if not duoc:
        raise ValueError("Không có quyền với mục tiêu này")
    db.delete(mt)
    db.commit()
