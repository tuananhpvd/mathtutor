import re

from sympy.parsing.latex import parse_latex as _sympy_parse_latex

# LaTeX chuẩn cho phép bỏ ngoặc nhọn quanh \sqrt khi đối số chỉ đúng 1 "token" (1 ký tự hoặc
# 1 lệnh \ten) — vd \sqrt2, \sqrt\alpha, \sqrt[3]2 đều hợp lệ và hiển thị đúng khi biên dịch
# LaTeX thật. NHƯNG parser sympy.parsing.latex (backend antlr) lại BẮT BUỘC phải có {} —
# thiếu ngoặc thì hoặc báo lỗi thẳng ("\sqrt2"), hoặc TỆ HƠN là ÂM THẦM SAI (vd "2\sqrt3" chỉ
# ra "2", mất hẳn phần căn, không báo lỗi gì). Vá bằng cách tự thêm {} quanh đối số bị thiếu
# TRƯỚC khi đưa cho parser — chỉ áp dụng khi CHƯA có ngoặc sẵn.
_RE_SQRT_THIEU_NGOAC = re.compile(r"\\sqrt(\[[^\[\]]*\])?\s*(\\[a-zA-Z]+|[0-9A-Za-z])")


def _them_ngoac_sqrt(latex_str: str) -> str:
    def _boc(m: re.Match) -> str:
        bac = m.group(1) or ""
        doi_so = m.group(2)
        return f"\\sqrt{bac}{{{doi_so}}}"

    return _RE_SQRT_THIEU_NGOAC.sub(_boc, latex_str)


def latex_sang_sympy(latex_str: str) -> str:
    """Chuyển chuỗi LaTeX sang chuỗi SymPy (Python). Ném ValueError nếu lỗi.

    Message KHÔNG kèm chi tiết lỗi ANTLR gốc (dài, kỹ thuật, tiếng Anh, có dấu ^^^ chỉ vị
    trí lỗi) — không phù hợp hiển thị cho GV/HS. Chi tiết vẫn giữ qua "raise ... from e"
    để debug qua traceback khi cần, chỉ ẩn khỏi phần str(exception) hiển thị ra ngoài.
    """
    try:
        expr = _sympy_parse_latex(_them_ngoac_sqrt(latex_str))
        return str(expr)
    except Exception as e:
        raise ValueError(f"Không thể parse LaTeX '{latex_str}'") from e
