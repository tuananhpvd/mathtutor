import enum
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class TrangThaiYeuCau(str, enum.Enum):
    cho_duyet = "cho_duyet"
    da_duyet = "da_duyet"
    tu_choi = "tu_choi"


class YeuCauDatLai(Base):
    __tablename__ = "yeu_cau_dat_lai"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    yeu_cau_boi_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    ly_do: Mapped[str] = mapped_column(Text, nullable=False)
    trang_thai: Mapped[TrangThaiYeuCau] = mapped_column(
        Enum(TrangThaiYeuCau), default=TrangThaiYeuCau.cho_duyet, nullable=False
    )
    tao_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    xu_ly_boi_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    xu_ly_luc: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    ghi_chu_admin: Mapped[str | None] = mapped_column(Text, nullable=True)
