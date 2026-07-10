import re

from sympy import I, Symbol
from sympy.parsing.latex import parse_latex as _sympy_parse_latex

# ---------------------------------------------------------------------------------------
# Chuẩn hóa LaTeX TRƯỚC khi đưa cho parser (sympy.parsing.latex, backend antlr).
#
# Bối cảnh: parser antlr KHÔNG hỗ trợ đầy đủ mọi cú pháp LaTeX hợp lệ — với một số lệnh, nó
# hoặc báo lỗi thẳng (an toàn, dễ phát hiện), hoặc TỆ HƠN NHIỀU là ÂM THẦM hiểu sai thành phép
# nhân với 1 ký hiệu tự do (vd "3\\pm 1" → "3*pm*1", "C_5^3" → "C_5**3" thay vì binomial(5,3))
# — sai lệch này KHÔNG ném lỗi nên rất dễ lọt qua, chỉ lộ ra khi so khớp đáp án cho kết quả sai
# một cách khó hiểu. Toàn bộ các lệnh dưới đây đều LẤY TỪ ĐÚNG bảng công thức HS/GV thực sự
# dùng để nhập (frontend/src/components/answer/MathPalette.jsx) — không phải LaTeX tùy ý.
#
# Đặt TẤT CẢ chuẩn hóa ở ĐÂY (module core/matching, không phụ thuộc web/LLM) để cả 2 nơi dùng
# CAS đều tự động được vá cùng lúc: (1) ô "chuyển đổi công thức" GV dùng khi soạn câu hỏi, và
# (2) core/matching/cas.py chấm đáp án học sinh. Tránh tình trạng vá 1 chỗ mà chỗ kia vẫn lỗi.
# ---------------------------------------------------------------------------------------

# 1) \sqrt/\sqrt[n] thiếu ngoặc nhọn (LaTeX chuẩn cho phép bỏ {} khi đối số chỉ 1 "token" —
#    vd \sqrt2, \sqrt\alpha — nhưng antlr bắt buộc phải có {}).
_RE_SQRT_THIEU_NGOAC = re.compile(r"\\sqrt(\[[^\[\]]*\])?\s*(\\[a-zA-Z]+|[0-9A-Za-z])")


def _them_ngoac_sqrt(s: str) -> str:
    def _boc(m: re.Match) -> str:
        bac = m.group(1) or ""
        doi_so = m.group(2)
        return f"\\sqrt{bac}{{{doi_so}}}"

    return _RE_SQRT_THIEU_NGOAC.sub(_boc, s)


# 2) Giá trị tuyệt đối/môđun \left|...\right| — antlr hiểu \left( \left[ \left\{ nhưng LẠI LỖI
#    HẲN với \left|...\right| (báo thiếu '\rangle', dù cú pháp hoàn toàn hợp lệ). Chỉ cần bỏ
#    \left/\right quanh riêng dấu | là parse đúng thành Abs(...); các cặp \left(/\right) khác
#    KHÔNG bị đụng tới.
def _bo_left_right_cho_gia_tri_tuyet_doi(s: str) -> str:
    return s.replace(r"\left|", "|").replace(r"\right|", "|")


# 3) Tổ hợp C_n^k / chỉnh hợp A_n^k — ký hiệu SGK VN mà bảng công thức tạo ra (nút "Cₙᵏ"/"Aₙᵏ"),
#    KHÔNG phải cú pháp LaTeX chuẩn nên antlr hiểu nhầm thành "C" (ký hiệu tự do) lũy thừa —
#    ÂM THẦM SAI, không báo lỗi. Chuyển sang \binom{n}{k} (antlr hiểu đúng thành binomial(n,k))
#    và n!/(n-k)! cho chỉnh hợp (không có lệnh LaTeX dựng sẵn, khai triển bằng giai thừa).
_RE_TO_HOP = re.compile(r"C_(?:\{([^{}]*)\}|([0-9A-Za-z]))\^(?:\{([^{}]*)\}|([0-9A-Za-z]))")
_RE_CHINH_HOP = re.compile(r"A_(?:\{([^{}]*)\}|([0-9A-Za-z]))\^(?:\{([^{}]*)\}|([0-9A-Za-z]))")


def _thay_to_hop_chinh_hop(s: str) -> str:
    def _to_hop(m: re.Match) -> str:
        n = m.group(1) if m.group(1) is not None else m.group(2)
        k = m.group(3) if m.group(3) is not None else m.group(4)
        return f"\\binom{{{n}}}{{{k}}}"

    def _chinh_hop(m: re.Match) -> str:
        n = m.group(1) if m.group(1) is not None else m.group(2)
        k = m.group(3) if m.group(3) is not None else m.group(4)
        return f"\\frac{{({n})!}}{{(({n})-({k}))!}}"

    s = _RE_TO_HOP.sub(_to_hop, s)
    s = _RE_CHINH_HOP.sub(_chinh_hop, s)
    return s


# 4) Độ (°) — nút "°" chèn "^{\circ}"/"^\circ". antlr hiểu nhầm "circ" thành ký hiệu tự do rồi
#    lấy 180 lũy thừa nó ("180**circ") thay vì giữ nguyên giá trị 180 — bỏ hẳn phần đánh dấu độ,
#    giữ lại đúng con số (đáp án cuối là giá trị độ, không cần đơn vị trong biểu thức CAS).
_RE_DO = re.compile(r"\^\{?\\circ\}?")


def _bo_ky_hieu_do(s: str) -> str:
    return _RE_DO.sub("", s)


# 5) \ne (MathLive xuất — nút "≠") — antlr CHỈ hiểu \neq (có "q"), \ne bị hiểu nhầm thành ký
#    hiệu tự do "ne" nhân vào ("3*(ne*4)"). Cùng loại vá với \star/\ast → \cdot đã có sẵn.
_RE_NE = re.compile(r"\\ne(?![a-zA-Z])")


def _chuan_hoa_ky_hieu(s: str) -> str:
    s = s.replace("\\star", "\\cdot").replace("\\ast", "\\cdot")
    s = _RE_NE.sub("\\\\neq", s)
    return s


# 6) \pm/\mp/\approx — không đại diện MỘT giá trị xác định (và antlr cũng hiểu sai thành ký
#    hiệu tự do nhân vào, KHÔNG báo lỗi) — với biểu thức đáp án/kết quả CAS cần so khớp bằng 1
#    giá trị cụ thể, thà báo lỗi rõ ràng (→ "em nhập lại bằng biểu thức hợp lệ") còn hơn để lọt
#    qua một phép so sánh sai lệch mà không ai biết. Dùng regex có ranh giới từ (KHÔNG phải
#    substring thô) để không báo nhầm các lệnh khác tình cờ chứa cùng ký tự (vd "\pmod").
_RE_KHONG_PHAI_1_GIA_TRI = re.compile(r"\\(pm|mp|approx)(?![a-zA-Z])")


def _kiem_tra_khong_phai_1_gia_tri(s: str) -> None:
    m = _RE_KHONG_PHAI_1_GIA_TRI.search(s)
    if m:
        raise ValueError(
            f"'\\{m.group(1)}' không đại diện một giá trị xác định để so khớp"
        )


def _chuan_hoa_truoc_khi_parse(s: str) -> str:
    _kiem_tra_khong_phai_1_gia_tri(s)
    s = _bo_left_right_cho_gia_tri_tuyet_doi(s)
    s = _thay_to_hop_chinh_hop(s)
    s = _bo_ky_hieu_do(s)
    s = _chuan_hoa_ky_hieu(s)
    s = _them_ngoac_sqrt(s)
    return s


def latex_sang_sympy(latex_str: str) -> str:
    """Chuyển chuỗi LaTeX sang chuỗi SymPy (Python). Ném ValueError nếu lỗi.

    Message KHÔNG kèm chi tiết lỗi ANTLR gốc (dài, kỹ thuật, tiếng Anh, có dấu ^^^ chỉ vị
    trí lỗi) — không phù hợp hiển thị cho GV/HS. Chi tiết vẫn giữ qua "raise ... from e"
    để debug qua traceback khi cần, chỉ ẩn khỏi phần str(exception) hiển thị ra ngoài.
    """
    try:
        expr = _sympy_parse_latex(_chuan_hoa_truoc_khi_parse(latex_str))
        # "i" luôn bị antlr hiểu là ký hiệu tự do, KHÔNG bao giờ là đơn vị ảo — nếu để nguyên,
        # "3+4i" (HS gõ) và "3+4*I" (chuẩn lưu kiểu SymPy) sẽ KHÔNG bao giờ khớp dù cùng giá
        # trị, làm sai toàn bộ việc chấm câu hỏi chủ đề Số phức. Bảng công thức không dùng "i"
        # cho việc khác (chỉ số tổng/tích dùng "k"), nên thay thế an toàn trong miền ứng dụng.
        if expr.has(Symbol("i")):
            expr = expr.subs(Symbol("i"), I)
        return str(expr)
    except Exception as e:
        raise ValueError(f"Không thể parse LaTeX '{latex_str}'") from e
