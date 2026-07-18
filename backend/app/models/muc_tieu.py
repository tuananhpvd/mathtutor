from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime


class MucTieu(Base):
    """Mục tiêu học tập của HS (B1).

    - loai = 'tuan': hoàn thành `chi_tieu_so` bài trong 7 ngày kể từ moc_bat_dau.
    - loai = 'chu_de': hoàn thành `chi_tieu_so` bài thuộc dạng `dang_id` (từ moc_bat_dau).
    - loai = 'nhieu': gồm NHIỀU dòng con (`muc_con` JSON) — mỗi dòng là 1 bộ lọc riêng kèm số
      lượng, VD [{"dang_id":3,"chi_tieu_so":3}, {"do_kho":"kho","chi_tieu_so":2}]. Mỗi dòng đếm
      độc lập; mục tiêu ĐẠT khi MỌI dòng đạt. Bao trùm 2 kiểu cũ; chúng giữ để tương thích ngược.
    nguon = 'hs' | 'gv' | 'he_thong' (xuất xứ). Tiến độ tính động từ phiên hoàn thành.

    Mỗi phần tử `muc_con`: {dang_id?, chuyen_de?, loai_cau?, do_kho?, chi_tieu_so} — trường lọc
    None/vắng = không lọc theo tiêu chí đó; đếm bài hoàn thành thỏa TẤT CẢ tiêu chí của dòng.
    """

    __tablename__ = "muc_tieu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hoc_sinh_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    nguoi_tao_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    nguon: Mapped[str] = mapped_column(String(16), default="hs", nullable=False)
    loai: Mapped[str] = mapped_column(String(16), nullable=False)  # tuan | chu_de | nhieu
    tieu_de: Mapped[str] = mapped_column(String(200), nullable=False)
    dang_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dang.id"), nullable=True)
    chuyen_de: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # loai='nhieu': danh sách dòng con [{dang_id?, chuyen_de?, loai_cau?, do_kho?, chi_tieu_so}].
    muc_con: Mapped[list | None] = mapped_column(JSON, nullable=True)
    chi_tieu_so: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    moc_bat_dau: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    han: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    da_huy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tao_luc: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
