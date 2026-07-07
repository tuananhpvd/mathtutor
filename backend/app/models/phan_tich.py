from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class PhanTich(Base):
    """Bản phân tích AI đã sinh cho 1 học sinh (cache, mỗi HS 1 bản mới nhất)."""

    __tablename__ = "phan_tich_hs"
    __table_args__ = (UniqueConstraint("hoc_sinh_id", name="uq_phantich_hs"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    noi_dung_hs: Mapped[str | None] = mapped_column(Text, nullable=True)
    noi_dung_gv: Mapped[str | None] = mapped_column(Text, nullable=True)
    so_bai_luc_tao: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Nguồn nội dung: "ai" (LLM diễn giải) | "luat" (đề xuất theo luật khi LLM không khả dụng).
    nguon: Mapped[str] = mapped_column(String(16), default="ai", nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
