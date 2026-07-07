"""
Danh mục 3 cấp: ChuyenDe (chuyên đề) → Dang (dạng) → Problem (câu hỏi).
Câu hỏi gắn vào một Dang qua khóa ngoại; cột chuyen_de (chuỗi) trên Problem được
giữ lại (denormalized) để tương thích với progress/sessions/scope đang dùng tên chuyên đề.
"""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChuyenDe(Base):
    __tablename__ = "chuyen_de"
    # Tên chuyên đề chỉ duy nhất TRONG phạm vi một GV — các GV khác được trùng tên.
    __table_args__ = (UniqueConstraint("nguoi_tao_id", "ten", name="uq_chuyende_nguoitao_ten"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ten: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(Text, nullable=True)
    thu_tu: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(UTCDateTime, default=_now, nullable=False)

    dang_list: Mapped[list["Dang"]] = relationship(
        "Dang",
        back_populates="chuyen_de",
        order_by="Dang.thu_tu, Dang.id",
        cascade="all, delete-orphan",
    )


class Dang(Base):
    __tablename__ = "dang"
    __table_args__ = (UniqueConstraint("chuyen_de_id", "ten", name="uq_dang_chuyende_ten"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chuyen_de_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chuyen_de.id"), nullable=False, index=True
    )
    ten: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(Text, nullable=True)
    thu_tu: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(UTCDateTime, default=_now, nullable=False)

    chuyen_de: Mapped["ChuyenDe"] = relationship("ChuyenDe", back_populates="dang_list")
    problems: Mapped[list["Problem"]] = relationship(  # noqa: F821
        "Problem", back_populates="dang"
    )
