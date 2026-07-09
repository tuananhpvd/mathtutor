from sympy.parsing.latex import parse_latex as _sympy_parse_latex


def latex_sang_sympy(latex_str: str) -> str:
    """Chuyển chuỗi LaTeX sang chuỗi SymPy (Python). Ném ValueError nếu lỗi.

    Message KHÔNG kèm chi tiết lỗi ANTLR gốc (dài, kỹ thuật, tiếng Anh, có dấu ^^^ chỉ vị
    trí lỗi) — không phù hợp hiển thị cho GV/HS. Chi tiết vẫn giữ qua "raise ... from e"
    để debug qua traceback khi cần, chỉ ẩn khỏi phần str(exception) hiển thị ra ngoài.
    """
    try:
        expr = _sympy_parse_latex(latex_str)
        return str(expr)
    except Exception as e:
        raise ValueError(f"Không thể parse LaTeX '{latex_str}'") from e
