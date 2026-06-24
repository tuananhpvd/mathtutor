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


def test_tn4pa_chon_ngay_dung():
    # Không bắt buộc suy luận → chọn đáp án luôn, đúng → kết thúc
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "em chọn B",
                          bat_buoc_suy_luan=False, la_chon_dap_an=True)
    assert ct.y_dinh == "ket_thuc"
    assert st2.da_xong is True


def test_tn4pa_chon_ngay_sai():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "em chọn A",
                          bat_buoc_suy_luan=False, la_chon_dap_an=True)
    assert ct.y_dinh == "hoi_nguoc"
    assert st2.so_lan_sai_lien_tiep == 1
    assert st2.da_xong is False


def test_tn4pa_bat_buoc_chua_lam_buoc_thi_chan_chon():
    # Bắt buộc suy luận nhưng HS bấm chọn đáp án ngay → bị chặn, nhắc làm bước trước
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "em chọn B",
                          bat_buoc_suy_luan=True, la_chon_dap_an=True)
    assert ct.y_dinh == "goi_y"
    assert st2.da_xong is False
    assert st2.buoc_hien_tai == 1  # chưa mở khóa


def test_tn4pa_bat_buoc_lam_dung_buoc_mo_khoa_roi_chon():
    st = make_tn4pa()
    # Pha 1: nhập biểu thức bước đúng → mở khóa
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.DUNG, "y' = ...",
                          bat_buoc_suy_luan=True, la_chon_dap_an=False)
    assert ct.y_dinh == "xac_nhan_dung"
    assert st2.buoc_hien_tai > 1
    # Pha 2: chọn đáp án đúng → kết thúc
    ct2, st3 = xu_ly_tn4pa(st2, KetQuaSoKhop.DUNG, "em chọn B",
                           bat_buoc_suy_luan=True, la_chon_dap_an=True)
    assert ct2.y_dinh == "ket_thuc"
    assert st3.da_xong is True


def test_tn4pa_bat_buoc_lam_sai_buoc():
    st = make_tn4pa()
    ct, st2 = xu_ly_tn4pa(st, KetQuaSoKhop.SAI, "y' = sai",
                          bat_buoc_suy_luan=True, la_chon_dap_an=False)
    assert ct.y_dinh == "hoi_nguoc"
    assert st2.so_lan_sai_lien_tiep == 1
    assert st2.buoc_hien_tai == 1  # chưa mở khóa


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


def test_tnds_chot_dung_y_a_sang_b():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "em chọn Đúng", la_chon_dung_sai=True)
    assert st2.trang_thai_y["a"] == "xong"
    assert st2.y_hien_tai == "b"
    assert st2.so_y_dung == 1
    assert ct.y_dinh == "xac_nhan_dung"


def test_tnds_chot_sai_y_a_o_lai():
    # Mới: chốt sai thì PHẢI làm lại ý a, không chuyển sang b
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.SAI, "em chọn Sai", la_chon_dung_sai=True)
    assert st2.trang_thai_y["a"] == "dang_lam"
    assert st2.y_hien_tai == "a"
    assert ct.y_dinh == "hoi_nguoc"


def test_tnds_bat_buoc_suy_luan_chan_chot_truoc_khi_suy_luan():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "Đúng",
                         bat_buoc_suy_luan_y=True, la_chon_dung_sai=True)
    assert ct.y_dinh == "goi_y"  # chưa suy luận → chặn
    assert st2.trang_thai_y["a"] == "dang_lam"


def test_tnds_bat_buoc_suy_luan_dung_roi_chot():
    st = make_tnds(y_hien_tai="a",
                   trang_thai_y={"a": "dang_lam", "b": "chua", "c": "chua", "d": "chua"})
    # Pha suy luận đúng → mở khóa
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "y'=...",
                         bat_buoc_suy_luan_y=True, la_chon_dung_sai=False)
    assert ct.y_dinh == "xac_nhan_dung"
    assert st2.da_suy_luan is True
    # Chốt Đúng → sang ý b
    ct2, st3 = xu_ly_tnds(st2, KetQuaSoKhop.DUNG, "Đúng",
                          bat_buoc_suy_luan_y=True, la_chon_dung_sai=True)
    assert st3.y_hien_tai == "b"
    assert st3.da_suy_luan is False  # reset cho ý mới


def test_tnds_hoan_thanh_sau_4_y():
    st = make_tnds(y_hien_tai="d",
                   trang_thai_y={"a": "xong", "b": "xong", "c": "xong", "d": "dang_lam"})
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.DUNG, "Sai", la_chon_dung_sai=True)
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
    ct, st2 = xu_ly_tnds(st, KetQuaSoKhop.KHONG_PHAN_TICH_DUOC, "xyz", la_chon_dung_sai=True)
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
