from dataclasses import dataclass, field


@dataclass
class ChiThi:
    """Chỉ thị sư phạm từ orchestrator → LLM diễn đạt."""

    loai_cau: str
    y_dinh: str  # dinh_huong | xac_nhan_dung | hoi_nguoc | goi_y | chuyen_y | tom_tat | ket_thuc
    buoc: int
    y_dang_xet: str | None  # TNDS: ký hiệu ý (a/b/c/d); None với TN4PA/TLN
    cap_goi_y: int
    y_goi_y: str  # Ý CHÍNH cho LLM làm la bàn (không phải lời thoại)
    ngu_canh_hs: str  # điều HS vừa nói
    rang_buoc: str = field(
        default="khong_duoc_neu_ket_qua_dap_an_dung_sai"
    )

    def to_dict(self) -> dict:
        return {
            "loai_cau": self.loai_cau,
            "y_dinh": self.y_dinh,
            "buoc": self.buoc,
            "y_dang_xet": self.y_dang_xet,
            "cap_goi_y": self.cap_goi_y,
            "y_goi_y": self.y_goi_y,
            "ngu_canh_hs": self.ngu_canh_hs,
            "rang_buoc": self.rang_buoc,
        }
