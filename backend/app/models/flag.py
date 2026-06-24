import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoaiCo(str, enum.Enum):
    ro_ri_dap_an = "ro_ri_dap_an"
    noi_dung_khong_phu_hop = "noi_dung_khong_phu_hop"
    ngoai_pham_vi = "ngoai_pham_vi"
    thu_cong = "thu_cong"


class TrangThaiCo(str, enum.Enum):
    cho_xu_ly = "cho_xu_ly"
    da_xu_ly = "da_xu_ly"
    bo_qua = "bo_qua"


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=True)
    turn_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("turns.id"), nullable=True)
    loai_co: Mapped[LoaiCo] = mapped_column(Enum(LoaiCo), nullable=False)
    trang_thai: Mapped[TrangThaiCo] = mapped_column(
        Enum(TrangThaiCo), default=TrangThaiCo.cho_xu_ly, nullable=False
    )
    ghi_chu: Mapped[str | None] = mapped_column(Text, nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    xu_ly_boi: Mapped[str | None] = mapped_column(String(100), nullable=True)
