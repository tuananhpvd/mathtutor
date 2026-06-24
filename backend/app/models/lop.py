from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lop(Base):
    __tablename__ = "lop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ten: Mapped[str] = mapped_column(String(100), nullable=False)
    gv_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    giao_vien: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[gv_id], uselist=False
    )
    hoc_sinhs: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="lop", foreign_keys="[User.lop_id]"
    )
