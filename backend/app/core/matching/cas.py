import re
from enum import Enum

from sympy import Matrix, simplify, sympify
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


# Dấu hiệu chuỗi là công thức LaTeX/toán (cần parse_latex), KHÔNG phải chữ thường.
# Tránh biến văn bản tự do (vd "hai muoi") thành tích các biến h*a*i*...
_RE_DAU_HIEU_LATEX = re.compile(r"[\\^{}]|\d\s*[a-zA-Z]|[a-zA-Z]\s*\d")


def _co_dau_hieu_latex(s: str) -> bool:
    return bool(_RE_DAU_HIEU_LATEX.search(s))


# Tọa độ/vectơ kiểu SGK VN "(a; b; c)" — dấu ";" ngăn cách thành phần (≥2), CÙNG quy ước
# dấu ";" đã dùng cho khoảng "(-\infty; 1)" trong toàn app. sympify thuần KHÔNG hiểu ";"
# (lỗi ngay) và hiểu NHẦM dấu "," thành cú pháp tuple Python (vd "1,5" → (1, 5) thay vì số
# 1.5) — nên phải tách theo ";" rồi tự thay "," → "." (thập phân kiểu VN) trong TỪNG thành
# phần trước khi sympify riêng lẻ, thay vì sympify cả chuỗi một lần.
_RE_VECTO = re.compile(r"^\((.+;.+)\)$")
_RE_PHAY_THAP_PHAN = re.compile(r"(?<=\d),(?=\d)")


def _thu_parse_vecto(expr_str: str):
    """Parse "(a; b; c)" (≥2 thành phần) thành sympy.Matrix (vectơ cột). Trả None nếu
    chuỗi không khớp dạng này hoặc có thành phần không parse được (KHÔNG ném lỗi — để
    _parse_an_toan tự thử các cách khác)."""
    m = _RE_VECTO.match(expr_str.strip())
    if not m:
        return None
    thanh_phan = [p.strip() for p in m.group(1).split(";")]
    if not all(thanh_phan):
        return None
    try:
        gia_tri = [_safe_sympify(_RE_PHAY_THAP_PHAN.sub(".", p)) for p in thanh_phan]
    except ValueError:
        return None
    return Matrix(gia_tri)


def _parse_an_toan(expr_str: str):
    """Parse linh hoạt: thử vectơ "(a; b; c)" → cú pháp SymPy → LaTeX (đầu vào từ editor).

    Cho phép HS nhập qua editor công thức (LaTeX, vd '3x^2-3', '\\frac{1}{2}') lẫn
    cú pháp SymPy thuần ('3*x**2-3') lẫn tọa độ/vectơ kiểu SGK ('(4; 4; -2)'). Chỉ thử
    LaTeX khi chuỗi CÓ dấu hiệu công thức, để văn bản thường (vd 'hai muoi') vẫn trả
    KHÔNG_PHÂN_TÍCH_ĐƯỢC. Ném ValueError nếu không cách nào parse được.
    """
    if any(w in expr_str for w in _FORBIDDEN):
        raise ValueError(f"Biểu thức không an toàn: {expr_str!r}")
    vecto = _thu_parse_vecto(expr_str)
    if vecto is not None:
        return vecto
    try:
        return sympify(_chuan_hoa_to_hop(expr_str), evaluate=True)
    except (SympifyError, SyntaxError, TypeError, ValueError):
        pass
    if not _co_dau_hieu_latex(expr_str):
        raise ValueError(f"Không parse được biểu thức: {expr_str!r}")
    # Thử như LaTeX (parse_latex hỗ trợ nhân ngầm '3x', '^', '\\frac', '\\sqrt'...)
    from app.core.matching.latex import latex_sang_sympy

    # Mọi chuẩn hóa LaTeX (bao gồm \star/\ast → \cdot) nằm chung trong latex_sang_sympy(),
    # dùng chung với ô "chuyển đổi công thức" của GV — sửa 1 chỗ, cả 2 nơi cùng được lợi.
    sympy_str = latex_sang_sympy(expr_str)  # ném ValueError nếu hỏng
    return _safe_sympify(sympy_str)


def parse_bieu_thuc_an_toan(expr_str: str):
    """Parse biểu thức toán (cú pháp SymPy hoặc LaTeX) an toàn, ném ValueError nếu hỏng.

    Public wrapper của _parse_an_toan — dùng chung cho so khớp đáp án và các tiện ích
    khác cần CAS (vd vẽ đồ thị) mà không phải chấm điểm HS.
    """
    return _parse_an_toan(expr_str)


def kiem_tra_bieu_thuc(expr_str: str) -> bool:
    """True nếu biểu thức parse được an toàn bằng SymPy — HOẶC đúng dạng tọa độ/vectơ
    kiểu SGK VN "(a; b; c)" (xem _thu_parse_vecto). Dùng để validate AI sinh."""
    if not expr_str or not str(expr_str).strip():
        return True  # bước không có biểu thức kết quả → hợp lệ
    s = str(expr_str)
    if _thu_parse_vecto(s) is not None:
        return True
    try:
        _safe_sympify(s)
        return True
    except ValueError:
        return False


def buoc_co_bieu_thuc_khong_hop_le(steps: list[dict]) -> list[str]:
    """Trả mô tả các bước có "bieu_thuc_ket_qua" KHÔNG parse được (rỗng = tất cả hợp lệ).

    Dùng làm điều kiện CHẶN LƯU (khác các cảnh báo trình bày khác chỉ nhắc GV tự kiểm) —
    một "bieu_thuc_ket_qua" hỏng (vd còn sót "$...$" do AI quên bỏ, dù prompt đã dặn field
    này KHÔNG bọc $) khiến CAS KHÔNG BAO GIỜ so khớp đúng được cho bước đó, kể cả khi học
    sinh nhập đúng tuyệt đối — lỗi âm thầm, chỉ lộ ra khi HS làm bài thật."""
    loi: list[str] = []
    for s in steps or []:
        if not isinstance(s, dict):
            continue
        bt = s.get("bieu_thuc_ket_qua", "")
        if not kiem_tra_bieu_thuc(bt):
            loi.append(
                f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): bieu_thuc_ket_qua {bt!r} "
                "không parse được — CAS sẽ không bao giờ chấm đúng được bước này, kể cả khi "
                "học sinh nhập đúng. Hãy sửa lại (vd bỏ dấu $, viết cú pháp SymPy thuần)."
            )
    return loi


def _la_khong(diff) -> bool:
    """True nếu diff là 0 (số) hay ma trận-0 (vectơ) — Matrix không bao giờ "== 0" trực
    tiếp trong SymPy (khác số thường), phải hỏi riêng is_zero_matrix."""
    is_zero_matrix = getattr(diff, "is_zero_matrix", None)
    if is_zero_matrix is not None:
        return bool(is_zero_matrix)
    return diff == 0


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

    # che_do == tuong_duong: chấp nhận mọi dạng tương đương (vd vectơ viết khác thứ tự
    # thành phần vẫn tính KHÁC — vị trí có ý nghĩa — nhưng mỗi thành phần được rút gọn/
    # tính toán như biểu thức số bình thường, vd "(2+2; 4; -2)" == "(4; 4; -2)")
    try:
        if lam_tron is not None:
            val_hs = float(expr_hs.evalf())
            val_chuan = float(expr_chuan.evalf())
            eq = round(val_hs, lam_tron) == round(val_chuan, lam_tron)
        else:
            diff = simplify(expr_hs - expr_chuan)
            eq = _la_khong(diff)
        return KetQuaSoKhop.DUNG if eq else KetQuaSoKhop.SAI
    except Exception:
        return KetQuaSoKhop.KHONG_PHAN_TICH_DUOC
