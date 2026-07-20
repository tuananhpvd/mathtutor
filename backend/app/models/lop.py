from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class Lop(Base):
    __tablename__ = "lop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ten: Mapped[str] = mapped_column(String(100), nullable=False)
    gv_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Mã mời để HS TỰ đăng ký vào đúng lớp (mức 1 của lộ trình gỡ nút thắt triển khai).
    # NULL = lớp ĐÓNG, không cho tự đăng ký — cố ý không thêm cờ "cho_tu_dang_ky" riêng để
    # tránh hai nguồn sự thật lệch nhau. Dùng unique INDEX (không phải unique CONSTRAINT) vì
    # SQLite không ALTER thêm được constraint mà không rebuild bảng; nhiều NULL vẫn hợp lệ
    # trong unique index ở cả SQLite lẫn Postgres.
    ma_lop: Mapped[str | None] = mapped_column(
        String(16), nullable=True, unique=True, index=True
    )
    # NULL = mã không hết hạn. Có hạn giúp mã lỡ bị phát tán ra ngoài lớp sẽ tự vô hiệu.
    ma_het_han: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    giao_vien: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[gv_id], uselist=False
    )
    hoc_sinhs: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="lop", foreign_keys="[User.lop_id]"
    )
