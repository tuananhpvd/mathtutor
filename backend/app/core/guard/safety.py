"""
Lớp lọc nội dung lứa tuổi: chặn ngôn ngữ không phù hợp với học sinh lớp 12.
Không import LLM, không import web framework.

Danh sách từ khóa mặc định dưới đây là NỀN AN TOÀN (dùng khi caller không truyền danh sách
riêng, hoặc khi tầng cấu hình admin gặp lỗi) — Admin quản lý danh sách đang dùng thực tế qua
`app/services/admin_service.py` (lưu trong bảng cấu hình, khởi tạo từ đúng các hằng số này).
Hàm `kiem_tra_an_toan` CHỦ ĐỘNG nhận danh sách từ khóa làm tham số để giữ module này thuần
khiết (không tự đọc DB) — tầng service chịu trách nhiệm nạp danh sách rồi truyền vào.
"""

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class KetQuaAnToan:
    an_toan: bool
    ly_do: str = ""
    # Dấu hiệu khủng hoảng/tự hại — khác hẳn "không phù hợp" thường: caller (tutor_service)
    # KHÔNG được chặn lạnh bằng lỗi, mà phải phản hồi ấm áp + báo GV mức ưu tiên cao nhất.
    khan_cap: bool = False
    # Ngoài phạm vi môn Toán (vd nhờ viết code, dịch bài) — không phải vấn đề an toàn, chỉ
    # cần nhắc nhở nhẹ nhàng, KHÔNG gắn cờ/báo GV như "không phù hợp".
    ngoai_pham_vi: bool = False


# Dấu hiệu khủng hoảng/tự hại — kiểm tra TRƯỚC, ưu tiên cao nhất. Cố tình bắt RỘNG (chấp
# nhận báo động giả, vd "mệt muốn chết" cường điệu) hơn là bỏ lọt một lời kêu cứu thật —
# cái giá của báo động giả (1 câu quan tâm hơi thừa) thấp hơn nhiều so với bỏ lọt.
TU_KHOA_KHAN_CAP_MAC_DINH = [
    "tự tử",
    "tự sát",
    "kết liễu",
    "muốn chết",
    "không muốn sống",
    "hết muốn sống",
    "chán sống",
    "sống làm gì",
    "kết thúc cuộc đời",
    "kết thúc tất cả",
    "kết thúc đời mình",
    "tự làm hại",
    "tự hại",
    "hại bản thân",
    "rạch tay",
    "cắt tay",
    "biến mất mãi mãi",
]

# Từ khoá không phù hợp lứa tuổi (cơ bản; production nên dùng classifier)
TU_KHOA_KHONG_PHU_HOP_MAC_DINH = [
    "kill",
    "hate",
    "ma túy",
    "khiêu dâm",
    "cờ bạc",
    "hack hệ thống",
    "hack server",
    "hack password",
]

# Nội dung NGOÀI phạm vi toán lớp 12
TU_KHOA_NGOAI_PHAM_VI_MAC_DINH = [
    "viết code",
    "tạo code",
    "sinh code",
    "viết chương trình",
    "tạo chương trình",
    "sinh chương trình",
    "viết script",
    "tạo script",
    "sinh script",
    "tra cứu",
    "tra google",
    "tra mạng",
    "hãy dịch",
    "hãy translate",
]


def bo_dau(van_ban: str) -> str:
    """Bỏ dấu tiếng Việt (vd 'tự tử' → 'tu tu') để so khớp không phân biệt dấu — HS gõ
    không dấu ('tu tu', 'muon chet'...) vẫn phải bị phát hiện, không chỉ bản có dấu."""
    s = (van_ban or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _mau_tu_khoa(tu_khoa: str) -> str:
    """Chuyển 1 cụm từ khóa thường (admin nhập, KHÔNG phải regex) thành mẫu so khớp an
    toàn: escape toàn bộ ký tự đặc biệt, chỉ thêm ranh giới từ \\b khi là 1 từ đơn thuần
    chữ/số (vd 'kill' không khớp nhầm bên trong 'skill') — cụm nhiều từ đã đủ đặc trưng
    nhờ khoảng trắng nên không cần ranh giới."""
    sach = re.escape(bo_dau(tu_khoa).strip().lower())
    if re.fullmatch(r"[a-z0-9]+", sach):
        return rf"\b{sach}\b"
    return sach


def _tim_tu_khoa(van_ban_chuan: str, danh_sach: list[str]) -> str | None:
    for tu_khoa in danh_sach:
        if not tu_khoa or not str(tu_khoa).strip():
            continue
        if re.search(_mau_tu_khoa(tu_khoa), van_ban_chuan):
            return tu_khoa
    return None


def kiem_tra_an_toan(
    van_ban: str,
    tu_khoa_khan_cap: list[str] | None = None,
    tu_khoa_khong_phu_hop: list[str] | None = None,
    tu_khoa_ngoai_pham_vi: list[str] | None = None,
) -> KetQuaAnToan:
    """Lọc văn bản HS gửi vào: phát hiện dấu hiệu khủng hoảng/tự hại (ưu tiên cao nhất),
    nội dung không phù hợp, hoặc ngoài phạm vi.

    3 tham số danh sách từ khóa là TÙY CHỌN — bỏ trống thì dùng đúng danh sách mặc định
    (nền an toàn không phụ thuộc DB). Caller thực tế (API/service) nên nạp danh sách đang
    hoạt động từ cấu hình admin (`admin_service.lay_tu_khoa_an_toan`) rồi truyền vào đây.
    """
    van_ban_chuan = bo_dau(van_ban or "").lower()

    tk = _tim_tu_khoa(
        van_ban_chuan,
        tu_khoa_khan_cap if tu_khoa_khan_cap is not None else TU_KHOA_KHAN_CAP_MAC_DINH,
    )
    if tk:
        return KetQuaAnToan(an_toan=False, ly_do=f"Dấu hiệu cần quan tâm: '{tk}'", khan_cap=True)

    tk = _tim_tu_khoa(
        van_ban_chuan,
        tu_khoa_khong_phu_hop if tu_khoa_khong_phu_hop is not None else TU_KHOA_KHONG_PHU_HOP_MAC_DINH,
    )
    if tk:
        return KetQuaAnToan(an_toan=False, ly_do=f"Nội dung không phù hợp: '{tk}'")

    tk = _tim_tu_khoa(
        van_ban_chuan,
        tu_khoa_ngoai_pham_vi if tu_khoa_ngoai_pham_vi is not None else TU_KHOA_NGOAI_PHAM_VI_MAC_DINH,
    )
    if tk:
        return KetQuaAnToan(
            an_toan=False, ly_do=f"Ngoài phạm vi toán lớp 12: '{tk}'", ngoai_pham_vi=True
        )

    return KetQuaAnToan(an_toan=True)
