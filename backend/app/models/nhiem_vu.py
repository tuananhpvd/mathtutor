from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NhiemVu(Base):
    """Nhiệm vụ GV giao cho HS/lớp: gồm nhiều bài, có hạn (A3)."""

    __tablename__ = "nhiem_vu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gv_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(Text, nullable=True)
    han_chot: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class NhiemVuBai(Base):
    __tablename__ = "nhiem_vu_bai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nhiem_vu_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nhiem_vu.id"), nullable=False, index=True
    )
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"), nullable=False)


class NhiemVuHocSinh(Base):
    __tablename__ = "nhiem_vu_hoc_sinh"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nhiem_vu_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nhiem_vu.id"), nullable=False, index=True
    )
    hoc_sinh_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
