from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class MucTieu(Base):
    """Mục tiêu học tập của HS (B1).

    - loai = 'tuan': hoàn thành `chi_tieu_so` bài trong 7 ngày kể từ moc_bat_dau.
    - loai = 'chu_de': hoàn thành `chi_tieu_so` bài thuộc dạng `dang_id` (từ moc_bat_dau).
    nguon = 'hs' | 'gv' | 'he_thong' (xuất xứ). Tiến độ tính động từ phiên hoàn thành.
    """

    __tablename__ = "muc_tieu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    nguon: Mapped[str] = mapped_column(String(16), default="hs", nullable=False)
    loai: Mapped[str] = mapped_column(String(16), nullable=False)  # tuan | chu_de
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    dang_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dang.id"), nullable=True)
    chuyen_de: Mapped[str | None] = mapped_column(String(200), nullable=True)
    chi_tieu_so: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    moc_bat_dau: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    han: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    da_huy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
