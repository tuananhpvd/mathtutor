"""
Lớp chốt chặn: phát hiện rò rỉ đáp án trong văn bản gia sư trước khi gửi HS.
Không import LLM, không import web framework.
"""

import re
from dataclasses import dataclass, field
from enum import Enum

from app.core.matching.cas import CheDoSoKhop, KetQuaSoKhop, tuong_duong


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


# Đoạn công thức LaTeX $...$ — quy ước BẮT BUỘC của mọi prompt LLM trong dự án
# (SYSTEM_DIEN_DAT/_QUY_TAC_LATEX): "Mọi công thức/biểu thức toán đặt trong cặp $...$... KHÔNG
# để trần biểu thức ngoài $...$ dù chỉ một biểu thức". Nhờ quy ước này, chỉ cần soi bên trong
# $...$ là đủ bắt được công thức AI viết ra — không cần đoán mò biểu thức trần giữa văn xuôi
# (tránh báo động giả với số/chữ tự nhiên như "bước 2", "x=0" — xem test_chua_gia_tri_dap_an).
_RE_CT_LATEX = re.compile(r"\$([^$]+)\$")

# Nhãn phương án/Đúng-Sai KHÔNG đưa vào so khớp ngữ nghĩa (dù có trong danh sách giá trị cần
# bảo vệ) — sympify("B") ra một SYMBOL tự do, có thể trùng ngẫu nhiên với tên điểm/vectơ trong
# đề hình học (vd đáp án đúng là "B" mà bài có nhắc điểm $B$) → báo động giả. Loại chữ cái đơn
# và "Dung"/"Sai" đã có quy tắc từ khoá ngữ cảnh riêng ("chọn B", "ý a là đúng"...) xử lý đúng
# bản chất của chúng, không cần lớp CAS.
_RE_NHAN_KHONG_PHAI_BIEU_THUC = re.compile(r"^[A-Da-d]$")
_NHAN_LOAI_TRU = {"dung", "sai"}


def _ung_vien_bieu_thuc(van_ban: str) -> list[str]:
    """Trích các đoạn công thức $...$ trong văn bản, tách thêm theo dấu '=' để bắt được cả
    2 vế một phương trình (vd "$3x^2 - 3 = 0$" → thử toàn bộ lẫn từng vế riêng) — vì
    "bieu_thuc_ket_qua" lưu trong CSDL là MỘT vế/biểu thức, không phải phương trình."""
    ung_vien: list[str] = []
    for m in _RE_CT_LATEX.finditer(van_ban):
        doan = m.group(1).strip()
        if not doan:
            continue
        ung_vien.append(doan)
        if "=" in doan:
            ung_vien.extend(p.strip() for p in doan.split("=") if p.strip())
    return ung_vien


def _chua_bieu_thuc_tuong_duong(van_ban: str, cac_gia_tri_chuan: list[str]) -> str | None:
    """Rà các đoạn công thức $...$ trong văn bản có TƯƠNG ĐƯƠNG ĐẠI SỐ với giá trị chuẩn nào
    không — bắt được cả khi AI diễn đạt khác ký hiệu/cú pháp với CSDL (vd CSDL lưu
    "3*x**2 - 3" theo cú pháp SymPy, AI viết "3x^2 - 3" theo LaTeX — so chuỗi trực tiếp
    KHÔNG khớp, nhưng về mặt toán học là MỘT).

    Sự cố thực tế phát hiện trên production (2026-08-03): AI tự đạo hàm rồi thay ký hiệu
    "y'" trong gợi ý bằng chính biểu thức đã tính — đúng bằng bieu_thuc_ket_qua của một bước
    TRƯỚC ĐÓ. Chốt chặn cũ chỉ biết đáp án CUỐI nên không phát hiện được các biểu thức
    trung gian này.

    Dùng LẠI đúng bộ máy CAS đã tin cậy để chấm đáp án HS (app.core.matching.cas), không tự
    viết lại logic so khớp riêng — nhất quán và không tạo thêm một nguồn sự thật thứ hai.
    """
    ung_vien = _ung_vien_bieu_thuc(van_ban)
    if not ung_vien:
        return None
    for chuan in cac_gia_tri_chuan:
        chuan = (chuan or "").strip()
        if not chuan:
            continue
        if _RE_NHAN_KHONG_PHAI_BIEU_THUC.match(chuan) or chuan.lower() in _NHAN_LOAI_TRU:
            continue
        for uv in ung_vien:
            try:
                if tuong_duong(uv, chuan, CheDoSoKhop.tuong_duong) == KetQuaSoKhop.DUNG:
                    return chuan
            except Exception:
                continue
    return None


def kiem_tra_ro_ri(
    van_ban: str,
    gia_tri_dap_an: str | list[str] | None = None,
    loai_cau: str = "TLN",
) -> KetQuaChot:
    """
    Kiểm tra văn bản gia sư có rò rỉ đáp án không.

    gia_tri_dap_an: MỘT giá trị chuẩn, HOẶC danh sách giá trị chuẩn (đáp án cuối + biểu thức
    kết quả của MỌI bước — xem tutor_service._gia_tri_can_bao_ve) để so khớp. Rà theo 2 lớp
    độc lập: (1) khớp chuỗi trực tiếp SAU từ khoá ngữ cảnh ("đáp án là...") và (2) khớp NGỮ
    NGHĨA bằng CAS cho công thức trong cặp $...$ (bắt được cả khi AI viết khác ký hiệu).
    Trả KetQuaChot; nếu ro_ri thì van_ban_thay_the chứa văn bản đã che.
    """
    ly_do = []

    danh_sach_gia_tri = (
        [gia_tri_dap_an] if isinstance(gia_tri_dap_an, str) else list(gia_tri_dap_an or [])
    )
    danh_sach_gia_tri = [g for g in danh_sach_gia_tri if g and str(g).strip()]

    # Lớp 1: khớp chuỗi trực tiếp sau từ khoá ngữ cảnh
    for gia_tri in danh_sach_gia_tri:
        if _chua_gia_tri_dap_an(van_ban, gia_tri):
            ly_do.append(f"Chứa giá trị đáp án chuẩn: '{gia_tri}'")
            break

    # Lớp 2: khớp ngữ nghĩa bằng CAS cho công thức trong $...$
    gia_tri_khop = _chua_bieu_thuc_tuong_duong(van_ban, danh_sach_gia_tri)
    if gia_tri_khop is not None:
        ly_do.append(f"Công thức trong bài tương đương đáp án chuẩn: '{gia_tri_khop}'")

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
