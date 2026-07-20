"""Mã mời lớp — sinh & chuẩn hóa (Pha A của luồng "HS tự đăng ký bằng mã lớp").

Mã được THẦY CÔ ĐỌC cho cả lớp chép, nên hai thứ phải chắc: (a) không chứa ký tự dễ đọc
nhầm, (b) HS gõ kiểu gì (chữ thường, có gạch, có khoảng trắng) cũng khớp.
"""

from app.core.ma_lop import BANG_CHU, DO_DAI, chuan_hoa, dinh_dang, hop_le, sinh_ma


def test_sinh_ma_dung_do_dai_va_bang_chu():
    for _ in range(200):
        ma = sinh_ma()
        assert len(ma) == DO_DAI
        assert all(c in BANG_CHU for c in ma)


def test_bang_chu_khong_co_ky_tu_de_doc_nham():
    """0/O và 1/I/L là nguồn sai phổ biến nhất khi chép mã đọc miệng."""
    for c in "01OIL":
        assert c not in BANG_CHU
    assert len(set(BANG_CHU)) == len(BANG_CHU)  # không trùng ký tự


def test_sinh_ma_khong_lap_lai_trong_mau_lon():
    """Không phải test tính ngẫu nhiên mật mã, chỉ chốt là không sinh ra hằng số."""
    assert len({sinh_ma() for _ in range(500)}) > 490


def test_chuan_hoa_chap_nhan_moi_kieu_go_cua_hs():
    goc = "A7K3QM9X"
    for bien_the in ("a7k3qm9x", "A7K3-QM9X", "a7k3 qm9x", "  A7K3–QM9X  ", "A7K3.QM9X"):
        assert chuan_hoa(bien_the) == goc


def test_chuan_hoa_rong_va_none():
    assert chuan_hoa(None) == ""
    assert chuan_hoa("") == ""
    assert chuan_hoa("---") == ""


def test_dinh_dang_chia_nhom_4_de_doc():
    assert dinh_dang("A7K3QM9X") == "A7K3-QM9X"
    assert dinh_dang("a7k3qm9x") == "A7K3-QM9X"
    assert dinh_dang(None) == ""


def test_dinh_dang_va_chuan_hoa_di_duoc_ca_hai_chieu():
    """Mã hiển thị cho GV chép về phải chuẩn hóa ngược đúng bản gốc."""
    for _ in range(50):
        ma = sinh_ma()
        assert chuan_hoa(dinh_dang(ma)) == ma


def test_hop_le():
    assert hop_le(sinh_ma())
    assert hop_le("A7K3-QM9X")
    assert not hop_le("A7K3")          # ngắn
    assert not hop_le("A7K3QM9XZZ")    # dài
    assert not hop_le("")
    assert not hop_le(None)
    # Ký tự ngoài bảng chữ bị loại → còn thiếu độ dài, không được coi là hợp lệ
    assert not hop_le("O0IL1OIL")
