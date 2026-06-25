from pydantic import BaseModel, Field


class HoSoUpdate(BaseModel):
    ho_ten: str | None = None
    mat_khau: str | None = Field(None, min_length=4)
