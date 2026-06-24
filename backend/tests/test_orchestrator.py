"""Test core/orchestrator với bài TLN (Phase 2)."""

from app.core.matching.cas import KetQuaSoKhop
from app.core.orchestrator.rules import xu_ly_tln
from app.core.orchestrator.state import TrangThaiPhien

STEPS_TLN = [
    {
        "thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm",
        "bieu_thuc_ket_qua": "3*x**2-3",
        "danh_sach_goi_y": ["gợi 1", "gợi 2", "gợi 3"],
    },
    {
        "thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Giải f'(x)=0",
        "bieu_thuc_ket_qua": "1",
        "danh_sach_goi_y": ["gợi a", "gợi b", "gợi c"],
    },
    {
        "thu_tu": 3, "pham_vi": "ca_bai", "mo_ta": "So sánh",
        "bieu_thuc_ket_qua": "20",
        "danh_sach_goi_y": ["gợi x", "gợi y", "gợi z"],
    },
]


def _state(buoc=1, cap=0, sai=0, khong_hieu=0):
    return TrangThaiPhien(
        loai_cau="TLN",
        buoc_hien_tai=buoc,
        cap_goi_y_hien_tai=cap,
        so_lan_sai_lien_tiep=sai,
        so_lan_khong_hieu=khong_hieu,
        steps=STEPS_TLN,
    )


def test_lan_dau_dinh_huong():
    chi_thi, st = xu_ly_tln(_state(), None, "")
    assert chi_thi.y_dinh == "dinh_huong"
    assert chi_thi.cap_goi_y == 0
    assert chi_thi.buoc == 1
    # rang_buoc luôn có
    assert chi_thi.rang_buoc != ""
    # y_goi_y không chứa bieu_thuc_ket_qua
    assert "3*x**2-3" not in chi_thi.y_goi_y


def test_hs_dung_buoc1_sang_buoc2():
    chi_thi, st = xu_ly_tln(_state(), KetQuaSoKhop.DUNG, "đạo hàm = 3x^2-3")
    assert chi_thi.y_dinh == "xac_nhan_dung"
    assert st.buoc_hien_tai == 2
    assert st.cap_goi_y_hien_tai == 0


def test_hs_sai_hoi_nguoc():
    chi_thi, st = xu_ly_tln(_state(), KetQuaSoKhop.SAI, "em tính được 3x")
    assert chi_thi.y_dinh == "hoi_nguoc"
    assert st.so_lan_sai_lien_tiep == 1
    assert st.buoc_hien_tai == 1  # không sang bước


def test_yeu_cau_goi_y_tang_dan():
    st = _state()
    # Lần 1
    chi_thi, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert chi_thi.cap_goi_y == 1
    assert chi_thi.y_goi_y == "gợi 2"
    # Lần 2
    chi_thi, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert chi_thi.cap_goi_y == 2
    assert chi_thi.y_goi_y == "gợi 3"
    # Lần 3 — đã hết (3 gợi ý, max index = 2), dừng tại index 2
    chi_thi, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert chi_thi.cap_goi_y == 2  # không vượt
    assert chi_thi.y_goi_y == "gợi 3"


def test_goi_y_cuoi_khong_chua_ket_qua():
    st = _state(cap=2)
    chi_thi, _ = xu_ly_tln(st, None, "", yeu_cau_goi_y=False)
    assert "3*x**2-3" not in chi_thi.y_goi_y
    assert "20" not in chi_thi.y_goi_y


def test_ket_thuc_sau_buoc_cuoi():
    # Đang ở bước 3 (bước cuối), HS trả lời đúng
    st = _state(buoc=3)
    chi_thi, st_moi = xu_ly_tln(st, KetQuaSoKhop.DUNG, "20")
    assert chi_thi.y_dinh == "ket_thuc"
    assert st_moi.da_xong is True


def test_2_goi_y_dung_dung():
    """Kiểm với bước chỉ có 2 gợi ý — cap_goi_y dừng ở index 1."""
    steps_2 = [{"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "test",
                 "bieu_thuc_ket_qua": "x", "danh_sach_goi_y": ["g1", "g2"]}]
    st = TrangThaiPhien(loai_cau="TLN", steps=steps_2)
    _, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert st.cap_goi_y_hien_tai == 1
    _, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert st.cap_goi_y_hien_tai == 1  # dừng, không vượt


def test_4_goi_y_dung_dung():
    """Kiểm với bước có 4 gợi ý — cap_goi_y dừng ở index 3."""
    steps_4 = [{"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "test",
                 "bieu_thuc_ket_qua": "x", "danh_sach_goi_y": ["g1", "g2", "g3", "g4"]}]
    st = TrangThaiPhien(loai_cau="TLN", steps=steps_4)
    for _ in range(5):
        _, st = xu_ly_tln(st, None, "", yeu_cau_goi_y=True)
    assert st.cap_goi_y_hien_tai == 3  # max index = 3


def test_orchestrator_khong_import_llm():
    import app.core.orchestrator.rules as r

    src = open(r.__file__, encoding="utf-8").read()
    assert "llm" not in src.lower() or "llm" not in src  # không import llm
