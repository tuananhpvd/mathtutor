"""
Báo cáo kết quả học tập của HS (để GV in/gửi phụ huynh — Mô hình C).

TẤT ĐỊNH, không LLM. Dữ liệu gộp từ `phan_tich_service.ho_so_nang_luc` (mạnh/yếu theo
dạng, xu hướng) — KHÔNG chứa bất kỳ trường đáp án nào (đúng nguyên tắc bất biến #3). Cho
phép lọc theo khoảng thời gian (các phiên BẮT ĐẦU trong khoảng).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.lop import Lop
from app.models.user import User, VaiTro
from app.services.phan_tich_service import ho_so_nang_luc


def _rut_gon_dang(rows: list[dict]) -> list[dict]:
    """Chỉ giữ các trường cần cho báo cáo phụ huynh (bỏ chi tiết nội bộ)."""
    return [
        {
            "ten": r["ten"],
            "diem_thanh_thao": r.get("diem_thanh_thao"),
            "so_hoan_thanh": r.get("so_hoan_thanh"),
            "nhan": r.get("nhan"),
        }
        for r in rows
    ]


def bao_cao_hoc_sinh(
    db: Session,
    hoc_sinh_id: int,
    tu_ngay: datetime | None = None,
    den_ngay: datetime | None = None,
) -> dict:
    """Payload báo cáo 1 HS: thông tin HS + tổng quan + mạnh/yếu theo dạng."""
    hs = db.get(User, hoc_sinh_id)
    if hs is None or hs.vai_tro != VaiTro.hs:
        raise ValueError("Không tìm thấy học sinh")
    lop = db.get(Lop, hs.lop_id) if hs.lop_id else None
    ho_so = ho_so_nang_luc(db, hoc_sinh_id, tu_ngay, den_ngay)
    return {
        "hoc_sinh": {
            "id": hs.id,
            "ho_ten": hs.ho_ten,
            "lop_ten": lop.ten if lop else None,
        },
        "tong_quan": {
            "so_phien": ho_so["so_phien"],
            "so_hoan_thanh": ho_so["tong_hoan_thanh"],
            "xu_huong": ho_so["xu_huong"],
            "do_tin_cay": ho_so["do_tin_cay"],
            "du_lieu_du": ho_so["du_lieu_du"],
        },
        "diem_manh": _rut_gon_dang(ho_so["diem_manh"]),
        "diem_yeu": _rut_gon_dang(ho_so["diem_yeu"]),
        "theo_dang": _rut_gon_dang(ho_so["theo_dang"]),
    }


def bao_cao_lop(
    db: Session,
    lop_id: int,
    tu_ngay: datetime | None = None,
    den_ngay: datetime | None = None,
) -> dict:
    """Payload báo cáo cả lớp: thông tin lớp + danh sách báo cáo từng HS (sắp theo tên).

    KHÔNG kiểm quyền ở đây — endpoint gọi phải tự xác nhận lớp thuộc GV (hoặc admin)
    trước khi gọi, mirror các endpoint progress khác."""
    lop = db.get(Lop, lop_id)
    if lop is None:
        raise ValueError("Không tìm thấy lớp")
    hs_list = (
        db.query(User)
        .filter(User.lop_id == lop_id, User.vai_tro == VaiTro.hs)
        .order_by(User.ho_ten)
        .all()
    )
    return {
        "lop": {"id": lop.id, "ten": lop.ten},
        "danh_sach": [
            bao_cao_hoc_sinh(db, hs.id, tu_ngay, den_ngay) for hs in hs_list
        ],
    }
