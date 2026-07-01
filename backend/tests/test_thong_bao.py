"""Tests A1: thông báo + nhận xét GV→HS (đồng hành GV↔HS)."""

from app.auth.security import hash_password
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _seed_gv(db):
    gv1 = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
               mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="Thầy Nam", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv1, gv2])
    db.commit()
    return gv1.id, gv2.id


def _tao_hs(client, h, lop_id, ho_ten, dn):
    return client.post("/api/gv/hoc-sinh", headers=h, json={
        "ho_ten": ho_ten, "dang_nhap": dn, "mat_khau": "password", "lop_id": lop_id,
    }).json()["id"]


def test_gv_gui_nhan_xet_hs_nhan_thong_bao(db, client):
    _seed_gv(db)
    h_gv = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv, lop_id, "HS A", "hsa")

    r = client.post("/api/gv/hoc-sinh/0/nhan-xet", headers=h_gv, json={"noi_dung": "x"})
    assert r.status_code == 400  # HS không tồn tại / không thuộc lớp

    hs_id = db.query(User).filter(User.dang_nhap == "hsa").first().id
    r = client.post(f"/api/gv/hoc-sinh/{hs_id}/nhan-xet", headers=h_gv,
                    json={"noi_dung": "Em làm tốt phần đạo hàm, cố lên nhé!"})
    assert r.status_code == 200, r.text

    h_hs = _h(client, "hsa")
    assert client.get("/api/thong-bao/chua-doc", headers=h_hs).json()["so_luong"] == 1
    ds = client.get("/api/thong-bao", headers=h_hs).json()
    assert len(ds) == 1
    assert ds[0]["loai"] == "nhan_xet"
    assert ds[0]["nguoi_gui_ten"] == "Cô Lan"
    assert ds[0]["da_doc"] is False
    assert "đạo hàm" in ds[0]["noi_dung"]


def test_nhan_xet_noi_dung_rong_bi_chan(db, client):
    _seed_gv(db)
    h_gv = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv, lop_id, "HS A", "hsa")
    hs_id = db.query(User).filter(User.dang_nhap == "hsa").first().id
    r = client.post(f"/api/gv/hoc-sinh/{hs_id}/nhan-xet", headers=h_gv, json={"noi_dung": "   "})
    assert r.status_code == 400


def test_gv_khac_lop_khong_duoc_nhan_xet(db, client):
    _seed_gv(db)
    h_gv1 = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv1, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv1, lop_id, "HS A", "hsa")
    hs_id = db.query(User).filter(User.dang_nhap == "hsa").first().id

    h_gv2 = _h(client, "gv2")
    r = client.post(f"/api/gv/hoc-sinh/{hs_id}/nhan-xet", headers=h_gv2,
                    json={"noi_dung": "Xin chào"})
    assert r.status_code == 400


def test_hs_danh_dau_da_doc(db, client):
    _seed_gv(db)
    h_gv = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv, lop_id, "HS A", "hsa")
    hs_id = db.query(User).filter(User.dang_nhap == "hsa").first().id
    client.post(f"/api/gv/hoc-sinh/{hs_id}/nhan-xet", headers=h_gv, json={"noi_dung": "abc"})

    h_hs = _h(client, "hsa")
    tb_id = client.get("/api/thong-bao", headers=h_hs).json()[0]["id"]
    assert client.post(f"/api/thong-bao/{tb_id}/da-doc", headers=h_hs).json()["ok"] is True
    assert client.get("/api/thong-bao/chua-doc", headers=h_hs).json()["so_luong"] == 0


def test_hs_chi_thay_thong_bao_cua_minh(db, client):
    _seed_gv(db)
    h_gv = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv, lop_id, "HS A", "hsa")
    _tao_hs(client, h_gv, lop_id, "HS B", "hsb")
    hsa_id = db.query(User).filter(User.dang_nhap == "hsa").first().id
    client.post(f"/api/gv/hoc-sinh/{hsa_id}/nhan-xet", headers=h_gv, json={"noi_dung": "cho A"})

    # HS B không thấy thông báo của HS A
    h_hsb = _h(client, "hsb")
    assert client.get("/api/thong-bao", headers=h_hsb).json() == []


def test_nhan_xet_nhap_tra_ve_noi_dung(db, client):
    _seed_gv(db)
    h_gv = _h(client, "gv1")
    lop_id = client.post("/api/gv/lop", headers=h_gv, json={"ten": "12A1"}).json()["id"]
    _tao_hs(client, h_gv, lop_id, "HS A", "hsa")
    hs_id = db.query(User).filter(User.dang_nhap == "hsa").first().id
    r = client.get(f"/api/gv/hoc-sinh/{hs_id}/nhan-xet-nhap", headers=h_gv)
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["noi_dung"], str) and len(r.json()["noi_dung"]) > 0
