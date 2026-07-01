from datetime import datetime

from pydantic import BaseModel, Field


class TaoMucTieuRequest(BaseModel):
    loai: str = Field(..., description="tuan | chu_de")
    tieu_de: str | None = None
    chi_tieu_so: int = Field(..., ge=1)
    dang_id: int | None = None
    chuyen_de: str | None = None
    han: datetime | None = None
