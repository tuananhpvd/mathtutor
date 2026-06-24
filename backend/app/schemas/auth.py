from pydantic import BaseModel


class LoginRequest(BaseModel):
    dang_nhap: str
    mat_khau: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vai_tro: str
    ho_ten: str
