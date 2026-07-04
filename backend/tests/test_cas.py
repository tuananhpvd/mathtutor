from app.core.matching.cas import CheDoSoKhop, KetQuaSoKhop, tuong_duong


def test_tuong_duong_bieu_thuc():
    assert tuong_duong("x**2-1", "-1+x**2") == KetQuaSoKhop.DUNG
    assert tuong_duong("x**2-1", "(x-1)*(x+1)") == KetQuaSoKhop.DUNG


def test_tuong_duong_so():
    assert tuong_duong("1/2", "0.5") == KetQuaSoKhop.DUNG
    assert tuong_duong("2/4", "0.5") == KetQuaSoKhop.DUNG
    assert tuong_duong("pi/6", "pi/6") == KetQuaSoKhop.DUNG


def test_sai():
    assert tuong_duong("2", "3") == KetQuaSoKhop.SAI
    assert tuong_duong("x+1", "x+2") == KetQuaSoKhop.SAI


def test_cu_phap_hong():
    # chuỗi chỉ có ký tự không parse được
    assert tuong_duong("x @ y", "1") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC
    assert tuong_duong("", "1") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC


def test_input_nguy_hiem():
    assert tuong_duong("__import__('os')", "1") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC


def test_dung_dang_phan_biet():
    # (x-1)(x+1) != x**2-1 theo dung_dang
    r = tuong_duong("(x-1)*(x+1)", "x**2-1", CheDoSoKhop.dung_dang)
    assert r == KetQuaSoKhop.SAI
    # x**2-1 == x**2-1 theo dung_dang
    r2 = tuong_duong("x**2-1", "x**2-1", CheDoSoKhop.dung_dang)
    assert r2 == KetQuaSoKhop.DUNG


def test_lam_tron():
    # 0.333... làm tròn 2 chữ số == 0.33
    assert tuong_duong("1/3", "0.33", lam_tron=2) == KetQuaSoKhop.DUNG


def test_input_latex_tu_editor():
    # Editor MathLive xuất LaTeX: nhân ngầm '3x', mũ '^', phải khớp chuẩn SymPy.
    assert tuong_duong("3x^2-3", "3*x**2-3") == KetQuaSoKhop.DUNG
    assert tuong_duong(r"3\cdot x^2-3", "3*x**2-3") == KetQuaSoKhop.DUNG
    assert tuong_duong(r"\frac{1}{2}", "1/2") == KetQuaSoKhop.DUNG
    assert tuong_duong(r"\sqrt{2}", "sqrt(2)") == KetQuaSoKhop.DUNG


def test_input_latex_star_chuan_hoa():
    # MathLive đôi khi xuất '\star' cho phép nhân → chuẩn hóa về '\cdot'.
    assert tuong_duong(r"2\star x", "2*x") == KetQuaSoKhop.DUNG


def test_to_hop_chinh_hop_chuan_hoa():
    """Ký hiệu tổ hợp/chỉnh hợp quen dùng (SGK VN + tên LLM hay bịa) phải parse được.

    Bug thật từ AI sinh câu hỏi: 'Rational(combinations(5, 3), combinations(10, 3))'
    không phải hàm SymPy → bước lời giải bị cảnh báo không parse được.
    """
    from app.core.matching.cas import kiem_tra_bieu_thuc

    # Chuỗi nguyên văn từ bug report
    assert kiem_tra_bieu_thuc("Rational(combinations(5, 3), combinations(10, 3))")
    # C(n,k) kiểu SGK = binomial
    assert tuong_duong("C(5,3)", "10") == KetQuaSoKhop.DUNG
    assert tuong_duong("combinations(10, 3)", "120") == KetQuaSoKhop.DUNG
    assert tuong_duong("comb(4,2)", "6") == KetQuaSoKhop.DUNG
    # Chỉnh hợp A(n,k) = n!/(n-k)! = ff(n,k)
    assert tuong_duong("A(5,2)", "20") == KetQuaSoKhop.DUNG
    assert tuong_duong("permutations(5, 2)", "20") == KetQuaSoKhop.DUNG
    # Hàm SymPy thật vẫn nguyên vẹn
    assert tuong_duong("binomial(5,3)", "10") == KetQuaSoKhop.DUNG
    assert tuong_duong("factorial(4)", "24") == KetQuaSoKhop.DUNG
    # Xác suất "ít nhất 1 bi đỏ" của chính câu hỏi bị lỗi: 1 - C(5,3)/C(10,3) = 11/12
    assert tuong_duong("1 - C(5,3)/C(10,3)", "11/12") == KetQuaSoKhop.DUNG
    # Văn bản thường không bị biến thành hàm (ranh giới từ)
    assert tuong_duong("hai muoi", "20") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC
