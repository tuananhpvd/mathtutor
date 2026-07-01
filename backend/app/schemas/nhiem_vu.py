from datetime import datetime

from pydantic import BaseModel, Field


class TaoNhiemVuRequest(BaseModel):
    tieu_de: str = Field(..., min_length=1)
    mo_ta: str | None = None
    han_chot: datetime | None = None
    problem_ids: list[int] = Field(..., min_length=1)
    hoc_sinh_ids: list[int] = []
    lop_ids: list[int] = []
