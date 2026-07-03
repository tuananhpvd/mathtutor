"""Phân tích hàm số để GV vẽ đồ thị mà không cần nhập gì ngoài f(x) (GĐ3A).

CAS (SymPy) tất định: tìm miền xác định, tiệm cận, cực trị, khoảng dấu đạo hàm, rồi lấy điểm
mẫu để vẽ đường cong. KHÔNG dùng LLM — đúng nguyên tắc "CAS quyết định đúng/sai/giá trị".

Phạm vi hỗ trợ: hàm hữu tỉ một biến x (đa thức / phân thức đa thức) bậc thấp — đúng trọng tâm
khảo sát hàm số lớp 12 (đa thức bậc 3, trùng phương bậc 4, phân thức b1/b1 và b2/b1). Hàm ngoài
phạm vi (căn, log, lượng giác, chứa tham số...) ném ValueError với thông báo tiếng Việt để GV
chuyển sang upload ảnh thường.

Thiết kế 2 tầng để dùng lại cho bảng biến thiên (GĐ3B, chưa làm):
  - _phan_tich(): nội bộ, có thể giữ đối tượng SymPy (khóa bắt đầu bằng "_" không xuất ra ngoài).
  - phan_tich_ham_so(): JSON-safe — TXĐ, tiệm cận, cực trị, khoảng dấu. Đủ cho bảng biến thiên sau này.
  - du_lieu_do_thi(): phan_tich_ham_so() + lấy điểm mẫu — dùng cho API /ve-do-thi (GĐ3A).
"""

import math

from sympy import S, Symbol, diff, fraction, lambdify, limit, oo, solveset, together

from app.core.matching.cas import parse_bieu_thuc_an_toan

X = Symbol("x")  # KHÔNG real=True: phải khớp đúng ký hiệu sympify() tạo ra (không assumption)

BAC_TOI_DA = 4              # bậc tử/mẫu tối đa — giữ đúng "hàm số quen thuộc lớp 12"
SO_DIEM_MAU = 300           # số điểm mẫu tối đa mỗi lần quét cửa sổ (chia thành nhiều đoạn)
TY_LE_EPS_TIEM_CAN = 0.015  # bề rộng vùng loại trừ quanh điểm gián đoạn, theo % độ rộng cửa sổ


def _tu_mau(expr):
    return fraction(together(expr))


def _bac(expr) -> int:
    p = expr.as_poly(X)
    return p.degree() if p is not None else 0


def _nghiem_thuc_sym(expr) -> list:
    """Nghiệm thực (dạng SymPy chính xác) của expr = 0, tăng dần.

    Trả [] nếu vô nghiệm, hoặc solveset không giải được ở dạng hữu hạn (ConditionSet/khoảng)
    — coi như không có mốc đặc biệt từ phía biểu thức này, KHÔNG ném lỗi (giữ tiện ích chạy được
    cho phần còn phân tích được, thay vì chặn toàn bộ vì một chi tiết phụ).
    """
    try:
        nghiem = solveset(expr, X, domain=S.Reals)
    except (NotImplementedError, TypeError):
        return []
    if not nghiem.is_FiniteSet:
        return []
    try:
        return sorted(nghiem, key=lambda v: float(v.evalf()))
    except (TypeError, ValueError):
        return []


def _so(v) -> float:
    """SymPy số → python float. Ném ValueError nếu không phải số thực hữu hạn."""
    f = complex(v.evalf())
    if abs(f.imag) > 1e-9:
        raise ValueError("Giá trị không thực")
    return float(f.real)


def _phan_tich(bieu_thuc_str: str) -> dict:
    """Phân tích nội bộ f(x). Khóa bắt đầu "_" giữ đối tượng SymPy, không xuất ra API."""
    try:
        expr = parse_bieu_thuc_an_toan(bieu_thuc_str)
    except ValueError as e:
        raise ValueError(f"Không đọc được hàm số: {e}") from e

    an_ngoai_x = expr.free_symbols - {X}
    if an_ngoai_x:
        raise ValueError(
            "Hàm chứa tham số/biến khác ngoài x — chưa hỗ trợ, hãy nhập hàm số cụ thể"
        )
    if not expr.is_rational_function(X):
        raise ValueError(
            "Chỉ hỗ trợ hàm đa thức / phân thức hữu tỉ (chưa hỗ trợ căn, log, lượng giác...)"
        )

    tu, mau = _tu_mau(expr)
    bac_tu, bac_mau = _bac(tu), _bac(mau)
    if bac_tu > BAC_TOI_DA or bac_mau > BAC_TOI_DA:
        raise ValueError(f"Bậc hàm số vượt quá {BAC_TOI_DA} — chưa hỗ trợ")

    # TXĐ: loại điểm làm mẫu = 0.
    diem_loai_sym = [] if mau.is_number else _nghiem_thuc_sym(mau)

    # Tiệm cận đứng: điểm loại trừ mà tử khác 0 tại đó (không phải lỗ hổng khử được).
    tiem_can_dung_sym = [x0 for x0 in diem_loai_sym if abs(_so(tu.subs(X, x0))) > 1e-9]

    # Tiệm cận ngang / xiên.
    tiem_can_ngang = None
    tiem_can_xien = None
    gh_duong = limit(expr, X, oo)
    if gh_duong.is_finite:
        tiem_can_ngang = _so(gh_duong)
    elif bac_tu == bac_mau + 1:
        he_so_a = limit(expr / X, X, oo)
        if he_so_a.is_finite and he_so_a != 0:
            he_so_b = limit(expr - he_so_a * X, X, oo)
            if he_so_b.is_finite:
                tiem_can_xien = (_so(he_so_a), _so(he_so_b))

    # Đạo hàm → điểm tới hạn (numerator của f' sau together = 0, loại điểm ngoài TXĐ).
    dao_ham = diff(expr, X)
    tu_d, mau_d = _tu_mau(dao_ham)
    diem_toi_han_sym = [
        x0 for x0 in _nghiem_thuc_sym(tu_d) if not any(x0 == lt for lt in diem_loai_sym)
    ]

    moc_sym = sorted(set(diem_loai_sym) | set(diem_toi_han_sym), key=lambda v: float(v.evalf()))

    # Dấu f' trên từng khoảng mở giữa 2 mốc liên tiếp (kể cả 2 đầu vô cực) — điểm giữa đại diện.
    bien = [-oo] + moc_sym + [oo]
    khoang_dau = []
    for i in range(len(bien) - 1):
        trai, phai = bien[i], bien[i + 1]
        if trai == -oo and phai == oo:
            diem_thu = 0.0
        elif trai == -oo:
            diem_thu = _so(phai) - 1.0
        elif phai == oo:
            diem_thu = _so(trai) + 1.0
        else:
            diem_thu = (_so(trai) + _so(phai)) / 2
        try:
            dau_tai = _so(tu_d.subs(X, diem_thu)) * _so(mau_d.subs(X, diem_thu))
            dau = "duong" if dau_tai > 0 else ("am" if dau_tai < 0 else "khong")
        except (ValueError, TypeError):
            dau = "khong_xac_dinh"
        khoang_dau.append({
            "trai": None if trai == -oo else _so(trai),
            "phai": None if phai == oo else _so(phai),
            "dau": dau,
        })

    cuc_tri = []
    for x0 in diem_toi_han_sym:
        try:
            vi_tri = moc_sym.index(x0)
            dau_truoc, dau_sau = khoang_dau[vi_tri]["dau"], khoang_dau[vi_tri + 1]["dau"]
            y0 = _so(expr.subs(X, x0))
        except (ValueError, IndexError, TypeError):
            continue
        if dau_truoc == "duong" and dau_sau == "am":
            cuc_tri.append({"x": _so(x0), "y": y0, "loai": "cuc_dai"})
        elif dau_truoc == "am" and dau_sau == "duong":
            cuc_tri.append({"x": _so(x0), "y": y0, "loai": "cuc_tieu"})

    return {
        "bieu_thuc_chuan": str(expr),
        "moc": [_so(m) for m in moc_sym],
        "diem_loai_txd": [_so(d) for d in diem_loai_sym],
        "tiem_can_dung": [_so(t) for t in tiem_can_dung_sym],
        "tiem_can_ngang": tiem_can_ngang,
        "tiem_can_xien": (
            {"a": tiem_can_xien[0], "b": tiem_can_xien[1]} if tiem_can_xien else None
        ),
        "cuc_tri": cuc_tri,
        "khoang_dau": khoang_dau,
        "_expr": expr,
    }


def phan_tich_ham_so(bieu_thuc_str: str) -> dict:
    """API công khai: phân tích f(x) → dữ liệu JSON-safe (TXĐ, tiệm cận, cực trị, khoảng dấu).

    Ném ValueError (thông báo tiếng Việt, an toàn hiện cho GV) nếu ngoài phạm vi hỗ trợ.
    """
    noi_bo = _phan_tich(bieu_thuc_str)
    return {k: v for k, v in noi_bo.items() if not k.startswith("_")}


def _cua_so_x_mac_dinh(moc: list[float]) -> tuple[float, float]:
    if not moc:
        return -6.0, 6.0
    lo, hi = min(moc), max(moc)
    bien = max(2.0, (hi - lo) * 0.6 + 1.0)
    return lo - bien, hi + bien


def _cua_so_y_mac_dinh(tt: dict, x_min: float, x_max: float, f_so, trong_vung_loai) -> tuple[float, float]:
    """Khung y ưu tiên các giá trị ĐÁNG CHÚ Ý (cực trị, tiệm cận) — KHÔNG dựa vào điểm mẫu sát
    tiệm cận đứng (sẽ "nổ" ra rất lớn, kéo méo khung nhìn vô dụng). Chỉ khi hàm không có mốc nào
    (đơn điệu, không cực trị/tiệm cận) mới dùng giá trị 2 đầu cửa sổ để có khung nhìn hợp lý —
    nếu luôn cộng 2 đầu này, đuôi hàm bậc lẻ (vốn tăng/giảm rất nhanh) sẽ lấn át khung nhìn,
    làm đoạn "đáng xem" quanh cực trị bị nén phẳng.
    """
    ys = [c["y"] for c in tt["cuc_tri"]]
    if tt["tiem_can_ngang"] is not None:
        ys.append(tt["tiem_can_ngang"])
    if tt["tiem_can_xien"] is not None:
        a, b = tt["tiem_can_xien"]["a"], tt["tiem_can_xien"]["b"]
        ys += [a * x_min + b, a * x_max + b]
    if not ys:
        for xb in (x_min, x_max):
            if trong_vung_loai(xb):
                continue
            try:
                yb = f_so(xb)
                if not isinstance(yb, complex) and math.isfinite(yb):
                    ys.append(yb)
            except (ZeroDivisionError, ValueError, OverflowError):
                pass
    if not ys:
        return -5.0, 5.0
    y_lo, y_hi = min(ys), max(ys)
    if y_lo == y_hi:
        y_lo, y_hi = y_lo - 1, y_hi + 1
    pad = (y_hi - y_lo) * 0.15
    return y_lo - pad, y_hi + pad


def du_lieu_do_thi(bieu_thuc_str: str, cua_so: tuple[float, float] | None = None) -> dict:
    """Phân tích + lấy điểm mẫu để vẽ đường cong. Trả dữ liệu JSON-safe cho API /ve-do-thi.

    "cac_doan": mỗi đoạn là 1 dải điểm liên tục — TÁCH đoạn tại tiệm cận đứng/điểm loại TXĐ, và
    tại chỗ đường "chạy khỏi khung nhìn" (gần tiệm cận), để frontend không vẽ nhầm 1 đường nối
    xuyên qua chỗ hàm không xác định hoặc kéo méo khung nhìn theo giá trị cực lớn.
    """
    noi_bo = _phan_tich(bieu_thuc_str)
    expr = noi_bo["_expr"]
    tt = {k: v for k, v in noi_bo.items() if not k.startswith("_")}

    if cua_so is not None:
        x_min, x_max = cua_so
        if not (x_max > x_min):
            raise ValueError("x_max phải lớn hơn x_min")
    else:
        x_min, x_max = _cua_so_x_mac_dinh(tt["moc"])

    eps = (x_max - x_min) * TY_LE_EPS_TIEM_CAN
    vung_loai_tru = [(d - eps, d + eps) for d in tt["diem_loai_txd"]]

    def _trong_vung_loai(xv: float) -> bool:
        return any(a <= xv <= b for a, b in vung_loai_tru)

    f_so = lambdify(X, expr, modules=["math"])

    y_lo, y_hi = _cua_so_y_mac_dinh(tt, x_min, x_max, f_so, _trong_vung_loai)
    # Điểm ngoài biên nới rộng coi như "chạy khỏi khung nhìn" → ngắt đoạn (không vẽ), giữ khung y ổn định.
    bien_hien = (y_hi - y_lo) * 0.5
    y_hien_thi_lo, y_hien_thi_hi = y_lo - bien_hien, y_hi + bien_hien

    cac_doan: list[list[list[float]]] = []
    doan_hien_tai: list[list[float]] = []
    buoc = (x_max - x_min) / SO_DIEM_MAU
    x = x_min
    for _ in range(SO_DIEM_MAU + 1):
        bi_loai = _trong_vung_loai(x)
        y = None
        if not bi_loai:
            try:
                y = f_so(x)
                if isinstance(y, complex) or not math.isfinite(y):
                    bi_loai = True
                elif not (y_hien_thi_lo <= y <= y_hien_thi_hi):
                    bi_loai = True
            except (ZeroDivisionError, ValueError, OverflowError):
                bi_loai = True
        if bi_loai:
            if len(doan_hien_tai) >= 2:
                cac_doan.append(doan_hien_tai)
            doan_hien_tai = []
        else:
            doan_hien_tai.append([round(x, 6), round(y, 6)])
        x += buoc
    if len(doan_hien_tai) >= 2:
        cac_doan.append(doan_hien_tai)

    return {
        **tt,
        "cac_doan": cac_doan,
        "cua_so": {"x_min": x_min, "x_max": x_max, "y_min": y_lo, "y_max": y_hi},
    }
