import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class VaiTroTurn(str, enum.Enum):
    hoc_sinh = "hoc_sinh"
    gia_su = "gia_su"
    giao_vien = "giao_vien"  # GV trả lời trực tiếp trong bài (A2)


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    vai_tro: Mapped[VaiTroTurn] = mapped_column(Enum(VaiTroTurn), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    dap_an_nhap: Mapped[str | None] = mapped_column(Text, nullable=True)
    ket_qua_so_khop: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cap_goi_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Bước/ý mà lượt này thuộc về — để FE dựng "dải phân cách bước" trong khung chat, kể cả
    # khi HS "Làm tiếp" (tải lại lịch sử). CHỈ lưu SỐ THỨ TỰ bước (và ký hiệu ý với TNDS),
    # KHÔNG lưu nguyên văn mô tả: mô tả được tra ĐỘNG lúc render theo bản solution_steps mới
    # nhất, nên GV sửa mô tả bước thì lịch sử hiển thị theo bản mới, không bị lệch.
    # Nullable: lượt tạo TRƯỚC khi có cột này = NULL → FE không dựng phân cách (thoái lui êm).
    buoc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y: Mapped[str | None] = mapped_column(String(10), nullable=True)
    co_bi_chot_chan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thoi_diem: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session: Mapped["Session"] = relationship("Session", back_populates="turns")  # noqa: F821
