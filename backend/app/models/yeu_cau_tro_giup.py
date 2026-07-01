import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrangThaiTroGiup(str, enum.Enum):
    cho_xu_ly = "cho_xu_ly"
    da_tra_loi = "da_tra_loi"


class YeuCauTroGiup(Base):
    """HS bấm 'Nhờ thầy/cô' khi bí một bài → tạo yêu cầu kèm ngữ cảnh (bước/ý).
    GV trả lời → câu trả lời chèn vào đúng khung hội thoại của bài (A2)."""

    __tablename__ = "yeu_cau_tro_giup"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"), nullable=False)
    buoc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y: Mapped[str | None] = mapped_column(String(10), nullable=True)
    noi_dung: Mapped[str | None] = mapped_column(Text, nullable=True)  # câu hỏi HS (tùy chọn)
    trang_thai: Mapped[TrangThaiTroGiup] = mapped_column(
        Enum(TrangThaiTroGiup), default=TrangThaiTroGiup.cho_xu_ly, nullable=False
    )
    tra_loi: Mapped[str | None] = mapped_column(Text, nullable=True)
    gv_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    tra_loi_luc: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
