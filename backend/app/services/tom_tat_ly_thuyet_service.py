"""Tóm tắt lý thuyết (Pha 1 — GV soạn, HS xem lại). TẤT ĐỊNH, không LLM.

Phân quyền/kiểm chủ sở hữu chuyên đề/dạng thực hiện ở tầng API (app/api/tom_tat_ly_thuyet.py),
theo đúng quy ước đã dùng ở danh_muc_service — service chỉ thao tác dữ liệu thuần."""

from sqlalchemy.orm import Session

from app.models.danh_muc import ChuyenDe, Dang
from app.models.tom_tat_ly_thuyet import TomTatLyThuyet


def tao_tom_tat(db: Session, nguoi_tao_id: int | None, data: dict) -> TomTatLyThuyet:
    dang_id = data.get("dang_id")
    if dang_id is not None:
        d = db.get(Dang, dang_id)
        if d is None or d.chuyen_de_id != data["chuyen_de_id"]:
            raise ValueError("Dạng không thuộc chuyên đề đã chọn")
    tt = TomTatLyThuyet(nguoi_tao_id=nguoi_tao_id, **data)
    db.add(tt)
    db.commit()
    db.refresh(tt)
    return tt


def sua_tom_tat(db: Session, tt_id: int, data: dict) -> TomTatLyThuyet:
    tt = db.get(TomTatLyThuyet, tt_id)
    if tt is None:
        raise ValueError("Không tìm thấy tóm tắt")
    chuyen_de_id = data.get("chuyen_de_id", tt.chuyen_de_id)
    dang_id = data.get("dang_id", tt.dang_id)
    if dang_id is not None:
        d = db.get(Dang, dang_id)
        if d is None or d.chuyen_de_id != chuyen_de_id:
            raise ValueError("Dạng không thuộc chuyên đề đã chọn")
    for k, v in data.items():
        setattr(tt, k, v)
    db.commit()
    db.refresh(tt)
    return tt


def xoa_tom_tat(db: Session, tt_id: int) -> None:
    tt = db.get(TomTatLyThuyet, tt_id)
    if tt is None:
        raise ValueError("Không tìm thấy tóm tắt")
    db.delete(tt)
    db.commit()


def _ten_map(db: Session, gv_id: int) -> tuple[dict[int, str], dict[int, str]]:
    """Map chuyen_de_id/dang_id → tên, giới hạn trong phạm vi 1 GV (1 query mỗi loại)."""
    cd_ten = {cd.id: cd.ten for cd in db.query(ChuyenDe).filter(ChuyenDe.nguoi_tao_id == gv_id).all()}
    dang_ten = {
        d.id: d.ten
        for d in db.query(Dang).join(ChuyenDe, Dang.chuyen_de_id == ChuyenDe.id)
        .filter(ChuyenDe.nguoi_tao_id == gv_id).all()
    }
    return cd_ten, dang_ten


def _tt_dict(tt: TomTatLyThuyet, cd_ten: dict[int, str], dang_ten: dict[int, str]) -> dict:
    return {
        "id": tt.id,
        "chuyen_de_id": tt.chuyen_de_id,
        "chuyen_de_ten": cd_ten.get(tt.chuyen_de_id),
        "dang_id": tt.dang_id,
        "dang_ten": dang_ten.get(tt.dang_id) if tt.dang_id else None,
        "tieu_de": tt.tieu_de,
        "noi_dung": tt.noi_dung,
        "tu_khoa": tt.tu_khoa,
        "hien": tt.hien,
        "tao_luc": tt.tao_luc.isoformat(),
        "cap_nhat_luc": tt.cap_nhat_luc.isoformat(),
    }


def danh_sach_gv(db: Session, gv_id: int) -> list[dict]:
    """GV xem TẤT CẢ tóm tắt của mình (kể cả đang ẩn với HS)."""
    rows = (
        db.query(TomTatLyThuyet)
        .filter(TomTatLyThuyet.nguoi_tao_id == gv_id)
        .order_by(TomTatLyThuyet.cap_nhat_luc.desc())
        .all()
    )
    cd_ten, dang_ten = _ten_map(db, gv_id)
    return [_tt_dict(tt, cd_ten, dang_ten) for tt in rows]


def danh_sach_hs(
    db: Session, gv_id: int, chuyen_de_id: int | None = None, dang_id: int | None = None
) -> list[dict]:
    """HS chỉ xem tóm tắt hien=True của GV chủ nhiệm, lọc tùy chọn theo chuyên đề/dạng."""
    q = db.query(TomTatLyThuyet).filter(
        TomTatLyThuyet.nguoi_tao_id == gv_id,
        TomTatLyThuyet.hien == True,  # noqa: E712
    )
    if chuyen_de_id is not None:
        q = q.filter(TomTatLyThuyet.chuyen_de_id == chuyen_de_id)
    if dang_id is not None:
        q = q.filter(TomTatLyThuyet.dang_id == dang_id)
    rows = q.order_by(TomTatLyThuyet.chuyen_de_id, TomTatLyThuyet.cap_nhat_luc.desc()).all()
    cd_ten, dang_ten = _ten_map(db, gv_id)
    return [_tt_dict(tt, cd_ten, dang_ten) for tt in rows]
