from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class CotMoc(Base):
    __tablename__ = "cot_moc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    loai: Mapped[str] = mapped_column(String(50), nullable=False)
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    mo_ta: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dat_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
