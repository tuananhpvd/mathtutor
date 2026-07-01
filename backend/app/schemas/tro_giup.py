from pydantic import BaseModel, Field


class TaoYeuCauRequest(BaseModel):
    session_id: int
    noi_dung: str | None = None  # câu hỏi của HS (tùy chọn)


class TraLoiRequest(BaseModel):
    noi_dung: str = Field(..., min_length=1)
