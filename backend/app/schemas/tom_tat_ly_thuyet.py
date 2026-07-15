from pydantic import BaseModel, Field


class TomTatCreate(BaseModel):
    chuyen_de_id: int
    dang_id: int | None = None
    tieu_de: str = Field(..., min_length=1, max_length=200)
    noi_dung: str = Field(default="")
    tu_khoa: list[str] = Field(default_factory=list)
    hien: bool = False


class TomTatUpdate(BaseModel):
    chuyen_de_id: int | None = None
    dang_id: int | None = None
    tieu_de: str | None = Field(None, min_length=1, max_length=200)
    noi_dung: str | None = None
    tu_khoa: list[str] | None = None
    hien: bool | None = None
