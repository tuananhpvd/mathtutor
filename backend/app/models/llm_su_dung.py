from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LLMSuDung(Base):
    """Đếm lượt gọi LLM theo ngày — phanh chi phí quota.

    Mỗi dòng = (ngày UTC, người dùng, loại tác vụ) → số lượt đã gọi LLM THẬT
    (stub không tính). user_id NULL = lượt của tác vụ nền không gắn người dùng.
    """

    __tablename__ = "llm_su_dung"
    __table_args__ = (UniqueConstraint("ngay", "user_id", "loai", name="uq_llm_su_dung"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ngay: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD (UTC)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loai: Mapped[str] = mapped_column(String(20), nullable=False)  # hoi_thoai | sinh_cau_hoi | phan_tich
    so_luot: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
