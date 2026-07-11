"""
Lớp lọc nội dung lứa tuổi: chặn ngôn ngữ không phù hợp với học sinh lớp 12.
Không import LLM, không import web framework.
"""

import re
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
_TU_KHOA_KHAN_CAP = [
    r"tự tử",
    r"tự sát",
    r"kết liễu",
    r"muốn chết",
    r"không muốn sống",
    r"hết muốn sống",
    r"chán sống",
    r"sống làm gì",
    r"kết thúc (cuộc đời|tất cả|đời mình)",
    r"tự làm hại",
    r"tự hại",
    r"hại bản thân",
    r"rạch tay",
    r"cắt tay",
    r"biến mất mãi mãi",
]

_RE_KHAN_CAP = [re.compile(p, re.IGNORECASE) for p in _TU_KHOA_KHAN_CAP]

# Từ khoá không phù hợp lứa tuổi (cơ bản; production nên dùng classifier)
_TU_KHOA_KHONG_PHU_HOP = [
    r"\bkill\b",
    r"\bhate\b",
    r"ma túy",
    r"khiêu dâm",
    r"cờ bạc",
    r"hack (hệ thống|server|password)",
]

_RE_UNSAFE = [re.compile(p, re.IGNORECASE) for p in _TU_KHOA_KHONG_PHU_HOP]

# Kiểm tra nội dung NGOÀI phạm vi toán lớp 12
_TU_KHOA_NGOAI_PHAM_VI = [
    r"(viết|tạo|sinh) (code|chương trình|script)",
    r"tra (cứu|google|mạng)",
    r"hãy (dịch|translate)",
]

_RE_NGOAI = [re.compile(p, re.IGNORECASE) for p in _TU_KHOA_NGOAI_PHAM_VI]


def kiem_tra_an_toan(van_ban: str) -> KetQuaAnToan:
    """Lọc văn bản HS gửi vào: phát hiện dấu hiệu khủng hoảng/tự hại (ưu tiên cao nhất),
    nội dung không phù hợp, hoặc ngoài phạm vi."""
    for r in _RE_KHAN_CAP:
        m = r.search(van_ban)
        if m:
            return KetQuaAnToan(
                an_toan=False, ly_do=f"Dấu hiệu cần quan tâm: '{m.group()}'", khan_cap=True
            )

    for r in _RE_UNSAFE:
        m = r.search(van_ban)
        if m:
            return KetQuaAnToan(an_toan=False, ly_do=f"Nội dung không phù hợp: '{m.group()}'")

    for r in _RE_NGOAI:
        m = r.search(van_ban)
        if m:
            return KetQuaAnToan(
                an_toan=False,
                ly_do=f"Ngoài phạm vi toán lớp 12: '{m.group()}'",
                ngoai_pham_vi=True,
            )

    return KetQuaAnToan(an_toan=True)
