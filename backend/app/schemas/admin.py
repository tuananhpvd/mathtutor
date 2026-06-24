from pydantic import BaseModel, Field


class TaoTaiKhoanRequest(BaseModel):
    ho_ten: str
    dang_nhap: str
    mat_khau: str = Field(..., min_length=4)
    vai_tro: str = Field(..., description="gv | hs")
    lop_id: int | None = None


class DoiTrangThaiRequest(BaseModel):
    trang_thai: str = Field(..., description="hoat_dong | khoa")


class DatCauHinhRequest(BaseModel):
    khoa: str
    gia_tri: object
