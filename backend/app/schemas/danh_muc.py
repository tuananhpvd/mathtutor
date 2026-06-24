from pydantic import BaseModel, Field


# ---------- Chuyên đề ----------
class ChuyenDeCreate(BaseModel):
    ten: str = Field(..., min_length=1, max_length=200)
    mo_ta: str | None = None
    thu_tu: int = 0


class ChuyenDeUpdate(BaseModel):
    ten: str | None = Field(None, min_length=1, max_length=200)
    mo_ta: str | None = None
    thu_tu: int | None = None


# ---------- Dạng ----------
class DangCreate(BaseModel):
    chuyen_de_id: int
    ten: str = Field(..., min_length=1, max_length=200)
    mo_ta: str | None = None
    thu_tu: int = 0


class DangUpdate(BaseModel):
    chuyen_de_id: int | None = None
    ten: str | None = Field(None, min_length=1, max_length=200)
    mo_ta: str | None = None
    thu_tu: int | None = None
