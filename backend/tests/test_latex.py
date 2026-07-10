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


# ---------- Rà soát toàn diện bảng công thức (MathPalette.jsx) — GV yêu cầu không để lỗi mới ----------
#
# Mọi lệnh dưới đây LẤY ĐÚNG từ frontend/src/components/answer/MathPalette.jsx (bảng công thức
# HS/GV thực sự dùng để nhập, không phải LaTeX tùy ý). Rà soát toàn bộ 1 lần để bắt hết các kiểu
# ANTLR hiểu SAI ÂM THẦM (không báo lỗi nhưng cho kết quả sai) cùng lúc, thay vì để lộ dần từng
# cái một qua nhiều lần báo lỗi/vá riêng lẻ.

def test_gia_tri_tuyet_doi_left_right():
    """\\left|x\\right| (nút "|x|"/"|z|") trước đây LỖI THẲNG (antlr đòi \\rangle) dù đây là
    cú pháp LaTeX hợp lệ — không phải chỉ \\sqrt mới bị kiểu lỗi ngoặc này."""
    from sympy import Abs, sympify
    assert sympify(latex_sang_sympy(r"\left|-5\right|")) == Abs(-5)
    assert sympify(latex_sang_sympy(r"\left|-5\right|")) == 5


def test_to_hop_ky_hieu_sgk():
    """Nút "Cₙᵏ" tạo ra C_{n}^{k} — KHÔNG phải cú pháp LaTeX chuẩn nên antlr hiểu nhầm thành
    "C" (ký hiệu tự do) lũy thừa, ÂM THẦM SAI (không lỗi) — nguy hiểm vì đây là chủ đề Tổ hợp -
    Xác suất rất phổ biến trong đề thi THPT."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"C_{5}^{3}")) == 10
    assert sympify(latex_sang_sympy(r"C_5^3")) == 10  # không ngoặc (số đơn)


def test_chinh_hop_ky_hieu_sgk():
    """Nút "Aₙᵏ" — cùng loại lỗi với C_n^k ở trên (n!/(n-k)! thay vì lũy thừa vô nghĩa)."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"A_{5}^{2}")) == 20
    assert sympify(latex_sang_sympy(r"A_5^2")) == 20


def test_ky_hieu_do():
    """Nút "°" chèn ^{\\circ} — antlr hiểu nhầm "circ" thành ký hiệu tự do rồi lấy 180 lũy
    thừa nó ("180**circ") thay vì giữ nguyên giá trị 180, ÂM THẦM SAI."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"180^{\circ}")) == 180
    assert sympify(latex_sang_sympy(r"60^\circ")) == 60


def test_ne_chuan_hoa_ve_neq():
    """Nút "≠" chèn \\ne — antlr CHỈ hiểu \\neq (có "q"), \\ne bị hiểu nhầm thành ký hiệu tự do
    "ne" nhân vào, ÂM THẦM SAI (không lỗi, luôn cho kết quả khác 0 dù có thể đúng)."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"3 \ne 4")) is True
    assert sympify(latex_sang_sympy(r"3 \ne 3")) is False


def test_pm_approx_bao_loi_ro_thay_vi_am_tham_sai():
    """\\pm/\\approx (nút "±"/"≈") không đại diện 1 giá trị xác định — antlr âm thầm biến
    chúng thành ký hiệu tự do nhân vào thay vì báo lỗi, khiến MỌI so sánh với biểu thức này
    luôn ra "khác nhau" một cách vô nghĩa mà không ai biết tại sao. Thà báo lỗi thẳng (HS được
    nhắc nhập lại) còn hơn để lọt qua so sánh sai."""
    with pytest.raises(ValueError, match="Không thể parse LaTeX"):
        latex_sang_sympy(r"3 \pm 1")
    with pytest.raises(ValueError, match="Không thể parse LaTeX"):
        latex_sang_sympy(r"3 \approx 3")


def test_pm_khong_bao_nham_pmod():
    """Hồi quy: kiểm tra \\pm phải dùng ranh giới từ, KHÔNG được báo nhầm các lệnh khác tình cờ
    chứa cùng chữ cái đầu (vd \\pmod) — dù \\pmod tự nó vẫn chưa được hỗ trợ (không thuộc bảng
    công thức, ngoài phạm vi), lỗi báo ra (nếu có) không được nói sai là do \\pm."""
    from app.core.matching.latex import _kiem_tra_khong_phai_1_gia_tri
    _kiem_tra_khong_phai_1_gia_tri(r"17 \pmod{5}")  # không raise — không phải \pm thật


def test_so_phuc_i_la_don_vi_ao():
    """Chủ đề Số phức: antlr LUÔN hiểu "i" là ký hiệu tự do, KHÔNG BAO GIỜ là đơn vị ảo — khiến
    đáp án HS gõ "3+4i" và đáp án chuẩn lưu kiểu SymPy "3+4*I" KHÔNG BAO GIỜ khớp dù cùng giá
    trị, làm sai toàn bộ việc chấm câu hỏi chủ đề này. Đây là lỗi nghiêm trọng nhất tìm được
    trong đợt rà soát này vì ảnh hưởng cả 1 chuyên đề, không chỉ 1 ký hiệu lẻ."""
    from sympy import I, simplify, sympify
    assert sympify(latex_sang_sympy("3+4i")) == 3 + 4 * I
    assert sympify(latex_sang_sympy("i")) == I
    assert sympify(latex_sang_sympy("2i")) == 2 * I
    # So khớp thật như CAS sẽ làm: HS gõ LaTeX "3+4i" phải khớp đáp án chuẩn SymPy "3+4*I"
    assert simplify(sympify(latex_sang_sympy("3+4i")) - sympify("3+4*I")) == 0


def test_mo_dun_so_phuc():
    """|3+4i| (nút "|z|" + số phức) = 5 — kết hợp 2 lỗi đã sửa (giá trị tuyệt đối + đơn vị ảo)
    trong cùng 1 biểu thức, đúng như HS thực tế sẽ gõ khi tính môđun số phức."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"\left|3+4i\right|")) == 5


def test_sao_nhan_van_hoat_dong_sau_khi_gom_ve_1_noi():
    """Sau khi dồn \\star/\\ast (trước ở cas.py) về chung latex.py, hành vi phải giữ nguyên."""
    from sympy import sympify
    assert sympify(latex_sang_sympy(r"2\star 3")) == 6
    assert sympify(latex_sang_sympy(r"2\ast 3")) == 6
