"""Chặn dò mật khẩu (brute-force) bằng cửa sổ trượt trong bộ nhớ — không cần thêm
dependency mới (khớp phong cách dự án dùng thư viện tối giản: PyJWT/passlib thuần thay
vì framework auth nặng). Đủ dùng cho quy mô 1 trường/1 instance Render; khởi động lại
app thì bộ đếm reset — chấp nhận được, không phải hổng bảo mật (Render không restart
theo từng request).

Khóa theo TÊN ĐĂNG NHẬP (không theo IP) vì HS dùng chung mạng trường/nhà mạng NAT dễ
đụng IP giữa nhiều tài khoản hợp lệ — khóa theo IP sẽ khóa oan cả lớp.
"""

import time
from collections import defaultdict

SO_LAN_SAI_TOI_DA = 5
CUA_SO_GIAY = 300  # 5 phút

_lan_sai: dict[str, list[float]] = defaultdict(list)


def _don_dep(dang_nhap: str) -> list[float]:
    now = time.time()
    lan = _lan_sai[dang_nhap]
    lan[:] = [t for t in lan if now - t < CUA_SO_GIAY]
    return lan


def qua_nguong(dang_nhap: str) -> bool:
    """True nếu tài khoản này vừa sai mật khẩu quá SO_LAN_SAI_TOI_DA lần trong CUA_SO_GIAY."""
    return len(_don_dep(dang_nhap)) >= SO_LAN_SAI_TOI_DA


def ghi_nhan_sai(dang_nhap: str) -> None:
    _don_dep(dang_nhap).append(time.time())


def xoa_lich_su_sai(dang_nhap: str) -> None:
    _lan_sai.pop(dang_nhap, None)
