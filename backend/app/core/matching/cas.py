import re
from enum import Enum

from sympy import simplify, sympify
from sympy.core.sympify import SympifyError


class CheDoSoKhop(str, Enum):
    tuong_duong = "tuong_duong"
    dung_dang = "dung_dang"


class KetQuaSoKhop(str, Enum):
    DUNG = "DUNG"
    SAI = "SAI"
    KHONG_PHAN_TICH_DUOC = "KHONG_PHAN_TICH_DUOC"


_FORBIDDEN = ("__import__", "eval", "exec", "open", "os", "sys", "subprocess")

# Chuẩn hóa ký hiệu tổ hợp/chỉnh hợp quen dùng (SGK VN + tên hàm LLM hay bịa) về hàm
# SymPy thật: C(n,k)/comb/combinations → binomial; A(n,k)/perm/permutations → ff
# (falling factorial, đúng bằng chỉnh hợp n!/(n-k)!). Chỉ khớp dạng GỌI HÀM `tên(`
# có ranh giới từ — không đụng vào tên biến khác.
_ALIAS_TO_HOP = [
    (re.compile(r"\b(?:combinations?|comb|nCr|C)\s*\("), "binomial("),
    (re.compile(r"\b(?:permutations?|perm|nPr|A)\s*\("), "ff("),
]


def _chuan_hoa_to_hop(s: str) -> str:
    for mau, thay in _ALIAS_TO_HOP:
        s = mau.sub(thay, s)
    return s


def _safe_sympify(expr_str: str):
    if any(w in expr_str for w in _FORBIDDEN):
        raise ValueError(f"Biểu thức không an toàn: {expr_str!r}")
    try:
        return sympify(_chuan_hoa_to_hop(expr_str), evaluate=True)
    except (SympifyError, SyntaxError, TypeError, ValueError) as e:
        raise ValueError(str(e)) from e


def _chuan_hoa_latex(s: str) -> str:
    """Chuẩn hóa vài ký hiệu nhân của editor (MathLive) về dạng parse_latex hiểu."""
    return s.replace("\\star", "\\cdot").replace("\\ast", "\\cdot")


# Dấu hiệu chuỗi là công thức LaTeX/toán (cần parse_latex), KHÔNG phải chữ thường.
# Tránh biến văn bản tự do (vd "hai muoi") thành tích các biến h*a*i*...
_RE_DAU_HIEU_LATEX = re.compile(r"[\\^{}]|\d\s*[a-zA-Z]|[a-zA-Z]\s*\d")


def _co_dau_hieu_latex(s: str) -> bool:
    return bool(_RE_DAU_HIEU_LATEX.search(s))


def _parse_an_toan(expr_str: str):
    """Parse linh hoạt: thử cú pháp SymPy trước, nếu hỏng thử LaTeX (đầu vào từ editor).

    Cho phép HS nhập qua editor công thức (LaTeX, vd '3x^2-3', '\\frac{1}{2}') lẫn
    cú pháp SymPy thuần ('3*x**2-3'). Chỉ thử LaTeX khi chuỗi CÓ dấu hiệu công thức,
    để văn bản thường (vd 'hai muoi') vẫn trả KHÔNG_PHÂN_TÍCH_ĐƯỢC.
    Ném ValueError nếu cả hai đều không parse được.
    """
    if any(w in expr_str for w in _FORBIDDEN):
        raise ValueError(f"Biểu thức không an toàn: {expr_str!r}")
    try:
        return sympify(_chuan_hoa_to_hop(expr_str), evaluate=True)
    except (SympifyError, SyntaxError, TypeError, ValueError):
        pass
    if not _co_dau_hieu_latex(expr_str):
        raise ValueError(f"Không parse được biểu thức: {expr_str!r}")
    # Thử như LaTeX (parse_latex hỗ trợ nhân ngầm '3x', '^', '\\frac', '\\sqrt'...)
    from app.core.matching.latex import latex_sang_sympy

    sympy_str = latex_sang_sympy(_chuan_hoa_latex(expr_str))  # ném ValueError nếu hỏng
    return _safe_sympify(sympy_str)


def parse_bieu_thuc_an_toan(expr_str: str):
    """Parse biểu thức toán (cú pháp SymPy hoặc LaTeX) an toàn, ném ValueError nếu hỏng.

    Public wrapper của _parse_an_toan — dùng chung cho so khớp đáp án và các tiện ích
    khác cần CAS (vd vẽ đồ thị) mà không phải chấm điểm HS.
    """
    return _parse_an_toan(expr_str)


def kiem_tra_bieu_thuc(expr_str: str) -> bool:
    """True nếu biểu thức parse được an toàn bằng SymPy. Dùng để validate AI sinh."""
    if not expr_str or not str(expr_str).strip():
        return True  # bước không có biểu thức kết quả → hợp lệ
    try:
        _safe_sympify(str(expr_str))
        return True
    except ValueError:
        return False


def tuong_duong(
    hs: str,
    chuan: str,
    che_do: CheDoSoKhop = CheDoSoKhop.tuong_duong,
    lam_tron: int | None = None,
) -> KetQuaSoKhop:
    try:
        expr_hs = _parse_an_toan(hs)
        expr_chuan = _parse_an_toan(chuan)
    except ValueError:
        return KetQuaSoKhop.KHONG_PHAN_TICH_DUOC

    if che_do == CheDoSoKhop.dung_dang:
        # So sánh cấu trúc cú pháp, không rút gọn
        return KetQuaSoKhop.DUNG if expr_hs == expr_chuan else KetQuaSoKhop.SAI

    # che_do == tuong_duong: chấp nhận mọi dạng tương đương
    try:
        if lam_tron is not None:
            val_hs = float(expr_hs.evalf())
            val_chuan = float(expr_chuan.evalf())
            eq = round(val_hs, lam_tron) == round(val_chuan, lam_tron)
        else:
            diff = simplify(expr_hs - expr_chuan)
            eq = diff == 0
        return KetQuaSoKhop.DUNG if eq else KetQuaSoKhop.SAI
    except Exception:
        return KetQuaSoKhop.KHONG_PHAN_TICH_DUOC
