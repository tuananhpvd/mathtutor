"""
Admin service: thống kê tổng, quản lý tài khoản, cấu hình hệ thống.
"""

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config import SO_GOI_Y_MAC_DINH, settings
from app.core.matching.scoring import BANG_BAC_THANG
from app.models.cauhinh import CauHinh
from app.models.flag import Flag, TrangThaiCo
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.user import TrangThaiUser, User, VaiTro

# Cấu hình mặc định (dùng khi DB chưa có bản ghi).
CAU_HINH_MAC_DINH: dict = {
    "nguong_co_khong_hieu": 3,
    "llm_temperature": settings.llm_temperature,
    "so_goi_y_mac_dinh": SO_GOI_Y_MAC_DINH,
    "bang_bac_thang": {str(k): v for k, v in BANG_BAC_THANG.items()},
}


def thong_ke(db: Session) -> dict:
    return {
        "so_nguoi_dung": db.query(User).count(),
        "so_giao_vien": db.query(User).filter(User.vai_tro == VaiTro.gv).count(),
        "so_hoc_sinh": db.query(User).filter(User.vai_tro == VaiTro.hs).count(),
        "so_cau_hoi": db.query(Problem).count(),
        "so_cau_da_duyet": db.query(Problem)
        .filter(Problem.trang_thai_duyet == TrangThaiDuyet.da_duyet)
        .count(),
        "so_phien": db.query(SessionModel).count(),
        "so_co_chua_xu_ly": db.query(Flag)
        .filter(Flag.trang_thai == TrangThaiCo.cho_xu_ly)
        .count(),
        "llm_provider": settings.llm_provider,
    }


def danh_sach_tai_khoan(db: Session) -> list[dict]:
    users = db.query(User).order_by(User.id).all()
    return [
        {
            "id": u.id,
            "ho_ten": u.ho_ten,
            "dang_nhap": u.dang_nhap,
            "vai_tro": u.vai_tro.value,
            "trang_thai": u.trang_thai.value,
            "lop_id": u.lop_id,
        }
        for u in users
    ]


def tao_tai_khoan(
    db: Session, ho_ten: str, dang_nhap: str, mat_khau: str, vai_tro: str, lop_id: int | None
) -> User:
    if vai_tro not in {"gv", "hs"}:
        raise ValueError("Chỉ tạo được tài khoản gv hoặc hs")
    if db.query(User).filter(User.dang_nhap == dang_nhap).first():
        raise ValueError("Tên đăng nhập đã tồn tại")
    user = User(
        ho_ten=ho_ten,
        dang_nhap=dang_nhap,
        mat_khau_hash=hash_password(mat_khau),
        vai_tro=VaiTro(vai_tro),
        lop_id=lop_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def doi_trang_thai_tai_khoan(db: Session, user_id: int, trang_thai: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Không tìm thấy tài khoản")
    if user.vai_tro == VaiTro.admin:
        raise ValueError("Không thể khóa tài khoản admin")
    user.trang_thai = TrangThaiUser(trang_thai)
    db.commit()
    db.refresh(user)
    return user


def lay_cau_hinh(db: Session) -> dict:
    ket_qua = dict(CAU_HINH_MAC_DINH)
    for row in db.query(CauHinh).all():
        ket_qua[row.khoa] = row.gia_tri.get("v", row.gia_tri)
    return ket_qua


def dat_cau_hinh(db: Session, khoa: str, gia_tri) -> dict:
    if khoa not in CAU_HINH_MAC_DINH:
        raise ValueError(f"Khóa cấu hình không hợp lệ: {khoa}")
    row = db.get(CauHinh, khoa)
    if row is None:
        row = CauHinh(khoa=khoa, gia_tri={"v": gia_tri})
        db.add(row)
    else:
        row.gia_tri = {"v": gia_tri}
    db.commit()
    return lay_cau_hinh(db)
