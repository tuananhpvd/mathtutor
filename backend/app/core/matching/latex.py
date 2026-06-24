from sympy.parsing.latex import parse_latex as _sympy_parse_latex


def latex_sang_sympy(latex_str: str) -> str:
    """Chuyển chuỗi LaTeX sang chuỗi SymPy (Python). Ném ValueError nếu lỗi."""
    try:
        expr = _sympy_parse_latex(latex_str)
        return str(expr)
    except Exception as e:
        raise ValueError(f"Không thể parse LaTeX '{latex_str}': {e}") from e
