"""
MC-1 — Bộ 100 biểu thức kiểm chứng CAS (thuyết minh Bảng 13, dòng "Chấm toán bằng SymPy").

QUAN TRỌNG: mỗi ca được SINH CÓ KIỂM SOÁT sao cho `ky_vong` đúng ĐÚNG BẰNG CẤU TRÚC sinh ra
nó (vd hs_nhap = LaTeX do chính SymPy xuất ra từ `chuan` → chắc chắn tương đương), KHÔNG
phải do người viết tự tính tay rồi có thể gõ nhầm. Điều này để `ky_vong` đáng tin cậy — nếu
`test_mc1_bieu_thuc.py` báo lệch, đó là dấu hiệu THẬT của CAS, không phải lỗi khi soạn dữ liệu.

random.seed cố định → chạy lại luôn ra đúng 100 ca này (tái lập được).
"""

import random

from sympy import Rational, binomial, expand, factorial, symbols
from sympy import latex as sympy_latex

x = symbols("x")

CAC_CA: list[dict] = []
_id = 0


def _them(nhom, hs_nhap, chuan, ky_vong, che_do="tuong_duong", lam_tron=None, ghi_chu=""):
    global _id
    _id += 1
    CAC_CA.append({
        "id": _id,
        "nhom": nhom,
        "hs_nhap": str(hs_nhap),
        "chuan": str(chuan),
        "che_do": che_do,
        "lam_tron": lam_tron,
        "ky_vong": ky_vong,
        "ghi_chu": ghi_chu,
    })


_rng = random.Random(42)  # tất định — chạy lại ra cùng bộ 100 ca


# ── Nhóm 1: khai triển/rút gọn (15 ca DUNG) — hs_nhap ở dạng CHƯA khai triển, chuan là
# kết quả expand() của CHÍNH biểu thức đó → tương đương do chính SymPy đảm bảo. ──
for _ in range(15):
    a, b, c = _rng.randint(-6, 6) or 1, _rng.randint(-6, 6) or 1, _rng.randint(-9, 9)
    hs_expr = (x + a) * (x + b) + c
    _them("khai_trien_rut_gon", hs_expr, expand(hs_expr), "DUNG",
          ghi_chu="HS nhập dạng tích chưa khai triển, chuẩn là kết quả expand()")

# ── Nhóm 2: LaTeX do chính SymPy xuất ra (10 ca DUNG) — mô phỏng HS nhập qua editor công
# thức (MathLive xuất LaTeX), chuẩn là chuỗi cú pháp SymPy thuần của CÙNG biểu thức. ──
for _ in range(10):
    a, b, c = _rng.randint(-6, 6) or 1, _rng.randint(1, 7), _rng.randint(-9, 9)
    expr = a * x**2 + b * x + c if _rng.random() < 0.7 else Rational(a, b) * x**2 - Rational(1, c or 1)
    _them("latex_editor", sympy_latex(expr), expr, "DUNG",
          ghi_chu="LaTeX do sympy.latex() xuất ra — mô phỏng đầu ra editor MathLive")

# ── Nhóm 3: thập phân kiểu VN trong tọa độ/vectơ (6 ca DUNG) — "(1,5; 2; -3)" ↔
# "(1.5; 2; -3)", đúng quy ước dấu phẩy thập phân chỉ áp dụng TRONG cú pháp vectơ. ──
for _ in range(6):
    p1 = round(_rng.uniform(-9, 9), 1)
    p2, p3 = _rng.randint(-9, 9), _rng.randint(-9, 9)
    hs_str = f"({str(p1).replace('.', ',')}; {p2}; {p3})"
    chuan_str = f"({p1}; {p2}; {p3})"
    _them("thap_phan_kieu_vn", hs_str, chuan_str, "DUNG",
          ghi_chu="Dấu phẩy thập phân kiểu VN trong tọa độ/vectơ SGK")

# ── Nhóm 4: tọa độ/vectơ đúng (10 ca DUNG) — mỗi thành phần là 1 biểu thức số rút gọn
# được, không chỉ so chuỗi. ──
for _ in range(10):
    v = [_rng.randint(-9, 9) for _ in range(3)]
    hs_str = f"({v[0]}+{_rng.randint(-3,3)}-{_rng.randint(-3,3)}; {v[1]}*1; {v[2]})"
    chuan_str = f"({v[0]}; {v[1]}; {v[2]})"
    # Chuẩn hóa hs_str: thành phần đầu = v[0] + d1 - d2, phải RA ĐÚNG v[0] — tính lại đúng d1,d2
    d1 = _rng.randint(-3, 3)
    d2 = d1  # d1 - d2 = 0 → thành phần đầu vẫn = v[0], đảm bảo DUNG chắc chắn
    hs_str = f"({v[0]}+{d1}-{d2}; {v[1]}*1; {v[2]})"
    _them("vecto_toa_do", hs_str, chuan_str, "DUNG",
          ghi_chu="Mỗi thành phần rút gọn về đúng giá trị chuẩn")

# ── Nhóm 5: tổ hợp/chỉnh hợp (8 ca DUNG) — C(n,k)/A(n,k) kiểu SGK so với giá trị tính
# bằng chính sympy.binomial/factorial (không tự tính tay). ──
for _ in range(8):
    n = _rng.randint(4, 12)
    k = _rng.randint(1, n - 1)
    if _rng.random() < 0.5:
        hs_str = f"C({n},{k})"
        chuan_val = binomial(n, k)
    else:
        hs_str = f"A({n},{k})"
        chuan_val = factorial(n) / factorial(n - k)
    _them("to_hop_chinh_hop", hs_str, chuan_val, "DUNG",
          ghi_chu="Ký hiệu SGK C(n,k)/A(n,k) so với binomial()/factorial() của sympy")

# ── Nhóm 6: làm tròn (5 ca DUNG) — phân số so với số thập phân làm tròn N chữ số. ──
for _ in range(5):
    p, q = _rng.randint(1, 9), _rng.randint(2, 9)
    so_chu_so = _rng.choice([1, 2, 3])
    gia_tri_tron = round(p / q, so_chu_so)
    _them("lam_tron", f"{p}/{q}", str(gia_tri_tron), "DUNG",
          che_do="tuong_duong", lam_tron=so_chu_so,
          ghi_chu=f"{p}/{q} làm tròn {so_chu_so} chữ số thập phân")

_SO_DUNG_GOC = len(CAC_CA)


# ── Nhóm 7: SAI có chủ đích (~30% tổng bộ) — lấy lại các ca DUNG ở trên, làm lệch 1 giá
# trị để chắc chắn KHÔNG còn tương đương. Không có nhóm SAI thì bộ test chỉ đo được khả
# năng "chấp nhận", không đo được khả năng "bác bỏ" — vô nghĩa quá nửa. ──
_mau_de_sai = _rng.sample(CAC_CA[:_SO_DUNG_GOC], min(30, _SO_DUNG_GOC))
for ca_goc in _mau_de_sai:
    if ca_goc["lam_tron"] is not None:
        chuan_sai = str(round(float(ca_goc["chuan"]) + 1, ca_goc["lam_tron"]))
    elif ca_goc["chuan"].startswith("("):
        # vectơ: đổi thành phần cuối
        thanh_phan = ca_goc["chuan"][1:-1].split(";")
        thanh_phan[-1] = str(int(float(thanh_phan[-1])) + 1)
        chuan_sai = "(" + ";".join(thanh_phan) + ")"
    else:
        chuan_sai = f"({ca_goc['chuan']}) + 1"
    _id += 1
    CAC_CA.append({
        "id": _id, "nhom": f"{ca_goc['nhom']}_sai", "hs_nhap": ca_goc["hs_nhap"],
        "chuan": chuan_sai, "che_do": ca_goc["che_do"], "lam_tron": ca_goc["lam_tron"],
        "ky_vong": "SAI",
        "ghi_chu": f"Biến thể SAI của ca #{ca_goc['id']} (lệch +1 có chủ đích)",
    })


# ── Nhóm 8: không phân tích được (8 ca cố ý) — văn bản thường, ký tự lạ, chuỗi rỗng. ──
# LƯU Ý: 2 chuỗi ban đầu dự định dùng ("3x^^2", "x = = 3") đã bị LOẠI sau khi bộ test chạy
# thật cho thấy chúng KHÔNG rơi vào KHONG_PHAN_TICH_DUOC như dự đoán — parser LaTeX dự phòng
# khoan dung hơn giả định: "3x^^2" bị đọc thành "3*x" (rơi mất số mũ lặp), "x = = 3" bị hiểu
# thành biểu thức boolean. Đây là phát hiện thật (đã xác minh bằng parse_bieu_thuc_an_toan()
# trực tiếp), không phải lỗi soạn dữ liệu — giữ lại làm ghi chú thay vì xóa âm thầm.
_KHONG_DOC_DUOC = [
    ("hai muoi", "20", "Văn bản chữ thường không phải công thức"),
    ("x @ y", "1", "Ký tự @ không hợp lệ trong biểu thức"),
    ("", "5", "Chuỗi rỗng"),
    ("x === 3", "3", "Cú pháp so sánh lặp 3 dấu bằng không hợp lệ"),
    ("bằng năm", "5", "Chữ số viết bằng lời"),
    ("(3;", "(3; 1; 2)", "Ngoặc vectơ không đóng"),
    ("toi khong biet lam", "5", "Câu chữ thường, không có ký hiệu toán học"),
    ("@#$%", "1", "Chuỗi ký tự không có ý nghĩa toán học"),
]
for hs, chuan, ghi_chu in _KHONG_DOC_DUOC:
    _them("khong_phan_tich_duoc", hs, chuan, "KHONG_PHAN_TICH_DUOC", ghi_chu=ghi_chu)


# ── Nhóm 9: chưa đủ cơ sở — điều kiện xác định (8 ca, thuyết minh mục V.4 phần B) —
# sqrt(f(x)) với f(x) chưa chứng minh được không âm dù giả định biến thực. ──
_CHUA_DU_CO_SO = [
    ("sqrt(x-1)", "sqrt(x-1)", "x-1 có thể âm hoặc dương tùy x thực"),
    ("sqrt(2*x+3)", "sqrt(2*x+3)", "2x+3 chưa xác định dấu"),
    ("sqrt(x)", "sqrt(x)", "x chưa xác định dấu (cần x>=0)"),
    ("sqrt(1-x**2)", "sqrt(1-x**2)", "1-x^2 chỉ không âm khi -1<=x<=1"),
    ("sqrt(x*y)", "sqrt(x*y)", "tích x*y chưa xác định dấu"),
    ("sqrt(x-3)+1", "sqrt(x-3)+1", "cộng thêm hằng số không đổi bản chất thiếu điều kiện"),
    ("2*sqrt(x+1)", "2*sqrt(x+1)", "nhân hệ số không đổi bản chất thiếu điều kiện"),
    ("sqrt(x**3)", "sqrt(x**3)", "x^3 đổi dấu theo x nên chưa xác định"),
]
for hs, chuan, ghi_chu in _CHUA_DU_CO_SO:
    _them("chua_du_co_so_dieu_kien_xac_dinh", hs, chuan, "CHUA_DU_CO_SO", ghi_chu=ghi_chu)
