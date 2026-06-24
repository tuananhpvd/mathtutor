"""Tests cho orchestrator TN4PA và TNDS (Phase 3)."""


from app.core.matching.cas import KetQuaSoKhop
from app.core.matching.matcher import so_khop, so_khop_tnds_mot_y
from app.core.orchestrator.rules import xu_ly_tn4pa, xu_ly_tnds
from app.core.orchestrator.state import TrangThaiPhien

STEPS_TN4PA = [
    {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "chọn phương án",
     "bieu_thuc_ket_qua": "B", "danh_sach_goi_y": ["loại trừ A trước", "xét D cuối"]},
]

STEPS_TNDS = [
    {"thu_tu": 1, "pham_vi": "a", "mo_ta": "ý a", "bieu_thuc_ket_qua": "Dung",
     "danh_sach_goi_y": ["gợi ý a1", "gợi ý a2", "gợi ý a3"]},
    {"thu_tu": 1, "pham_vi": "b", "mo_ta": "ý b", "bieu_thuc_ket_qua": "Sai",
     "danh_sach_goi_y": ["gợi ý b1"]},
    {"thu_tu": 1, "pham_vi": "c", "mo_ta": "ý c", "bieu_thuc_ket_qua": "Dung",
     "danh_sach_goi_y": ["gợi ý c1"]},
    {"thu_tu": 1, "pham_vi": "d", "mo_ta": "ý d", "bieu_thuc_ket_qua": "Sai",
     "danh_sach_goi_y": ["gợi ý d1"]},
]


# ----- TN4PA -----

def make_tn4pa(**kw) -> TrangThaiPhien:
    return TrangThaiPhien(loai_cau="TN4PA", steps=STEPS_TN4PA, **kw)


def test_tn4pa_lan_dau():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, None, "")
    assert ct.y_dinh == "dinh_huong"
    assert "loại trừ A trước" in ct.y_goi_y


def test_tn4pa_dung():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "em chọn B vì...")
    assert ct.y_dinh == "ket_thuc"
    assert st2.da_xong is True


def test_tn4pa_sai_co_ly_giai():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "em thấy A đúng vì...")
    assert ct.y_dinh == "hoi_nguoc"
    assert st2.so_lan_sai_lien_tiep == 1


def test_tn4pa_chon_bua_kich_hoat():
    st = make_tn4pa()
    # Sai + không có nội dung → phát hiện chọn bừa trong service, ở đây test trực tiếp
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "", chon_bua=True)
    assert ct.y_dinh == "goi_y"
    assert "loại trừ" in ct.y_goi_y.lower() or "phân tích" in ct.y_goi_y.lower()


def test_tn4pa_yeu_cau_goi_y():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, None, "", yeu_cau_goi_y=True)
    assert ct.y_dinh == "goi_y"
    assert st2.cap_goi_y_hien_tai == 1


def test_tn4pa_so_khop_chinh_xac():
    du_lieu = {"dap_an_dung": "B", "phuong_an": {"A": "...", "B": "...", "C": "...", "D": "..."}}
    assert so_khop("TN4PA", "B", du_lieu).ket_qua == KetQuaSoKhop.DUNG
    assert so_khop("TN4PA", "b", du_lieu).ket_qua == KetQuaSoKhop.DUNG
    assert so_khop("TN4PA", "A", du_lieu).ket_qua == KetQuaSoKhop.SAI


# ----- TNDS -----

META_TNDS = {
    "y": [
        {"ky_hieu": "a", "noi_dung_y": "...", "dap_an": "Dung"},
        {"ky_hieu": "b", "noi_dung_y": "...", "dap_an": "Sai"},
        {"ky_hieu": "c", "noi_dung_y": "...", "dap_an": "Dung"},
        {"ky_hieu": "d", "noi_dung_y": "...", "dap_an": "Sai"},
    ]
}


def make_tnds(**kw) -> TrangThaiPhien:
    return TrangThaiPhien(loai_cau="TNDS", steps=STEPS_TNDS, **kw)


def test_tnds_khoi_dong_y_a():
    st = make_tnds()
    ct, st2 = xu_ly_tnds(st, None, "")
    assert st2.y_hien_tai == "a"
    assert ct.y_dinh == "dinh_huong"
    assert "gợi ý a1" in ct.y_goi_y


def test_tnds_dung_y_a_sang_b():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "em chọn Đúng")
    assert st2.trang_thai_y["a"] == "xong"
    assert st2.y_hien_tai == "b"
    assert ct.y_dinh == "xac_nhan_dung"


def test_tnds_sai_y_a_van_sang_b():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.SAI, "em chọn Sai")
    assert st2.trang_thai_y["a"] == "xong"
    assert st2.y_hien_tai == "b"
    assert ct.y_dinh == "chuyen_y"


def test_tnds_hoan_thanh_sau_4_y():
    st = make_tnds(y_hien_tai="d",
                   trang_thai_y={"a": "xong", "b": "xong", "c": "xong", "d": "dang_lam"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "Sai")
    assert st2.da_xong is True
    assert ct.y_dinh == "tom_tat"


def test_tnds_so_khop_mot_y():
    km = so_khop_tnds_mot_y("Dung", META_TNDS, "a")
    assert km.ket_qua == KetQuaSoKhop.DUNG
    km2 = so_khop_tnds_mot_y("Sai", META_TNDS, "a")
    assert km2.ket_qua == KetQuaSoKhop.SAI
    km3 = so_khop_tnds_mot_y("sai", META_TNDS, "b")
    assert km3.ket_qua == KetQuaSoKhop.DUNG


def test_tnds_so_khop_toan_bo_diem_bac_thang():
    # Toàn bộ 4 đúng
    km = so_khop("TNDS", {"a": "Dung", "b": "Sai", "c": "Dung", "d": "Sai"}, META_TNDS)
    assert km.ket_qua == KetQuaSoKhop.DUNG
    assert km.diem == 1.0

    # 3 đúng
    km2 = so_khop("TNDS", {"a": "Dung", "b": "Sai", "c": "Dung", "d": "Dung"}, META_TNDS)
    assert km2.diem == 0.5

    # 0 đúng
    km3 = so_khop("TNDS", {"a": "Sai", "b": "Dung", "c": "Sai", "d": "Dung"}, META_TNDS)
    assert km3.diem == 0.0


def test_tnds_khong_phan_tich():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.KHONG_PHAN_TICH_DUOC, "xyz")
    assert ct.y_dinh == "goi_y"
    assert "Đúng hoặc Sai" in ct.y_goi_y or "chọn" in ct.y_goi_y


def test_orchestrator_tnds_khong_import_llm():
    import ast
    import pathlib
    src = pathlib.Path("app/core/orchestrator/rules.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports = [
        n.names[0].name if isinstance(n, ast.Import) else n.module
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]
    assert not any("llm" in (imp or "") for imp in imports)
    assert not any("fastapi" in (imp or "") for imp in imports)
