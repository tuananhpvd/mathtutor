from pydantic import BaseModel, Field


class TaoTaiKhoanRequest(BaseModel):
    ho_ten: str
    dang_nhap: str
    # Chuẩn mật khẩu tối thiểu 6 ký tự (áp dụng CHO MỌI schema tạo/sửa/import tài khoản +
    # đổi hồ sơ ở admin/gv/hs) — tài khoản GV/quản lý dùng "1234" quá yếu dù đã có throttle
    # chống dò. Chỉ ràng buộc lúc TẠO MỚI/ĐỔI; mật khẩu cũ đã hash không bị ảnh hưởng, và
    # LoginRequest KHÔNG áp min để mật khẩu seed/cũ ngắn hơn vẫn đăng nhập được.
    mat_khau: str = Field(..., min_length=6)
    vai_tro: str = Field(..., description="gv | hs")
    lop_id: int | None = None


class DoiTrangThaiRequest(BaseModel):
    trang_thai: str = Field(..., description="hoat_dong | khoa")


class GanLopRequest(BaseModel):
    lop_id: int | None = None


class SuaTaiKhoanRequest(BaseModel):
    ho_ten: str | None = None
    dang_nhap: str | None = None
    mat_khau: str | None = Field(None, min_length=6)
    vai_tro: str | None = None  # gv | hs


class HoSoUpdate(BaseModel):
    """Admin TỰ sửa hồ sơ của chính mình — khác SuaTaiKhoanRequest (admin sửa tài khoản
    GV/HS người khác, chặn không cho áp dụng lên tài khoản admin, xem admin_service.sua_tai_khoan)."""
    ho_ten: str | None = None
    mat_khau: str | None = Field(None, min_length=6)


class TaoLopRequest(BaseModel):
    ten: str = Field(..., min_length=1)
    gv_id: int | None = None


class SuaLopRequest(BaseModel):
    ten: str | None = None
    gv_id: int | None = None


class DatCauHinhRequest(BaseModel):
    khoa: str
    gia_tri: object


class KiemTraDangNhapRequest(BaseModel):
    dang_nhaps: list[str] = Field(..., min_length=1)


class KiemTraTuKhoaRequest(BaseModel):
    van_ban: str


class TaiKhoanImportItem(BaseModel):
    ho_ten: str = Field(..., min_length=1)
    dang_nhap: str = Field(..., min_length=1)
    mat_khau: str = Field(..., min_length=6)
    vai_tro: str = Field(..., description="gv | hs")


class ImportTaiKhoanRequest(BaseModel):
    # max_length: chặn batch khổng lồ tốn RAM/CPU không giới hạn — 2000 đủ rộng cho cả 1
    # trường (nhiều lớp) nhập cùng lúc.
    tai_khoans: list[TaiKhoanImportItem] = Field(..., min_length=1, max_length=2000)
