from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SolutionStep(Base):
    __tablename__ = "solution_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    problem_id: Mapped[int] = mapped_column(Integer, ForeignKey("problems.id"), nullable=False)
    thu_tu: Mapped[int] = mapped_column(Integer, nullable=False)
    pham_vi: Mapped[str] = mapped_column(String(10), nullable=False, default="ca_bai")
    mo_ta: Mapped[str] = mapped_column(Text, nullable=False)
    bieu_thuc_ket_qua: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    danh_sach_goi_y: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    problem: Mapped["Problem"] = relationship(  # noqa: F821
        "Problem", back_populates="solution_steps"
    )
