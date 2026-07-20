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

# Đăng ký bằng mã lớp (endpoint CÔNG KHAI): khóa theo IP và CHỈ đếm lần nhập mã SAI.
# Vì sao đếm-lần-sai lại quan trọng ở đây: cả lớp 40 em thường đăng ký cùng lúc qua cùng một
# IP (NAT của trường/nhà mạng). Nếu đếm mọi lượt gọi thì sẽ khóa oan cả lớp; đếm lần SAI thì
# lớp nhập đúng mã không sinh lần sai nào → không bao giờ bị chặn, còn kẻ dò mã chỉ tạo ra
# lần sai nên bị chặn rất nhanh. Ngưỡng rộng hơn login vì HS gõ nhầm mã là chuyện thường.
SO_LAN_SAI_MA_TOI_DA = 10
CUA_SO_MA_GIAY = 600  # 10 phút

_lan_sai: dict[str, list[float]] = defaultdict(list)
_lan_sai_ma: dict[str, list[float]] = defaultdict(list)


def _don_dep_bucket(bucket: dict[str, list[float]], khoa: str, cua_so: int) -> list[float]:
    now = time.time()
    lan = bucket[khoa]
    lan[:] = [t for t in lan if now - t < cua_so]
    return lan


def _don_dep(dang_nhap: str) -> list[float]:
    return _don_dep_bucket(_lan_sai, dang_nhap, CUA_SO_GIAY)


def qua_nguong(dang_nhap: str) -> bool:
    """True nếu tài khoản này vừa sai mật khẩu quá SO_LAN_SAI_TOI_DA lần trong CUA_SO_GIAY."""
    return len(_don_dep(dang_nhap)) >= SO_LAN_SAI_TOI_DA


def ghi_nhan_sai(dang_nhap: str) -> None:
    _don_dep(dang_nhap).append(time.time())


def xoa_lich_su_sai(dang_nhap: str) -> None:
    _lan_sai.pop(dang_nhap, None)


# ----- Đăng ký bằng mã lớp -----

def qua_nguong_ma(khoa: str) -> bool:
    """True nếu IP này đã nhập SAI mã quá nhiều lần trong cửa sổ."""
    return len(_don_dep_bucket(_lan_sai_ma, khoa, CUA_SO_MA_GIAY)) >= SO_LAN_SAI_MA_TOI_DA


def ghi_nhan_sai_ma(khoa: str) -> None:
    _don_dep_bucket(_lan_sai_ma, khoa, CUA_SO_MA_GIAY).append(time.time())


def xoa_lich_su_sai_ma(khoa: str) -> None:
    _lan_sai_ma.pop(khoa, None)
