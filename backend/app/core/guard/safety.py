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


# Từ khoá không phù hợp lứa tuổi (cơ bản; production nên dùng classifier)
_TU_KHOA_KHONG_PHU_HOP = [
    r"\bkill\b",
    r"\bhate\b",
    r"tự tử",
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
    """Lọc văn bản HS gửi vào: phát hiện nội dung không phù hợp hoặc ngoài phạm vi."""
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
            )

    return KetQuaAnToan(an_toan=True)
