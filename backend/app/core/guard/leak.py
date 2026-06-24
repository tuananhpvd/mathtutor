"""
Lớp chốt chặn: phát hiện rò rỉ đáp án trong văn bản gia sư trước khi gửi HS.
Không import LLM, không import web framework.
"""

import re
from dataclasses import dataclass, field
from enum import Enum


class MucDoRoRi(str, Enum):
    sach = "sach"
    nghi_ngo = "nghi_ngo"
    ro_ri = "ro_ri"


@dataclass
class KetQuaChot:
    muc_do: MucDoRoRi
    ly_do: list[str] = field(default_factory=list)
    van_ban_goc: str = ""
    van_ban_thay_the: str = ""  # văn bản đã che nếu cần


# ---------- Từ khoá chốt chặn ----------

_TU_KHOA_LO_DAP_AN = [
    r"đáp án (là|:)",
    r"kết quả (là|:)",
    r"đáp số (là|:)",
    r"answer is",
    r"the answer",
    # "= số" chỉ phát hiện khi đứng trước từ khoá kết quả, tránh false-positive trong biểu thức toán
    r"(đáp án|kết quả|answer|result)\s*=\s*[0-9\-\+\/\.\,]+",
    r"(đáp án|kết quả)\s+bằng\s+[0-9\-\+\/\.\,]+",
    r"chọn [A-D]\b",                 # TN4PA: "chọn B"
    r"phương án [A-D]\b",
    r"ý (a|b|c|d) (là đúng|là sai|đúng|sai)\b",
]

_TU_KHOA_NGHI_NGO = [
    r"vì (kết quả|đáp án)",
    r"ta (tính|có) (được|ra)",
    r"suy ra (được)?[^.]*=",
]

_RE_LO = [re.compile(p, re.IGNORECASE) for p in _TU_KHOA_LO_DAP_AN]
_RE_NGO = [re.compile(p, re.IGNORECASE) for p in _TU_KHOA_NGHI_NGO]


_RE_CONTEXT_LEAK = re.compile(
    r"(đáp án|kết quả|đáp số|answer|result|là|bằng)\s*[=:]?\s*",
    re.IGNORECASE,
)


def _chua_gia_tri_dap_an(van_ban: str, gia_tri: str) -> bool:
    """Phát hiện giá trị đáp án xuất hiện SAU từ khoá kết quả.

    Chỉ báo rò rỉ khi giá trị nằm ngay sau "đáp án / kết quả / là / bằng / = ..."
    tránh false-positive với số xuất hiện tự nhiên trong biểu thức toán (x=0, bước 1, ...).
    """
    if not gia_tri or not gia_tri.strip():
        return False
    gv = gia_tri.strip()
    pattern = _RE_CONTEXT_LEAK.pattern + re.escape(gv) + r'(?![0-9a-zA-Z])'
    return bool(re.search(pattern, van_ban, re.IGNORECASE))


def kiem_tra_ro_ri(
    van_ban: str,
    gia_tri_dap_an: str | None = None,
    loai_cau: str = "TLN",
) -> KetQuaChot:
    """
    Kiểm tra văn bản gia sư có rò rỉ đáp án không.

    gia_tri_dap_an: giá trị chuẩn (dap_an_cuoi / dap_an_dung / ký hiệu ý) để so khớp trực tiếp.
    Trả KetQuaChot; nếu ro_ri thì van_ban_thay_the chứa văn bản đã che.
    """
    ly_do = []

    # Kiểm tra chứa giá trị đáp án chuẩn
    if gia_tri_dap_an and _chua_gia_tri_dap_an(van_ban, gia_tri_dap_an):
        ly_do.append(f"Chứa giá trị đáp án chuẩn: '{gia_tri_dap_an}'")

    # Kiểm tra từ khoá rò rỉ rõ ràng
    for r in _RE_LO:
        m = r.search(van_ban)
        if m:
            ly_do.append(f"Cụm từ rò rỉ: '{m.group()}'")

    if ly_do:
        van_ban_che = "[Nội dung bị lọc — có thể chứa đáp án]"
        return KetQuaChot(
            muc_do=MucDoRoRi.ro_ri,
            ly_do=ly_do,
            van_ban_goc=van_ban,
            van_ban_thay_the=van_ban_che,
        )

    # Nghi ngờ
    for r in _RE_NGO:
        m = r.search(van_ban)
        if m:
            ly_do.append(f"Nghi ngờ rò rỉ: '{m.group()}'")

    muc = MucDoRoRi.nghi_ngo if ly_do else MucDoRoRi.sach
    return KetQuaChot(muc_do=muc, ly_do=ly_do, van_ban_goc=van_ban, van_ban_thay_the=van_ban)
