from pydantic import BaseModel, Field


class SolutionStepIn(BaseModel):
    thu_tu: int = 1
    pham_vi: str = "ca_bai"
    mo_ta: str = ""
    bieu_thuc_ket_qua: str = ""
    danh_sach_goi_y: list[str] = Field(default_factory=list)


class ProblemCreate(BaseModel):
    """Tạo câu hỏi mới (GV/Admin). loai_dap_an_nhap suy ra từ loai_cau ở service."""

    loai_cau: str  # TN4PA | TNDS | TLN
    do_kho: str = "tb"  # de | tb | kho
    dang_id: int | None = None
    chuyen_de: str | None = Field(None, max_length=200)
    de_bai: str = Field(..., min_length=1)
    che_do_so_khop: str = "tuong_duong"
    meta: dict = Field(default_factory=dict)
    solution_steps: list[SolutionStepIn] = Field(default_factory=list)


class ProblemUpdate(BaseModel):
    """Cập nhật câu hỏi (GV/Admin). Mọi trường tùy chọn; chỉ áp dụng trường được gửi.

    Dùng model_dump(exclude_unset=True) để phân biệt "không gửi" với "đặt rỗng".
    """

    chuyen_de: str | None = Field(None, min_length=1, max_length=200)
    dang_id: int | None = None
    do_kho: str | None = None  # de | tb | kho
    de_bai: str | None = Field(None, min_length=1)
    meta: dict | None = None
    solution_steps: list[SolutionStepIn] | None = None
    trang_thai_duyet: str | None = None  # cho_duyet | da_duyet | loai
