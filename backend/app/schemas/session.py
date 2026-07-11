from pydantic import BaseModel


class TaoPhienRequest(BaseModel):
    problem_id: int


class TaoPhienResponse(BaseModel):
    session_id: int
    van_ban: str  # lời mở đầu gia sư
    buoc_hien_tai: int
    loai_cau: str
    y_hien_tai: str | None = None
    buoc_mo_ta: str | None = None   # mô tả bước hiện tại (TLN/TN4PA)
    tong_buoc: int | None = None    # tổng số bước
    cho_chon_dap_an: bool | None = None  # TN4PA: đã mở khóa cho chọn A/B/C/D chưa
    cho_chon_dung_sai: bool | None = None  # TNDS: đã mở khóa cho chốt Đúng/Sai ý hiện tại chưa
    so_goi_y_toi_da: int | None = None  # số gợi ý tối đa của bước/ý hiện tại (FE hiện "x/y")


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
    buoc_mo_ta: str | None = None   # mô tả bước mới (sau khi bước chuyển)
    tong_buoc: int | None = None
    cho_chon_dap_an: bool | None = None  # TN4PA: đã mở khóa cho chọn A/B/C/D chưa
    cho_chon_dung_sai: bool | None = None  # TNDS: đã mở khóa cho chốt Đúng/Sai ý hiện tại
    thoi_gian_y: dict | None = None       # TNDS: thời gian (giây) từng ý đã hoàn thành
    dap_an_y: dict | None = None          # TNDS: đáp án đúng từng ý — CHỈ gửi khi đã hoàn thành
    so_goi_y_toi_da: int | None = None    # số gợi ý tối đa của bước/ý hiện tại
    so_lan_khong_hieu: int | None = None  # số lần xin gợi ý/không hiểu CẢ PHIÊN
    tong_so_lan_sai: int | None = None    # số lần trả lời sai CẢ PHIÊN


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
    hinh_anh: str | None = None
    meta: dict
    trang_thai: str
    buoc_hien_tai: int
    y_hien_tai: str | None
    trang_thai_y: dict | None
    cap_goi_y_hien_tai: int
    diem: float | None
    thoi_gian_giay: int | None = None
    buoc_mo_ta: str | None = None
    tong_buoc: int | None = None
    cho_chon_dap_an: bool | None = None
    cho_chon_dung_sai: bool | None = None
    thoi_gian_y: dict | None = None
    dap_an_y: dict | None = None
    so_goi_y_toi_da: int | None = None
    so_lan_khong_hieu: int | None = None
    tong_so_lan_sai: int | None = None
    turns: list[TurnResponse]


class PhienDangDoResponse(BaseModel):
    session_id: int
    problem_id: int
    loai_cau: str
    chuyen_de: str
    dang_ten: str | None = None
    de_bai: str
    buoc_hien_tai: int
    y_hien_tai: str | None
    trang_thai_y: dict | None
    cap_goi_y_hien_tai: int
    cap_nhat_luc: str
