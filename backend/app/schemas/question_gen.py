from pydantic import BaseModel, Field


class SinhCauHoiRequest(BaseModel):
    chuyen_de: str
    dang_id: int | None = None  # gắn câu hỏi sinh ra vào một dạng cụ thể
    loai_cau: str = Field(..., description="TN4PA | TNDS | TLN")
    do_kho: str = Field("tb", description="de | tb | kho")
    so_luong: int = Field(1, ge=1, le=10)
    tai_lieu: str | None = None


class CauHoiNhapResponse(BaseModel):
    id: int
    loai_cau: str
    do_kho: str
    chuyen_de: str = ""
    de_bai: str
    meta: dict = {}
    trang_thai_duyet: str
    canh_bao: list[str]


class DuyetRequest(BaseModel):
    hanh_dong: str = Field("duyet", description="duyet | loai")
