import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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
    so_y_dung: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    diem: Mapped[float | None] = mapped_column(Float, nullable=True)
    bat_dau_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    thoi_gian_giay: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cap_nhat_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    turns: Mapped[list["Turn"]] = relationship("Turn", back_populates="session")  # noqa: F821
