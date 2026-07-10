import pytest

from app.core.matching.latex import latex_sang_sympy


def test_frac():
    result = latex_sang_sympy(r"\frac{x^2-1}{2}")
    # Kết quả là biểu thức SymPy dạng chuỗi, phải parseable và đúng giá trị
    from sympy import simplify, sympify
    expr = sympify(result)
    expected = sympify("(x**2 - 1) / 2")
    assert simplify(expr - expected) == 0


def test_sqrt():
    result = latex_sang_sympy(r"\sqrt{2}")
    from sympy import sqrt, sympify
    assert sympify(result) == sqrt(2)


def test_sqrt_thieu_ngoac_nhon():
    """LaTeX chuẩn cho phép bỏ {} khi đối số \\sqrt chỉ 1 ký tự (vd \\sqrt2) — nhưng
    parser antlr của sympy bắt buộc phải có {}, trước đây báo lỗi thẳng thừng."""
    from sympy import sqrt, sympify
    assert sympify(latex_sang_sympy(r"\sqrt2")) == sqrt(2)
    assert sympify(latex_sang_sympy(r"\sqrt 2")) == sqrt(2)


def test_sqrt_bac_n_thieu_ngoac_nhon():
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"\sqrt[3]2")) == sympify("2**(1/3)")


def test_sqrt_thieu_ngoac_khong_am_tham_sai():
    """Hồi quy: trước khi vá, "2\\sqrt3" bị parser ANTLR ÂM THẦM cắt cụt thành "2" (mất hẳn
    phần căn, KHÔNG báo lỗi gì) — nguy hiểm hơn cả báo lỗi thẳng vì không ai phát hiện ra."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"2\sqrt3")) == sympify("2*sqrt(3)")


def test_latex_hong():
    with pytest.raises(ValueError, match="Không thể parse LaTeX"):
        latex_sang_sympy(r"\frac{}{")


def test_don_gian():
    result = latex_sang_sympy(r"x^2 + 1")
    from sympy import sympify
    assert sympify(result) == sympify("x**2 + 1")
