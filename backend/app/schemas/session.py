from pydantic import BaseModel


class TaoPhienRequest(BaseModel):
    problem_id: int


class TaoPhienResponse(BaseModel):
    session_id: int
    van_ban: str  # lời mở đầu gia sư
    buoc_hien_tai: int
    loai_cau: str
    y_hien_tai: str | None = None


class GửiTinRequest(BaseModel):
    noi_dung: str = ""
    dap_an_nhap: str | None = None  # TLN/TN4PA: string; TNDS sẽ dùng endpoint riêng
    yeu_cau_goi_y: bool = False


class PhanHoiResponse(BaseModel):
    van_ban: str
    y_dinh: str
    buoc_hien_tai: int
    cap_goi_y: int
    da_xong: bool
    diem: float | None = None
    y_hien_tai: str | None = None
    so_y_dung: int | None = None
    thoi_gian_giay: int | None = None


class TurnResponse(BaseModel):
    vai_tro: str
    noi_dung: str
    dap_an_nhap: str | None = None
    cap_goi_y: int


class ChiTietPhienResponse(BaseModel):
    session_id: int
    problem_id: int
    loai_cau: str
    chuyen_de: str
    dang_ten: str | None = None
    de_bai: str
    meta: dict
    trang_thai: str
    buoc_hien_tai: int
    y_hien_tai: str | None
    trang_thai_y: dict | None
    cap_goi_y_hien_tai: int
    diem: float | None
    thoi_gian_giay: int | None = None
    turns: list[TurnResponse]


class PhienDangDoResponse(BaseModel):
    session_id: int
    problem_id: int
    loai_cau: str
    chuyen_de: str
    de_bai: str
    buoc_hien_tai: int
    y_hien_tai: str | None
    trang_thai_y: dict | None
    cap_goi_y_hien_tai: int
    cap_nhat_luc: str
