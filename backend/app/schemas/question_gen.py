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


class DocDeTuAnhRequest(BaseModel):
    """AI đọc ảnh GV dán, nhận dạng loại câu + trích xuất đề bài/phương án/ý."""
    # Chặn NGOÀI ở tầng request — ngăn payload khổng lồ (hàng chục/trăm MB) tốn RAM giải
    # mã trước khi tới được service. Ngưỡng nghiệp vụ THẬT (5MB ảnh gốc, thông báo rõ
    # ràng bằng tiếng Việt) đã có sẵn ở question_gen_service.doc_de_tu_anh() — 10_000_000
    # ký tự base64 ≈ 7,3MB ảnh gốc, đủ rộng để KHÔNG đụng ngưỡng 5MB đó.
    anh_base64: str = Field(..., min_length=1, max_length=10_000_000)
    mime_type: str = Field(..., description="image/png | image/jpeg | image/webp")
    loai_cau_ky_vong: str = Field(..., description="TN4PA | TNDS | TLN — loại GV đang chọn")


class DocDeTuAnhResponse(BaseModel):
    khop_loai_cau: bool
    loai_cau_nhan_dang: str = ""
    de_bai: str = ""
    meta_nhap: dict = {}
    ly_do_khong_khop: str | None = None
