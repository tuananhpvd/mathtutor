from datetime import datetime

from pydantic import BaseModel, Field


class MucConItem(BaseModel):
    """1 dòng con của mục tiêu 'nhiều' — bộ lọc kèm số lượng (bỏ trống tiêu chí = không lọc)."""
    dang_id: int | None = None
    chuyen_de: str | None = None
    loai_cau: str | None = None  # TN4PA | TNDS | TLN
    do_kho: str | None = None    # de | tb | kho
    chi_tieu_so: int = Field(..., ge=1)


class TaoMucTieuRequest(BaseModel):
    loai: str = Field(..., description="tuan | chu_de | nhieu")
    tieu_de: str | None = None
    chi_tieu_so: int | None = Field(None, ge=1)  # cho tuan | chu_de (không dùng cho 'nhieu')
    dang_id: int | None = None
    chuyen_de: str | None = None
    han: datetime | None = None
    muc: list[MucConItem] | None = Field(None, max_length=30)  # cho 'nhieu'
