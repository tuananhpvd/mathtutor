import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TrangThaiBaiThi(str, enum.Enum):
    dang_thi = "dang_thi"
    da_nop = "da_nop"


class DeThi(Base):
    """Đề ôn thi THPT (C1): GV ghép câu từ ngân hàng theo cấu trúc 3 phần.

    Cấu trúc chuẩn 2025: Phần I — 12 câu TN4PA (0,25đ/câu); Phần II — 4 câu TNDS
    (điểm bậc thang theo số ý đúng, tối đa 1đ/câu); Phần III — 6 câu TLN (0,5đ/câu).
    GV được ghép số câu khác chuẩn — điểm tối đa khi đó khác 10 và hiển thị rõ.
    """

    __tablename__ = "de_thi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ten: Mapped[str] = mapped_column(String(200), nullable=False)
    nguoi_tao_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    thoi_gian_phut: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    # Chỉ đề đã phát hành mới hiện với HS; thu hồi = ẩn với HS (bài đã nộp giữ nguyên).
    phat_hanh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(UTCDateTime, default=_now, nullable=False)

    cau_list: Mapped[list["DeThiCau"]] = relationship(
        "DeThiCau", back_populates="de_thi", order_by="DeThiCau.thu_tu",
        cascade="all, delete-orphan",
    )


class DeThiCau(Base):
    """Một câu trong đề: gắn problem + phần (I/II/III) + thứ tự."""

    __tablename__ = "de_thi_cau"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    de_thi_id: Mapped[int] = mapped_column(Integer, ForeignKey("de_thi.id"), nullable=False)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"), nullable=False)
    phan: Mapped[str] = mapped_column(String(5), nullable=False)  # I | II | III
    thu_tu: Mapped[int] = mapped_column(Integer, nullable=False)

    de_thi: Mapped["DeThi"] = relationship("DeThi", back_populates="cau_list")


class BaiThi(Base):
    """Một lượt HS làm một đề: bài làm tạm (autosave) + kết quả chấm sau nộp."""

    __tablename__ = "bai_thi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    de_thi_id: Mapped[int] = mapped_column(Integer, ForeignKey("de_thi.id"), nullable=False)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    trang_thai: Mapped[TrangThaiBaiThi] = mapped_column(
        Enum(TrangThaiBaiThi), default=TrangThaiBaiThi.dang_thi, nullable=False
    )
    bat_dau_luc: Mapped[datetime] = mapped_column(UTCDateTime, default=_now, nullable=False)
    nop_luc: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    # {de_thi_cau_id (str): đáp án nhập} — TN4PA: "A"; TNDS: {"a":"Dung",...}; TLN: "5".
    bai_lam: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    diem: Mapped[float | None] = mapped_column(Float, nullable=True)
    diem_toi_da: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Chi tiết chấm từng câu (CHỈ ghi khi đã nộp): [{de_thi_cau_id, problem_id, phan,
    # thu_tu, dung, diem, diem_toi_da}] — đáp án đúng trả qua API riêng sau nộp.
    chi_tiet: Mapped[list | None] = mapped_column(JSON, nullable=True)
