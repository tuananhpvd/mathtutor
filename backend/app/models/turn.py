import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VaiTroTurn(str, enum.Enum):
    hoc_sinh = "hoc_sinh"
    gia_su = "gia_su"


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    vai_tro: Mapped[VaiTroTurn] = mapped_column(Enum(VaiTroTurn), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    dap_an_nhap: Mapped[str | None] = mapped_column(Text, nullable=True)
    ket_qua_so_khop: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cap_goi_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    co_bi_chot_chan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thoi_diem: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session: Mapped["Session"] = relationship("Session", back_populates="turns")  # noqa: F821
