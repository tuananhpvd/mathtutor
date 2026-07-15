"""Tóm tắt lý thuyết GV soạn cho học sinh xem lại (không qua AI — nội dung GV kiểm soát)."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TomTatLyThuyet(Base):
    """1 bản tóm tắt gắn với 1 chuyên đề (dang_id=None) hoặc 1 dạng cụ thể của chuyên đề đó.

    noi_dung: văn bản tự do GV soạn liền mạch (như 1 tài liệu) — công thức viết trong cặp
    $...$ (quy ước KaTeX dùng chung toàn app), ảnh chèn bằng cú pháp Markdown ![chú thích](url)
    ngay tại vị trí con trỏ. Render lại đúng thứ tự bằng NoiDungLyThuyet.jsx (frontend)."""

    __tablename__ = "tom_tat_ly_thuyet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chuyen_de_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chuyen_de.id"), nullable=False, index=True
    )
    dang_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dang.id"), nullable=True, index=True
    )
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    noi_dung: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tu_khoa: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    hien: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    tao_luc: Mapped[datetime] = mapped_column(UTCDateTime, default=_now, nullable=False)
    cap_nhat_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_now, onupdate=_now, nullable=False
    )
