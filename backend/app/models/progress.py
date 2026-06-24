from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("hoc_sinh_id", "chuyen_de", name="uq_progress_hs_chuyende"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    chuyen_de: Mapped[str] = mapped_column(String(200), nullable=False)
    so_bai_lam: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    so_bai_hoan_thanh: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ty_le_dung_trung_binh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tong_thoi_gian_giay: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cap_nhat_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
