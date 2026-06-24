import enum

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LoaiCau(str, enum.Enum):
    TN4PA = "TN4PA"
    TNDS = "TNDS"
    TLN = "TLN"


class DoKho(str, enum.Enum):
    de = "de"
    tb = "tb"
    kho = "kho"


class TrangThaiDuyet(str, enum.Enum):
    cho_duyet = "cho_duyet"
    da_duyet = "da_duyet"
    loai = "loai"


class Nguon(str, enum.Enum):
    gv_nhap = "gv_nhap"
    ai_sinh = "ai_sinh"


class CheDoSoKhopEnum(str, enum.Enum):
    tuong_duong = "tuong_duong"
    dung_dang = "dung_dang"


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Tên chuyên đề (denormalized) — giữ để tương thích progress/sessions/scope.
    chuyen_de: Mapped[str] = mapped_column(String(200), nullable=False)
    # Khóa ngoại tới Dạng trong danh mục (nullable: nháp AI/bài cũ có thể chưa gán).
    dang_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dang.id"), nullable=True, index=True
    )
    loai_cau: Mapped[LoaiCau] = mapped_column(Enum(LoaiCau), nullable=False)
    do_kho: Mapped[DoKho] = mapped_column(Enum(DoKho), nullable=False)
    de_bai: Mapped[str] = mapped_column(Text, nullable=False)
    loai_dap_an_nhap: Mapped[str] = mapped_column(String(50), nullable=False)
    che_do_so_khop: Mapped[CheDoSoKhopEnum] = mapped_column(
        Enum(CheDoSoKhopEnum), default=CheDoSoKhopEnum.tuong_duong, nullable=False
    )
    trang_thai_duyet: Mapped[TrangThaiDuyet] = mapped_column(
        Enum(TrangThaiDuyet), default=TrangThaiDuyet.cho_duyet, nullable=False
    )
    nguon: Mapped[Nguon] = mapped_column(Enum(Nguon), default=Nguon.gv_nhap, nullable=False)
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    solution_steps: Mapped[list["SolutionStep"]] = relationship(  # noqa: F821
        "SolutionStep", back_populates="problem", order_by="SolutionStep.thu_tu"
    )
    dang: Mapped["Dang | None"] = relationship(  # noqa: F821
        "Dang", back_populates="problems"
    )
