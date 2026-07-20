import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime


class VaiTro(str, enum.Enum):
    admin = "admin"
    gv = "gv"
    hs = "hs"


class TrangThaiUser(str, enum.Enum):
    hoat_dong = "hoat_dong"
    khoa = "khoa"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vai_tro: Mapped[VaiTro] = mapped_column(Enum(VaiTro), nullable=False)
    ho_ten: Mapped[str] = mapped_column(String(200), nullable=False)
    dang_nhap: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    mat_khau_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    trang_thai: Mapped[TrangThaiUser] = mapped_column(
        Enum(TrangThaiUser), default=TrangThaiUser.hoat_dong, nullable=False
    )
    # Tài khoản GV đặc biệt "Quản lý": toàn quyền trên nội dung mọi GV (không phải admin).
    la_quan_ly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lop_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("lop.id"), nullable=True)
    # HS: đã xem hướng dẫn 3 bước lúc vào phòng học lần đầu chưa — lưu server-side (không
    # dùng localStorage) để hướng dẫn chỉ hiện đúng 1 lần dù đổi máy/trình duyệt.
    da_xem_huong_dan_phong_hoc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Thời điểm tạo tài khoản. NULLABLE có chủ ý: tài khoản đã tồn tại trước khi có cột này
    # KHÔNG biết được ngày tạo thật — để NULL trung thực hơn là gán bừa thời điểm chạy
    # migration. Dùng cho trần chống spam "số đăng ký/lớp/ngày" (xem dang_ky_service).
    tao_luc: Mapped[datetime | None] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=True
    )

    lop: Mapped["Lop | None"] = relationship("Lop", back_populates="hoc_sinhs", foreign_keys=[lop_id])  # noqa: F821
