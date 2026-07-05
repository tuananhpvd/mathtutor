from pydantic import BaseModel, Field


class BuocGoiYSpec(BaseModel):
    """1 bước trong cấu trúc GV yêu cầu — pham_vi: 'ca_bai' (TN4PA/TLN) hoặc 'a'/'b'/'c'/'d'
    (TNDS, tương ứng 4 ý). so_goi_y: số gợi ý leo thang AI phải viết cho đúng bước này."""
    pham_vi: str = "ca_bai"
    so_goi_y: int = Field(..., ge=1, le=8)


class TaoBuocGoiYRequest(BaseModel):
    """AI tạo bước và gợi ý (GV viết đề bài, AI chỉ giải + chia bước + viết gợi ý)."""
    dang_id: int
    loai_cau: str = Field(..., description="TN4PA | TNDS | TLN")
    do_kho: str = Field("tb", description="de | tb | kho")
    de_bai: str = Field(..., min_length=1)
    meta_nhap: dict = Field(default_factory=dict)  # phương án (TN4PA) / 4 ý (TNDS) GV đã viết
    cau_truc_buoc: list[BuocGoiYSpec] = Field(..., min_length=1, max_length=8)


class LuuBuocGoiYRequest(BaseModel):
    cau: dict


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
