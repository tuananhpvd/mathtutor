import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoaiThongBao(str, enum.Enum):
    nhan_xet = "nhan_xet"         # GV gửi nhận xét cho HS (A1)
    co = "co"                     # HS được báo đang gặp khó / bị gắn cờ (A4)
    nhiem_vu = "nhiem_vu"         # GV giao nhiệm vụ (A3)
    nho_tro_giup = "nho_tro_giup"  # HS nhờ thầy/cô → báo GV (A2)
    tra_loi = "tra_loi"           # GV trả lời yêu cầu "Nhờ thầy/cô" → báo HS (A2)
    quan_ly = "quan_ly"           # Tài khoản Quản lý sửa/xóa nội dung của GV → báo GV
    he_thong = "he_thong"


class ThongBao(Base):
    """Thông báo gửi tới 1 người dùng (HS hoặc GV). Xương sống cho các tính năng
    đồng hành GV↔HS: nhận xét, giao nhiệm vụ, trả lời, báo cờ..."""

    __tablename__ = "thong_bao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nguoi_nhan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    nguoi_gui_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # None = hệ thống
    loai: Mapped[LoaiThongBao] = mapped_column(
        Enum(LoaiThongBao), default=LoaiThongBao.he_thong, nullable=False
    )
    tieu_de: Mapped[str | None] = mapped_column(String(200), nullable=True)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    # Liên kết sâu tới thực thể nguồn (vd 'session' + id) để mở đúng chỗ.
    lien_ket_loai: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lien_ket_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    da_doc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
