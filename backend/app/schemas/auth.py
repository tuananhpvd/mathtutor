from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    dang_nhap: str
    mat_khau: str


class DangKyBangMaRequest(BaseModel):
    """HS tự đăng ký bằng mã lớp.

    KHÔNG có trường `vai_tro`/`lop_id`: vai trò luôn cứng là `hs` và lớp lấy từ mã — client
    không được phép tự khai (chặn leo thang đặc quyền qua endpoint công khai).
    """
    ma: str = Field(..., min_length=1, max_length=32)
    ho_ten: str = Field(..., min_length=1, max_length=100)
    dang_nhap: str = Field(..., min_length=3, max_length=50)
    mat_khau: str = Field(..., min_length=6)  # cùng chuẩn với các luồng đổi mật khẩu khác


class LopTuMaResponse(BaseModel):
    """Xem trước lớp ứng với mã — để HS xác nhận đúng lớp trước khi tạo tài khoản."""
    lop_ten: str
    gv_ten: str | None = None
    ma_het_han: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vai_tro: str
    ho_ten: str
    la_quan_ly: bool = False
