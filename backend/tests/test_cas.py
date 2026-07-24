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


# ----- buoc_co_bieu_thuc_khong_hop_le (v142 — chặn lưu bieu_thuc_ket_qua hỏng, không chỉ
# cảnh báo, vì lỗi này khiến CAS không bao giờ chấm đúng được dù HS nhập đúng tuyệt đối) -----

def test_buoc_hop_le_khong_bao_loi():
    from app.core.matching.cas import buoc_co_bieu_thuc_khong_hop_le
    steps = [
        {"thu_tu": 1, "pham_vi": "ca_bai", "bieu_thuc_ket_qua": "3*x**2-3"},
        {"thu_tu": 2, "pham_vi": "ca_bai", "bieu_thuc_ket_qua": ""},  # rỗng vẫn hợp lệ
    ]
    assert buoc_co_bieu_thuc_khong_hop_le(steps) == []


def test_buoc_con_sot_dollar_bao_loi():
    """Sự cố thực tế: bieu_thuc_ket_qua lỡ còn bọc $...$ (AI quên bỏ dù prompt cấm) khiến
    CAS KHÔNG BAO GIỜ so khớp đúng được, kể cả khi học sinh nhập đúng tuyệt đối."""
    from app.core.matching.cas import buoc_co_bieu_thuc_khong_hop_le
    steps = [{"thu_tu": 1, "pham_vi": "ca_bai", "bieu_thuc_ket_qua": "$3x^2-3$"}]
    loi = buoc_co_bieu_thuc_khong_hop_le(steps)
    assert loi and "Bước 1" in loi[0] and "không parse được" in loi[0]


def test_buoc_hong_khong_lam_sap_khi_input_bat_thuong():
    from app.core.matching.cas import buoc_co_bieu_thuc_khong_hop_le
    assert buoc_co_bieu_thuc_khong_hop_le([]) == []
    assert buoc_co_bieu_thuc_khong_hop_le(None) == []
    assert buoc_co_bieu_thuc_khong_hop_le([{"khong_phai": "buoc"}, "chuoi_la"]) == []


# ----- Tọa độ/vectơ kiểu SGK VN "(a; b; c)" (v143 — phát hiện qua sự cố production câu
# #31: bieu_thuc_ket_qua='(4; 4; -2)' trước đây bị coi là hỏng, dù đây là cách viết chuẩn
# SGK cho tọa độ/vectơ, thân thiện với HS hơn cú pháp Matrix([4,4,-2])) -----

def test_vecto_dung_y_het():
    assert tuong_duong("(4; 4; -2)", "(4; 4; -2)") == KetQuaSoKhop.DUNG


def test_vecto_khong_dau_cach_van_dung():
    assert tuong_duong("(4;4;-2)", "(4; 4; -2)") == KetQuaSoKhop.DUNG
    assert tuong_duong("( 4 ; 4 ; -2 )", "(4; 4; -2)") == KetQuaSoKhop.DUNG


def test_vecto_rut_gon_tung_thanh_phan():
    """Mỗi thành phần được tính/rút gọn như biểu thức bình thường, không chỉ so sánh chuỗi."""
    assert tuong_duong("(2+2; 2*2; -2)", "(4; 4; -2)") == KetQuaSoKhop.DUNG


def test_vecto_thap_phan_dau_phay_kieu_vn():
    assert tuong_duong("(1,5; 2; -3)", "(1.5; 2; -3)") == KetQuaSoKhop.DUNG


def test_vecto_sai_1_thanh_phan():
    assert tuong_duong("(4; 4; -3)", "(4; 4; -2)") == KetQuaSoKhop.SAI


def test_vecto_lech_so_chieu_khong_phan_tich_duoc():
    assert tuong_duong("(4; 4)", "(4; 4; -2)") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC


def test_vecto_dung_dang_so_cau_truc_khong_rut_gon():
    # dung_dang: so CẤU TRÚC cú pháp, không rút gọn — thành phần chưa khai triển
    # "(x-1)*(x+1)" khác cây với "x**2-1" dù cùng giá trị đại số (tuong_duong mới coi là
    # bằng nhau)
    assert tuong_duong("((x-1)*(x+1); 2; -2)", "(x**2-1; 2; -2)",
                        CheDoSoKhop.dung_dang) == KetQuaSoKhop.SAI
    assert tuong_duong("((x-1)*(x+1); 2; -2)", "(x**2-1; 2; -2)",
                        CheDoSoKhop.tuong_duong) == KetQuaSoKhop.DUNG
    assert tuong_duong("(4; 4; -2)", "(4; 4; -2)", CheDoSoKhop.dung_dang) == KetQuaSoKhop.DUNG


def test_vecto_khong_pha_bieu_thuc_thuong():
    """Hồi quy: biểu thức đại số bình thường (không có ';') vẫn hoạt động y hệt trước —
    xác nhận không phá bug gốc v142 (đạo hàm 3x^2-3)."""
    assert tuong_duong("3x^2 - 3", "3*x**2-3") == KetQuaSoKhop.DUNG
    assert tuong_duong("hai muoi", "20") == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC


def test_kiem_tra_bieu_thuc_chap_nhan_dang_vecto():
    """Sự cố thực tế: bieu_thuc_ket_qua='(4; 4; -2)' (câu #31 production) trước đây bị
    validate_cau_hoi()/buoc_co_bieu_thuc_khong_hop_le() coi là hỏng — giờ phải chấp nhận."""
    from app.core.matching.cas import buoc_co_bieu_thuc_khong_hop_le, kiem_tra_bieu_thuc
    assert kiem_tra_bieu_thuc("(4; 4; -2)") is True
    assert buoc_co_bieu_thuc_khong_hop_le(
        [{"thu_tu": 1, "pham_vi": "ca_bai", "bieu_thuc_ket_qua": "(4; 4; -2)"}]
    ) == []
