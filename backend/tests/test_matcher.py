
from app.core.matching.cas import KetQuaSoKhop
from app.core.matching.matcher import so_khop


# ---- TN4PA ----
def test_tn4pa_dung():
    r = so_khop("TN4PA", "B", {"dap_an_dung": "B"}, "tuong_duong")
    assert r.ket_qua == KetQuaSoKhop.DUNG


def test_tn4pa_sai():
    r = so_khop("TN4PA", "A", {"dap_an_dung": "B"}, "tuong_duong")
    assert r.ket_qua == KetQuaSoKhop.SAI


# ---- TNDS ----
Y_BAI_103 = [
    {"ky_hieu": "a", "dap_an": "Dung"},
    {"ky_hieu": "b", "dap_an": "Dung"},
    {"ky_hieu": "c", "dap_an": "Dung"},
    {"ky_hieu": "d", "dap_an": "Sai"},
]


def test_tnds_4_dung():
    nhap = {"a": "Dung", "b": "Dung", "c": "Dung", "d": "Sai"}
    r = so_khop("TNDS", nhap, {"y": Y_BAI_103})
    assert r.diem == 1.0


def test_tnds_3_dung():
    nhap = {"a": "Dung", "b": "Sai", "c": "Dung", "d": "Sai"}
    r = so_khop("TNDS", nhap, {"y": Y_BAI_103})
    assert r.diem == 0.5


def test_tnds_0_dung():
    nhap = {"a": "Sai", "b": "Sai", "c": "Sai", "d": "Dung"}
    r = so_khop("TNDS", nhap, {"y": Y_BAI_103})
    assert r.diem == 0.0


# ---- TLN ----
def test_tln_dung_nguyen():
    r = so_khop("TLN", "20", {"dap_an_cuoi": "20"})
    assert r.ket_qua == KetQuaSoKhop.DUNG


def test_tln_dung_float():
    r = so_khop("TLN", "20.0", {"dap_an_cuoi": "20"})
    assert r.ket_qua == KetQuaSoKhop.DUNG


def test_tln_sai():
    r = so_khop("TLN", "19", {"dap_an_cuoi": "20"})
    assert r.ket_qua == KetQuaSoKhop.SAI


def test_tln_chu():
    r = so_khop("TLN", "hai muoi", {"dap_an_cuoi": "20"})
    assert r.ket_qua == KetQuaSoKhop.KHONG_PHAN_TICH_DUOC


# ---- Smoke kiến trúc ----
def test_matching_khong_import_fastapi():
    import app.core.matching.matcher as m

    src = open(m.__file__, encoding="utf-8").read()
    assert "fastapi" not in src
    assert "llm" not in src


def test_matching_khong_import_llm():
    import app.core.matching.cas as c
    src = open(c.__file__, encoding="utf-8").read()
    assert "llm" not in src
