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

LOAI_HOP_LE = {"tuan", "chu_de", "nhieu"}
LOAI_CAU_HOP_LE = {"TN4PA", "TNDS", "TLN"}
DO_KHO_HOP_LE = {"de", "tb", "kho"}


def _naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def _ds_hoan_thanh(db: Session, hs_id: int) -> list[dict]:
    """Các phiên HOÀN THÀNH (không bị ẩn) kèm thuộc tính bài để lọc mục tiêu:
    [{pid, dang_id, loai_cau, do_kho, chuyen_de, luc}]."""
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
        out.append({
            "pid": s.problem_id,
            "dang_id": p.dang_id if p else None,
            "loai_cau": p.loai_cau.value if p else None,
            "do_kho": p.do_kho.value if p else None,
            "chuyen_de": p.chuyen_de if p else None,
            "luc": _naive(s.cap_nhat_luc),
        })
    return out


def _khop_muc(muc: dict, c: dict) -> bool:
    """1 phiên hoàn thành c có khớp bộ lọc của 1 DÒNG con (muc) không — AND các tiêu chí đã đặt."""
    if muc.get("dang_id"):
        if c["dang_id"] != muc["dang_id"]:
            return False
    elif muc.get("chuyen_de"):  # chỉ lọc chuyên đề khi KHÔNG chọn dạng (dạng đã bao hàm)
        if c["chuyen_de"] != muc["chuyen_de"]:
            return False
    if muc.get("loai_cau") and c["loai_cau"] != muc["loai_cau"]:
        return False
    if muc.get("do_kho") and c["do_kho"] != muc["do_kho"]:
        return False
    return True


def _prog_muc(muc: dict, comp: list[dict], moc: datetime | None) -> int:
    """Số bài (distinct) hoàn thành TỪ moc thỏa dòng con muc."""
    return len({c["pid"] for c in comp
                if (moc is None or (c["luc"] and c["luc"] >= moc)) and _khop_muc(muc, c)})


def _tien_do(mt: MucTieu, comp: list[dict]) -> int:
    moc = _naive(mt.moc_bat_dau)
    if mt.loai == "tuan":
        den = (moc + timedelta(days=7)) if moc else None
        return len({c["pid"] for c in comp
                    if c["luc"] and moc and den and moc <= c["luc"] < den})
    if mt.loai == "chu_de":
        return len({c["pid"] for c in comp
                    if c["dang_id"] == mt.dang_id and (moc is None or (c["luc"] and c["luc"] >= moc))})
    # nhieu: tổng tiến độ mọi dòng con (mỗi dòng cộng tối đa bằng chỉ tiêu của nó, nên
    # tong >= chi_tieu_so (=∑ chỉ tiêu) ⇔ MỌI dòng đạt).
    return sum(min(_prog_muc(m, comp, moc), m["chi_tieu_so"]) for m in (mt.muc_con or []))


def _dict(mt: MucTieu, hien_tai: int, dang_ten: str | None, nguoi_tao_ten: str | None,
          muc: list[dict] | None = None) -> dict:
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
        # loai='nhieu': chi tiết từng dòng con kèm tiến độ riêng.
        "muc": muc,
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
    # Gom mọi dang_id (cả mục tiêu chu_de lẫn các dòng con của mục tiêu nhiều) để lấy tên.
    dang_ids = {g.dang_id for g in goals if g.dang_id}
    for g in goals:
        for m in (g.muc_con or []):
            if m.get("dang_id"):
                dang_ids.add(m["dang_id"])
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
        muc = None
        if g.loai == "nhieu":
            moc = _naive(g.moc_bat_dau)
            muc = []
            for m in (g.muc_con or []):
                prog = _prog_muc(m, comp, moc)
                muc.append({
                    **m,
                    "dang_ten": dang_ten.get(m.get("dang_id")),
                    "hien_tai": min(prog, m["chi_tieu_so"]),
                    "da_dat": prog >= m["chi_tieu_so"],
                })
        out.append(_dict(
            g, _tien_do(g, comp), dang_ten.get(g.dang_id), nguoi_ten.get(g.nguoi_tao_id), muc
        ))
    # Chưa đạt lên trước, mới-trước trong nhóm.
    out.sort(key=lambda x: x["da_dat"])
    return out


def _chuan_hoa_muc(db: Session, muc: list[dict]) -> list[dict]:
    """Kiểm tra + chuẩn hóa các dòng con của mục tiêu 'nhiều'. Mỗi dòng cần chi_tieu_so ≥ 1;
    dang_id (nếu có) phải tồn tại → điền luôn chuyen_de từ dạng; loai_cau/do_kho hợp lệ."""
    if not muc:
        raise ValueError("Cần ít nhất một dòng mục tiêu")
    ra: list[dict] = []
    for m in muc:
        ct = m.get("chi_tieu_so")
        if not ct or ct < 1:
            raise ValueError("Mỗi dòng mục tiêu cần số lượng từ 1 trở lên")
        lc, dk, did = m.get("loai_cau"), m.get("do_kho"), m.get("dang_id")
        if lc and lc not in LOAI_CAU_HOP_LE:
            raise ValueError("Loại câu không hợp lệ")
        if dk and dk not in DO_KHO_HOP_LE:
            raise ValueError("Mức độ không hợp lệ")
        cd = m.get("chuyen_de")
        if did:
            d = db.get(Dang, did)
            if d is None:
                raise ValueError("Dạng không tồn tại")
            cd = d.chuyen_de.ten
        ra.append({"dang_id": did, "chuyen_de": cd, "loai_cau": lc or None,
                   "do_kho": dk or None, "chi_tieu_so": int(ct)})
    return ra


def tao(
    db: Session,
    hoc_sinh_id: int,
    nguoi_tao_id: int,
    nguon: str,
    loai: str,
    tieu_de: str | None,
    chi_tieu_so: int | None = None,
    dang_id: int | None = None,
    chuyen_de: str | None = None,
    han: datetime | None = None,
    muc: list[dict] | None = None,
    bao_hs: bool = False,
) -> dict:
    if loai not in LOAI_HOP_LE:
        raise ValueError("Loại mục tiêu không hợp lệ")

    tieu_de = (tieu_de or "").strip()

    if loai == "nhieu":
        muc_con = _chuan_hoa_muc(db, muc or [])
        tong = sum(x["chi_tieu_so"] for x in muc_con)
        if not tieu_de:
            tieu_de = f"Kế hoạch luyện {len(muc_con)} nhóm ({tong} bài)"
        mt = MucTieu(
            hoc_sinh_id=hoc_sinh_id, nguoi_tao_id=nguoi_tao_id, nguon=nguon, loai="nhieu",
            tieu_de=tieu_de, chi_tieu_so=tong, muc_con=muc_con, han=han,
        )
    else:
        if chi_tieu_so is None or chi_tieu_so < 1:
            raise ValueError("Chỉ tiêu phải từ 1 trở lên")
        dang = None
        if loai == "chu_de":
            if not dang_id:
                raise ValueError("Mục tiêu theo chủ đề cần chọn một dạng")
            dang = db.get(Dang, dang_id)
            if dang is None:
                raise ValueError("Dạng không tồn tại")
        else:  # tuan
            dang_id = None
        if not tieu_de:
            tieu_de = (f"Hoàn thành {chi_tieu_so} bài dạng «{dang.ten}»" if dang
                       else f"Hoàn thành {chi_tieu_so} bài trong tuần này")
        mt = MucTieu(
            hoc_sinh_id=hoc_sinh_id, nguoi_tao_id=nguoi_tao_id, nguon=nguon, loai=loai,
            tieu_de=tieu_de, dang_id=dang_id if loai == "chu_de" else None,
            chuyen_de=(dang.chuyen_de.ten if dang else (chuyen_de or None)),
            chi_tieu_so=chi_tieu_so, han=han,
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
