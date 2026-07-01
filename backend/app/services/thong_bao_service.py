"""Dịch vụ thông báo (xương sống đồng hành GV↔HS).

Không phụ thuộc LLM/web. Mọi tính năng đồng hành (nhận xét, nhiệm vụ, trả lời,
báo cờ) tạo thông báo qua `tao()` và người nhận đọc qua `danh_sach()`.
"""

from sqlalchemy.orm import Session

from app.models.thong_bao import LoaiThongBao, ThongBao
from app.models.user import User

GIOI_HAN_MAC_DINH = 50


def tao(
    db: Session,
    nguoi_nhan_id: int,
    noi_dung: str,
    loai: LoaiThongBao = LoaiThongBao.he_thong,
    *,
    nguoi_gui_id: int | None = None,
    tieu_de: str | None = None,
    lien_ket_loai: str | None = None,
    lien_ket_id: int | None = None,
) -> ThongBao:
    tb = ThongBao(
        nguoi_nhan_id=nguoi_nhan_id,
        nguoi_gui_id=nguoi_gui_id,
        loai=loai,
        tieu_de=tieu_de,
        noi_dung=noi_dung,
        lien_ket_loai=lien_ket_loai,
        lien_ket_id=lien_ket_id,
    )
    db.add(tb)
    db.commit()
    db.refresh(tb)
    return tb


def _dict(tb: ThongBao, ten_nguoi_gui: str | None = None) -> dict:
    return {
        "id": tb.id,
        "loai": tb.loai.value,
        "tieu_de": tb.tieu_de,
        "noi_dung": tb.noi_dung,
        "da_doc": tb.da_doc,
        "nguoi_gui_id": tb.nguoi_gui_id,
        "nguoi_gui_ten": ten_nguoi_gui,
        "lien_ket_loai": tb.lien_ket_loai,
        "lien_ket_id": tb.lien_ket_id,
        "tao_luc": tb.tao_luc.isoformat() if tb.tao_luc else None,
    }


def danh_sach(
    db: Session, user_id: int, chi_chua_doc: bool = False, gioi_han: int = GIOI_HAN_MAC_DINH
) -> list[dict]:
    q = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == user_id)
    if chi_chua_doc:
        q = q.filter(ThongBao.da_doc == False)  # noqa: E712
    rows = q.order_by(ThongBao.tao_luc.desc(), ThongBao.id.desc()).limit(gioi_han).all()

    gui_ids = {r.nguoi_gui_id for r in rows if r.nguoi_gui_id}
    ten = (
        {u.id: u.ho_ten for u in db.query(User).filter(User.id.in_(gui_ids)).all()}
        if gui_ids else {}
    )
    return [_dict(r, ten.get(r.nguoi_gui_id)) for r in rows]


def dem_chua_doc(db: Session, user_id: int) -> int:
    return (
        db.query(ThongBao)
        .filter(ThongBao.nguoi_nhan_id == user_id, ThongBao.da_doc == False)  # noqa: E712
        .count()
    )


def danh_dau_da_doc(db: Session, user_id: int, tb_id: int) -> bool:
    tb = db.get(ThongBao, tb_id)
    if tb is None or tb.nguoi_nhan_id != user_id:
        return False
    if not tb.da_doc:
        tb.da_doc = True
        db.commit()
    return True


def danh_dau_het(db: Session, user_id: int) -> int:
    n = (
        db.query(ThongBao)
        .filter(ThongBao.nguoi_nhan_id == user_id, ThongBao.da_doc == False)  # noqa: E712
        .update({ThongBao.da_doc: True})
    )
    db.commit()
    return n
