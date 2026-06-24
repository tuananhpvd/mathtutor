from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CauHinh(Base):
    """Cấu hình hệ thống dạng key-value (Admin chỉnh được mà không sửa code)."""

    __tablename__ = "cau_hinh"

    khoa: Mapped[str] = mapped_column(String(100), primary_key=True)
    gia_tri: Mapped[dict] = mapped_column(JSON, nullable=False)
