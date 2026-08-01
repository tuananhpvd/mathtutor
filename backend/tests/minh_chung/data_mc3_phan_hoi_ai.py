"""
MC-3 — Corpus 250 phản hồi AI mô phỏng (thuyết minh Bảng 13, dòng "An toàn phản hồi AI";
giảm nửa từ 500 theo yêu cầu rút gọn thời gian).

CẢNH BÁO PHƯƠNG PHÁP (đã trao đổi trước khi soạn): tỉ lệ "bị chặn/tổng" của bộ này HOÀN
TOÀN là hàm số của cách dựng corpus — dựng toàn câu rủi ro thì gần 100% bị chặn, dựng toàn
câu sạch thì gần 0%. Con số tự nó KHÔNG nói lên chất lượng bộ lọc nếu không công bố rõ cách
dựng. Vì vậy corpus này công bố RÕ tỉ lệ dựng: 200 câu AN TOÀN (mô phỏng phản hồi Socratic
bình thường — đa số thực tế) + 50 câu RỦI RO cố ý (mô phỏng các dạng lộ đáp án thường gặp).
Sinh templated có tham số ngẫu nhiên (seed cố định, tái lập được) — KHÔNG nắn để ra một con
số định trước.
"""

import random

_rng = random.Random(7)

CAC_HAM = ["y = x^3 - 3x + 2", "y = x^4 - 2x^2", "y = (2x-1)/(x+1)", "y = x^2 - 4x + 3"]
CAC_CONG_THUC = ["công thức đạo hàm của tích", "công thức tích phân từng phần",
                 "quy tắc xét dấu tam thức bậc hai", "công thức tổ hợp chỉnh hợp",
                 "công thức khai triển nhị thức Newton"]
CAC_DINH_NGHIA = ["định nghĩa xác suất có điều kiện", "định nghĩa cực trị của hàm số",
                  "định nghĩa số phức liên hợp", "định nghĩa vectơ pháp tuyến"]
CAC_HANH_DONG = ["giải phương trình đạo hàm bằng 0", "lập bảng biến thiên",
                 "xét dấu của tử số và mẫu số", "tính tích của hai vectơ"]
CAC_PHAN = ["dấu của biểu thức", "điều kiện xác định", "dấu ngoặc", "hệ số góc"]


def _cau_an_toan() -> str:
    mau = _rng.randint(0, 6)
    if mau == 0:
        return f"Em hãy tính đạo hàm của hàm số {_rng.choice(CAC_HAM)} trước nhé"
    if mau == 1:
        return f"Em thử áp dụng {_rng.choice(CAC_CONG_THUC)} xem sao"
    if mau == 2:
        return "Chính xác! Em đã suy luận đúng bước này rồi, tiếp tục nhé"
    if mau == 3:
        return f"Em hãy xét {_rng.choice(CAC_PHAN)} trong biểu thức nhé"
    if mau == 4:
        return f"Hãy nhớ lại {_rng.choice(CAC_DINH_NGHIA)} nhé"
    if mau == 5:
        return f"Bước tiếp theo em cần {_rng.choice(CAC_HANH_DONG)}"
    return f"Hãy kiểm tra lại {_rng.choice(CAC_PHAN)} em vừa tính nhé"


def _cau_rui_ro() -> str:
    n = _rng.randint(1, 99)
    letter = _rng.choice("ABCD")
    y1, y2 = _rng.sample(["a", "b", "c", "d"], 2)
    mau = _rng.randint(0, 8)
    if mau == 0:
        return f"Đáp án là {n} em nhé"
    if mau == 1:
        return f"Kết quả là {n}"
    if mau == 2:
        return f"Đáp số: {n} là kết quả bài toán này"
    if mau == 3:
        return f"The answer is {n}, well done"
    if mau == 4:
        return f"Em chọn {letter} là chính xác"
    if mau == 5:
        return f"Em hãy chọn phương án {letter} rồi nộp bài"
    if mau == 6:
        return f"Ý {y1} là đúng, ý {y2} là sai, em kiểm tra lại nhé"
    if mau == 7:
        return f"Vậy kết quả bằng {n} đúng không em"
    return f"Đáp án = {n} chính là điều em cần tìm"


def sinh_corpus(so_an_toan: int = 200, so_rui_ro: int = 50) -> list[dict]:
    ca: list[dict] = []
    _id = 0
    for _ in range(so_an_toan):
        _id += 1
        ca.append({"id": _id, "nhom": "an_toan", "noi_dung": _cau_an_toan(), "ky_vong_chan": False})
    for _ in range(so_rui_ro):
        _id += 1
        ca.append({"id": _id, "nhom": "rui_ro", "noi_dung": _cau_rui_ro(), "ky_vong_chan": True})
    return ca


CAC_CA = sinh_corpus()
