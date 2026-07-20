"""Mã mời lớp học — sinh & chuẩn hóa (TẤT ĐỊNH, thuần Python).

Dùng cho luồng "HS tự đăng ký bằng mã lớp": GV sinh mã, đọc cho cả lớp, HS tự tạo tài khoản
và vào đúng lớp — bỏ được nút thắt "phải chờ GV nhập tay từng em" mà KHÔNG phá vỡ chuỗi
trách nhiệm (mọi HS vẫn thuộc một lớp có GV phụ trách).

Không import web/DB/LLM để test được độc lập.
"""

import secrets

# Bảng chữ CỐ Ý bỏ ký tự dễ đọc nhầm khi thầy cô đọc mã cho cả lớp chép:
#   0/O, 1/I/L. Giữ số 2-9 và chữ cái còn lại → 31 ký tự.
BANG_CHU = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
DO_DAI = 8
_NHOM = 4  # hiển thị theo nhóm 4 ký tự: A7K3-QM9X

# Không gian mã = 31^8 ≈ 8,5×10^11 → dò mù bất khả thi trong giới hạn throttle.


def sinh_ma(do_dai: int = DO_DAI) -> str:
    """Sinh mã ngẫu nhiên an toàn (secrets, KHÔNG dùng random) dạng chuẩn hóa, chưa có gạch."""
    return "".join(secrets.choice(BANG_CHU) for _ in range(do_dai))


def chuan_hoa(ma: str | None) -> str:
    """Đưa mã người dùng gõ về dạng so khớp được.

    Chấp nhận mọi kiểu gõ thực tế của HS: chữ thường, có gạch nối, có khoảng trắng
    ("a7k3-qm9x", "A7K3 QM9X" → "A7K39M9X"...). Ký tự không thuộc bảng chữ bị loại bỏ để
    tránh việc HS gõ nhầm dấu câu là hỏng cả mã.
    """
    if not ma:
        return ""
    return "".join(c for c in ma.strip().upper() if c in BANG_CHU)


def dinh_dang(ma: str | None) -> str:
    """Dạng hiển thị cho GV đọc/chép: chèn gạch mỗi 4 ký tự (A7K3-QM9X)."""
    sach = chuan_hoa(ma)
    if not sach:
        return ""
    return "-".join(sach[i:i + _NHOM] for i in range(0, len(sach), _NHOM))


def hop_le(ma: str | None) -> bool:
    """Mã có đúng độ dài & chỉ gồm ký tự trong bảng chữ (sau chuẩn hóa)."""
    return len(chuan_hoa(ma)) == DO_DAI
