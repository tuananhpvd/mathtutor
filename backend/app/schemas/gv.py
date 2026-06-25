from pydantic import BaseModel, Field


class HoSoUpdate(BaseModel):
    ho_ten: str | None = None
    mat_khau: str | None = Field(None, min_length=4)


class TaoLopGVRequest(BaseModel):
    ten: str = Field(..., min_length=1)


class SuaLopGVRequest(BaseModel):
    ten: str = Field(..., min_length=1)


class TaoHocSinhRequest(BaseModel):
    ho_ten: str = Field(..., min_length=1)
    dang_nhap: str = Field(..., min_length=1)
    mat_khau: str = Field(..., min_length=4)
    lop_id: int


class SuaHocSinhRequest(BaseModel):
    ho_ten: str | None = None
    dang_nhap: str | None = None
    mat_khau: str | None = Field(None, min_length=4)


class GanLopRequest(BaseModel):
    lop_id: int


class DoiTrangThaiRequest(BaseModel):
    trang_thai: str = Field(..., description="hoat_dong | khoa")
