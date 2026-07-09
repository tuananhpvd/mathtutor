"""Test GĐ3A: CAS tự phân tích hàm số để vẽ đồ thị (app/core/ve_hinh.py + API /ve-do-thi)."""

import pytest

from app.auth.security import hash_password
from app.core.ve_hinh import du_lieu_do_thi, phan_tich_ham_so
from app.models.user import User, VaiTro

# ---------- Core: phan_tich_ham_so (đối chiếu tính tay) ----------

def test_da_thuc_bac_3_2_cuc_tri():
    tt = phan_tich_ham_so("x**3 - 3*x + 1")
    assert tt["moc"] == [-1.0, 1.0]
    cuc_tri = {c["loai"]: (c["x"], c["y"]) for c in tt["cuc_tri"]}
    assert cuc_tri["cuc_dai"] == (-1.0, 3.0)
    assert cuc_tri["cuc_tieu"] == (1.0, -1.0)
    assert tt["tiem_can_dung"] == []
    assert tt["tiem_can_ngang"] is None


def test_trung_phuong_bac_4_3_cuc_tri():
    tt = phan_tich_ham_so("x**4 - 2*x**2")
    loai_theo_x = {c["x"]: c["loai"] for c in tt["cuc_tri"]}
    assert loai_theo_x[-1.0] == "cuc_tieu"
    assert loai_theo_x[0.0] == "cuc_dai"
    assert loai_theo_x[1.0] == "cuc_tieu"


def test_phan_thuc_b1_b1_tiem_can_dung_ngang():
    tt = phan_tich_ham_so("(2*x - 1)/(x + 1)")
    assert tt["tiem_can_dung"] == [-1.0]
    assert tt["tiem_can_ngang"] == 2.0
    assert tt["tiem_can_xien"] is None
    assert tt["cuc_tri"] == []  # b1/b1 luôn đơn điệu trên từng nhánh


def test_phan_thuc_b2_b1_tiem_can_xien():
    tt = phan_tich_ham_so("(x**2 - 2*x + 3)/(x - 1)")
    assert tt["tiem_can_dung"] == [1.0]
    assert tt["tiem_can_ngang"] is None
    assert tt["tiem_can_xien"] == {"a": 1.0, "b": -1.0}
    assert len(tt["cuc_tri"]) == 2


def test_ham_khong_tiem_can_dung_van_co_cuc_tri():
    tt = phan_tich_ham_so("1/(x**2+1)")  # TXĐ = R, không tiệm cận đứng
    assert tt["tiem_can_dung"] == []
    assert tt["tiem_can_ngang"] == 0.0
    assert tt["cuc_tri"] == [{"x": 0.0, "y": 1.0, "loai": "cuc_dai"}]


# ---------- Core: gia_tri_bien (hàng "y" bảng biến thiên — GĐ3B) ----------

def test_gia_tri_bien_da_thuc_bac_3():
    tt = phan_tich_ham_so("x**3 - 3*x + 1")
    gtb = tt["gia_tri_bien"]
    assert gtb[0] == {"vi_tri": "-oo", "gia_tri": {"loai": "vo_cuc_am", "gia_tri": None}}
    assert gtb[1] == {"vi_tri": -1.0, "gia_tri": {"loai": "so", "gia_tri": 3.0}}
    assert gtb[2] == {"vi_tri": 1.0, "gia_tri": {"loai": "so", "gia_tri": -1.0}}
    assert gtb[3] == {"vi_tri": "+oo", "gia_tri": {"loai": "vo_cuc_duong", "gia_tri": None}}


def test_gia_tri_bien_gian_doan_tai_tiem_can_dung():
    """Tại tiệm cận đứng: giới hạn TRÁI và PHẢI phải tách riêng (hàm không xác định đúng tại đó)."""
    tt = phan_tich_ham_so("(2*x - 1)/(x + 1)")
    gtb = tt["gia_tri_bien"]
    assert gtb[0] == {"vi_tri": "-oo", "gia_tri": {"loai": "so", "gia_tri": 2.0}}
    diem_gian_doan = gtb[1]
    assert diem_gian_doan["vi_tri"] == -1.0
    assert diem_gian_doan["trai"] == {"loai": "vo_cuc_duong", "gia_tri": None}
    assert diem_gian_doan["phai"] == {"loai": "vo_cuc_am", "gia_tri": None}
    assert gtb[2] == {"vi_tri": "+oo", "gia_tri": {"loai": "so", "gia_tri": 2.0}}


def test_gia_tri_bien_tiem_can_xien():
    tt = phan_tich_ham_so("(x**2 - 2*x + 3)/(x - 1)")
    gtb = tt["gia_tri_bien"]
    assert gtb[0]["gia_tri"]["loai"] == "vo_cuc_am"
    assert gtb[-1]["gia_tri"]["loai"] == "vo_cuc_duong"
    diem_gian_doan = next(g for g in gtb if g.get("vi_tri") == 1.0)
    assert diem_gian_doan["trai"]["loai"] == "vo_cuc_am"
    assert diem_gian_doan["phai"]["loai"] == "vo_cuc_duong"


@pytest.mark.parametrize("bieu_thuc", [
    "sqrt(x)",
    "log(x)",
    "sin(x)",
    "x**2 + m*x",   # chứa tham số
    "x**10",        # vượt bậc tối đa
    "",
    "__import__('os')",
])
def test_ngoai_pham_vi_bao_loi_ro_rang(bieu_thuc):
    with pytest.raises(ValueError):
        phan_tich_ham_so(bieu_thuc)


# ---------- Core: du_lieu_do_thi (điểm mẫu) ----------

def test_do_thi_tach_doan_tai_tiem_can_dung():
    """Không được nối 1 đường xuyên qua tiệm cận đứng."""
    d = du_lieu_do_thi("(2*x - 1)/(x + 1)")
    assert len(d["cac_doan"]) == 2
    for doan in d["cac_doan"]:
        assert len(doan) >= 2
        for x, _y in doan:
            assert abs(x - (-1.0)) > 0.001  # không có điểm nào sát tiệm cận lọt vào


def test_do_thi_ham_lien_tuc_1_doan():
    d = du_lieu_do_thi("x**3 - 3*x + 1", cua_so=(-3, 3))
    assert len(d["cac_doan"]) == 1
    assert d["cua_so"]["x_min"] == -3
    assert d["cua_so"]["x_max"] == 3


def test_do_thi_cua_so_x_khong_hop_le():
    with pytest.raises(ValueError):
        du_lieu_do_thi("x", cua_so=(5, 1))


def test_do_thi_khung_y_khong_bi_keo_boi_diem_gan_tiem_can():
    """Trước khi sửa: y_max từng vọt lên ~58 do lấy min/max mọi điểm mẫu sát tiệm cận."""
    d = du_lieu_do_thi("(2*x - 1)/(x + 1)")
    assert d["cua_so"]["y_max"] < 10
    assert d["cua_so"]["y_min"] > -10


def test_do_thi_cuc_tri_nam_trong_khung_y():
    d = du_lieu_do_thi("x**3 - 3*x + 1")
    for c in d["cuc_tri"]:
        assert d["cua_so"]["y_min"] <= c["y"] <= d["cua_so"]["y_max"]


# ---------- API /api/problems/ve-do-thi ----------

def _seed_users(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_vh", mat_khau_hash=hash_password("pass"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_vh", mat_khau_hash=hash_password("pass"))
    db.add_all([gv, hs])
    db.commit()
    return gv, hs


def _tok(client, dang_nhap):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": "pass"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_api_ve_do_thi_gv_ok(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/ve-do-thi", json={"bieu_thuc": "x**3 - 3*x + 1"}, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert len(data["cuc_tri"]) == 2
    assert len(data["cac_doan"]) >= 1
    assert "cua_so" in data


def test_api_ve_do_thi_hs_bi_cam(client, db):
    _seed_users(db)
    h = _tok(client, "hs_vh")
    r = client.post("/api/problems/ve-do-thi", json={"bieu_thuc": "x**2"}, headers=h)
    assert r.status_code == 403


def test_api_ve_do_thi_ham_ngoai_pham_vi_tra_400(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/ve-do-thi", json={"bieu_thuc": "sin(x)"}, headers=h)
    assert r.status_code == 400
    assert "chưa hỗ trợ" in r.json()["detail"].lower() or "lượng giác" in r.json()["detail"].lower()


def test_api_ve_do_thi_x_window_tuy_chinh(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post(
        "/api/problems/ve-do-thi",
        json={"bieu_thuc": "x**3 - 3*x + 1", "x_min": -3, "x_max": 3},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["cua_so"]["x_min"] == -3
    assert r.json()["cua_so"]["x_max"] == 3


def test_api_ve_do_thi_x_window_khong_hop_le(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post(
        "/api/problems/ve-do-thi",
        json={"bieu_thuc": "x", "x_min": 5, "x_max": 1},
        headers=h,
    )
    assert r.status_code == 400


# ---------- API /api/problems/ve-bbt (GĐ3B) ----------

def test_api_ve_bbt_gv_ok(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/ve-bbt", json={"bieu_thuc": "x**3 - 3*x + 1"}, headers=h)
    assert r.status_code == 200
    data = r.json()
    assert len(data["cuc_tri"]) == 2
    assert len(data["gia_tri_bien"]) == 4  # -oo, 2 mốc, +oo
    assert "cac_doan" not in data  # /ve-bbt không lấy điểm mẫu (khác /ve-do-thi)


def test_api_ve_bbt_hs_bi_cam(client, db):
    _seed_users(db)
    h = _tok(client, "hs_vh")
    r = client.post("/api/problems/ve-bbt", json={"bieu_thuc": "x**2"}, headers=h)
    assert r.status_code == 403


def test_api_ve_bbt_ham_ngoai_pham_vi_tra_400(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/ve-bbt", json={"bieu_thuc": "log(x)"}, headers=h)
    assert r.status_code == 400


# ---------- API /api/problems/latex-sang-sympy ----------

def test_api_latex_sang_sympy_gv_ok(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/latex-sang-sympy", json={"latex": r"\sqrt{2}"}, headers=h)
    assert r.status_code == 200
    assert r.json()["sympy"] == "sqrt(2)"


def test_api_latex_sang_sympy_cac_cong_thuc_hay_gap(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    truong_hop = [
        (r"x^{2}", "x**2"),
        (r"\frac{1}{2}", "1/2"),
        (r"\sin(x)", "sin(x)"),
    ]
    for latex, sympy_ky_vong in truong_hop:
        r = client.post("/api/problems/latex-sang-sympy", json={"latex": latex}, headers=h)
        assert r.status_code == 200, r.text
        assert r.json()["sympy"] == sympy_ky_vong


def test_api_latex_sang_sympy_hs_bi_cam(client, db):
    _seed_users(db)
    h = _tok(client, "hs_vh")
    r = client.post("/api/problems/latex-sang-sympy", json={"latex": "x"}, headers=h)
    assert r.status_code == 403


def test_api_latex_sang_sympy_khong_parse_duoc_tra_400(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/latex-sang-sympy", json={"latex": r"\frac{1"}, headers=h)
    assert r.status_code == 400
    # Thông báo phải gọn, KHÔNG lộ dump lỗi ANTLR gốc (dài, tiếng Anh, có dấu ^^^ chỉ vị trí)
    # — GV không đọc hiểu được, từng thấy khi test tay trên UI.
    chi_tiet = r.json()["detail"]
    assert "^^^" not in chi_tiet
    assert len(chi_tiet) < 100


def test_api_latex_sang_sympy_rong_tra_422(client, db):
    _seed_users(db)
    h = _tok(client, "gv_vh")
    r = client.post("/api/problems/latex-sang-sympy", json={"latex": ""}, headers=h)
    assert r.status_code == 422
