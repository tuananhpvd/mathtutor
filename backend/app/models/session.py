import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class TrangThaiSession(str, enum.Enum):
    dang_lam = "dang_lam"
    hoan_thanh = "hoan_thanh"
    bo_do = "bo_do"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"), nullable=False)
    trang_thai: Mapped[TrangThaiSession] = mapped_column(
        Enum(TrangThaiSession), default=TrangThaiSession.dang_lam, nullable=False
    )
    buoc_hien_tai: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    y_hien_tai: Mapped[str | None] = mapped_column(String(10), nullable=True)
    trang_thai_y: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cap_goi_y_hien_tai: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    so_lan_sai_lien_tiep: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    so_lan_khong_hieu: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Tổng số lần sai CẢ PHIÊN (không reset qua bước/ý, khác so_lan_sai_lien_tiep) — dùng để
    # kể lại hành trình cho HS lúc hoàn thành + tính điểm quá trình cho GV.
    tong_so_lan_sai: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Số lần HS cạn SẠCH thang gợi ý của 1 bước/ý (khoảnh khắc khối 3 liên kết hiện ra) —
    # tín hiệu "bí thật" mạnh hơn so_lan_khong_hieu (vốn tính cả lần chỉ hỏi 1-2 gợi ý).
    so_lan_het_goi_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Số lần HS bấm "Xem lại lý thuyết" từ trong phiên — tín hiệu tự nhận thức hổng lý thuyết.
    so_lan_xem_ly_thuyet: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Điểm quá trình (0-1, CHỈ GV/Admin thấy — không phải điểm chính thức): tính từ số lần
    # sai + xin gợi ý, phân hóa HS "làm phát ăn ngay" và HS "bò qua nhiều lần sai/gợi ý" dù
    # cùng điểm hoàn thành. None khi phiên chưa hoàn thành.
    diem_qua_trinh: Mapped[float | None] = mapped_column(Float, nullable=True)
    so_y_dung: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # TN4PA/TNDS: đã suy luận đúng cho ý/bước hiện tại chưa (mở khóa chọn đáp án/Đúng-Sai)
    da_suy_luan: Mapped[bool] = mapped_column(default=False, nullable=False)
    # TNDS: thời gian (giây) làm từng ý {a: 12, b: 30, ...}
    thoi_gian_y: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diem: Mapped[float | None] = mapped_column(Float, nullable=True)
    bat_dau_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # Thời gian HOẠT ĐỘNG tích lũy (giây) — cộng dồn mỗi lượt, đã chặn khoảng nghỉ dài.
    thoi_gian_hoat_dong_giay: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    # Thời gian làm bài cuối cùng (giây) khi hoàn thành = thoi_gian_hoat_dong_giay.
    thoi_gian_giay: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cap_nhat_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # Soft-reset: True khi GV yêu cầu đặt lại tiến độ HS và admin đã duyệt.
    bi_an: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    turns: Mapped[list["Turn"]] = relationship("Turn", back_populates="session")  # noqa: F821
