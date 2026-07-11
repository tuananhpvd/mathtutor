"""Service cho học sinh: hồ sơ cá nhân (xem & cập nhật họ tên / mật khẩu)."""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.user import User


def ho_so(db: Session, hs: User) -> dict:
    lop = db.get(Lop, hs.lop_id) if hs.lop_id else None
    return {
        "id": hs.id,
        "ho_ten": hs.ho_ten,
        "dang_nhap": hs.dang_nhap,
        "vai_tro": hs.vai_tro.value,
        "trang_thai": hs.trang_thai.value,
        "lop_id": hs.lop_id,
        "lop_ten": lop.ten if lop else None,
        "da_xem_huong_dan_phong_hoc": hs.da_xem_huong_dan_phong_hoc,
    }


def cap_nhat_ho_so(db: Session, hs: User, ho_ten: str | None, mat_khau: str | None) -> User:
    if ho_ten:
        hs.ho_ten = ho_ten.strip()
    if mat_khau:
        hs.mat_khau_hash = hash_password(mat_khau)
    db.commit()
    db.refresh(hs)
    return hs


def danh_dau_da_xem_huong_dan(db: Session, hs: User) -> User:
    """HS đã xem hướng dẫn 3 bước lúc vào phòng học — lưu server-side, chỉ hiện 1 lần."""
    if not hs.da_xem_huong_dan_phong_hoc:
        hs.da_xem_huong_dan_phong_hoc = True
        db.commit()
        db.refresh(hs)
    return hs
