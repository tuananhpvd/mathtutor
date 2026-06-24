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


def test_latex_hong():
    with pytest.raises(ValueError, match="Không thể parse LaTeX"):
        latex_sang_sympy(r"\frac{}{")


def test_don_gian():
    result = latex_sang_sympy(r"x^2 + 1")
    from sympy import sympify
    assert sympify(result) == sympify("x**2 + 1")
