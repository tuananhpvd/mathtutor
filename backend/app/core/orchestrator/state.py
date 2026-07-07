from dataclasses import dataclass, field


@dataclass
class TrangThaiPhien:
    """Trạng thái hiện tại của một phiên học."""

    loai_cau: str
    buoc_hien_tai: int = 1
    y_hien_tai: str | None = None          # TNDS: ký hiệu ý đang xét
    trang_thai_y: dict = field(default_factory=dict)  # TNDS: {a: xong, b: dang_lam, ...}
    cap_goi_y_hien_tai: int = 0
    so_lan_sai_lien_tiep: int = 0
    so_lan_khong_hieu: int = 0
    so_y_dung: int = 0       # TNDS: số ý trả lời đúng (để tính điểm bậc thang)
    da_suy_luan: bool = False  # TN4PA/TNDS: đã suy luận đúng cho ý/bước hiện tại chưa
    da_xong: bool = False

    # danh sách bước (list[SolutionStep-like dict])
    steps: list = field(default_factory=list)
    # Đề bài (rút gọn) — CHỈ để làm ngữ cảnh cho LLM diễn đạt bám đúng chủ đề, orchestrator
    # KHÔNG dùng để quyết định logic chuyển trạng thái.
    de_bai: str = ""

    def buoc_data(self) -> dict | None:
        """Lấy step dict phù hợp với buoc_hien_tai và y_hien_tai."""
        for s in self.steps:
            if s["thu_tu"] == self.buoc_hien_tai:
                if self.loai_cau == "TNDS":
                    if s.get("pham_vi") == self.y_hien_tai:
                        return s
                else:
                    return s
        return None

    def so_goi_y_buoc(self) -> int:
        """Số gợi ý của bước hiện tại (đọc từ danh_sach_goi_y thực tế)."""
        d = self.buoc_data()
        if d is None:
            return 1
        return len(d.get("danh_sach_goi_y", ["..."]))
