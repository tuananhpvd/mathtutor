"""Test API tóm tắt lý thuyết (Pha 1) — GV soạn/quản lý, HS chỉ xem bản hien=True."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.user import User, VaiTro


def _seed(db):
    """gv1 chủ nhiệm lop1 (hs1); gv2 là GV khác không liên quan."""
    gv1 = User(vai_tro=VaiTro.gv, ho_ten="GV1", dang_nhap="gv1_lt",
               mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_lt",
               mat_khau_hash=hash_password("pass"))
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin_lt",
                 mat_khau_hash=hash_password("pass"))
    db.add_all([gv1, gv2, admin])
    db.flush()
    lop1 = Lop(ten="12A1", gv_id=gv1.id)
    db.add(lop1)
    db.flush()
    hs1 = User(vai_tro=VaiTro.hs, ho_ten="HS1", dang_nhap="hs1_lt",
               mat_khau_hash=hash_password("pass"), lop_id=lop1.id)
    db.add(hs1)
    db.commit()
    return gv1, gv2, admin, hs1


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _tao_danh_muc(client, h_gv, ten_cd="Khảo sát hàm số", ten_dang="Cực trị"):
    cd = client.post("/api/danh-muc/chuyen-de", json={"ten": ten_cd, "thu_tu": 1}, headers=h_gv).json()
    d = client.post("/api/danh-muc/dang",
                    json={"chuyen_de_id": cd["id"], "ten": ten_dang, "thu_tu": 1}, headers=h_gv).json()
    return cd, d


def _body_toi_thieu(chuyen_de_id, dang_id=None, hien=False):
    return {
        "chuyen_de_id": chuyen_de_id, "dang_id": dang_id, "tieu_de": "Tóm tắt test",
        "noi_dung": "Công thức $x^2$.\n![minh họa](/uploads/x.png)",
        "tu_khoa": ["cực trị"], "hien": hien,
    }


def test_gv_tao_va_xem_danh_sach_cua_minh(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)

    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_gv1)
    assert r.status_code == 200, r.text
    tt_id = r.json()["id"]

    ds = client.get("/api/ly-thuyet/gv", headers=h_gv1).json()
    assert len(ds) == 1
    assert ds[0]["id"] == tt_id
    assert ds[0]["chuyen_de_ten"] == "Khảo sát hàm số"
    assert ds[0]["dang_ten"] == "Cực trị"
    assert ds[0]["hien"] is False


def test_tao_cap_chuyen_de_khong_dang(db, client):
    """dang_id=None → tóm tắt cấp chuyên đề, hợp lệ."""
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)

    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], dang_id=None), headers=h_gv1)
    assert r.status_code == 200, r.text
    ds = client.get("/api/ly-thuyet/gv", headers=h_gv1).json()
    assert ds[0]["dang_id"] is None
    assert ds[0]["dang_ten"] is None


def test_tao_dang_khong_thuoc_chuyen_de_bi_chan(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    cd1, d1 = _tao_danh_muc(client, h_gv1, "Chuyên đề A", "Dạng A")
    cd2, d2 = _tao_danh_muc(client, h_gv1, "Chuyên đề B", "Dạng B")

    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd1["id"], dang_id=d2["id"]), headers=h_gv1)
    assert r.status_code == 400
    assert "không thuộc" in r.json()["detail"]


def test_gv_khac_khong_tao_duoc_tren_chuyen_de_nguoi_khac(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_gv2 = _h(_login(client, "gv2_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)

    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_gv2)
    assert r.status_code == 403

    ds = client.get("/api/ly-thuyet/gv", headers=h_gv2).json()
    assert ds == []


def test_hs_chi_thay_ban_hien_true_cua_gv_chu_nhiem(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_hs1 = _h(_login(client, "hs1_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)

    an = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"], hien=False),
                     headers=h_gv1).json()
    hien = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"], hien=True),
                       headers=h_gv1).json()

    ds = client.get("/api/ly-thuyet/hs", headers=h_hs1).json()
    ids = [x["id"] for x in ds]
    assert hien["id"] in ids
    assert an["id"] not in ids


def test_hs_khong_thay_tom_tat_cua_gv_khac(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv2 = _h(_login(client, "gv2_lt"))
    h_hs1 = _h(_login(client, "hs1_lt"))
    cd, d = _tao_danh_muc(client, h_gv2)
    client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"], hien=True), headers=h_gv2)

    ds = client.get("/api/ly-thuyet/hs", headers=h_hs1).json()
    assert ds == []


def test_hs_loc_theo_chuyen_de_va_dang(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_hs1 = _h(_login(client, "hs1_lt"))
    cd1, d1 = _tao_danh_muc(client, h_gv1, "Chuyên đề A", "Dạng A")
    cd2, d2 = _tao_danh_muc(client, h_gv1, "Chuyên đề B", "Dạng B")
    tt1 = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd1["id"], d1["id"], hien=True),
                      headers=h_gv1).json()
    client.post("/api/ly-thuyet", json=_body_toi_thieu(cd2["id"], d2["id"], hien=True), headers=h_gv1)

    r = client.get(f"/api/ly-thuyet/hs?chuyen_de_id={cd1['id']}", headers=h_hs1)
    ds = r.json()
    assert len(ds) == 1 and ds[0]["id"] == tt1["id"]

    r2 = client.get(f"/api/ly-thuyet/hs?dang_id={d1['id']}", headers=h_hs1)
    assert len(r2.json()) == 1


def test_hs_khong_tao_duoc(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_hs1 = _h(_login(client, "hs1_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)
    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_hs1)
    assert r.status_code == 403


def test_sua_va_xoa(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)
    tt = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_gv1).json()

    r = client.patch(f"/api/ly-thuyet/{tt['id']}", json={"hien": True, "tieu_de": "Đã sửa"},
                     headers=h_gv1)
    assert r.status_code == 200
    ds = client.get("/api/ly-thuyet/gv", headers=h_gv1).json()
    assert ds[0]["hien"] is True and ds[0]["tieu_de"] == "Đã sửa"

    r2 = client.delete(f"/api/ly-thuyet/{tt['id']}", headers=h_gv1)
    assert r2.status_code == 200
    assert client.get("/api/ly-thuyet/gv", headers=h_gv1).json() == []


def test_gv_khac_khong_sua_xoa_duoc(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_gv2 = _h(_login(client, "gv2_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)
    tt = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_gv1).json()

    assert client.patch(f"/api/ly-thuyet/{tt['id']}", json={"hien": True},
                        headers=h_gv2).status_code == 403
    assert client.delete(f"/api/ly-thuyet/{tt['id']}", headers=h_gv2).status_code == 403


def test_admin_toan_quyen(db, client):
    gv1, gv2, admin, hs1 = _seed(db)
    h_gv1 = _h(_login(client, "gv1_lt"))
    h_admin = _h(_login(client, "admin_lt"))
    cd, d = _tao_danh_muc(client, h_gv1)

    # Admin tạo trên chuyên đề của GV1 → chủ sở hữu vẫn là gv1 (giống quy ước dang/danh_muc)
    r = client.post("/api/ly-thuyet", json=_body_toi_thieu(cd["id"], d["id"]), headers=h_admin)
    assert r.status_code == 200, r.text
    tt_id = r.json()["id"]

    ds_gv1 = client.get("/api/ly-thuyet/gv", headers=h_gv1).json()
    assert any(x["id"] == tt_id for x in ds_gv1)

    assert client.patch(f"/api/ly-thuyet/{tt_id}", json={"hien": True},
                        headers=h_admin).status_code == 200
    assert client.delete(f"/api/ly-thuyet/{tt_id}", headers=h_admin).status_code == 200
