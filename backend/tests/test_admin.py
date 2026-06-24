"""Tests Phase 10 — API quản trị."""

from app.auth.security import hash_password
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _seed(db):
    admin = User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
                 mat_khau_hash=hash_password("password"))
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"))
    db.add_all([admin, gv, hs])
    db.commit()


def test_stats_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/stats", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["so_nguoi_dung"] == 3
    assert data["so_giao_vien"] == 1
    assert data["so_hoc_sinh"] == 1


def test_stats_phan_quyen_chan_gv_hs(db, client):
    _seed(db)
    for dn in ["gv1", "hs1"]:
        h = {"Authorization": f"Bearer {_login(client, dn)}"}
        assert client.get("/api/admin/stats", headers=h).status_code == 403


def test_tao_va_khoa_tai_khoan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "HS Mới", "dang_nhap": "hs99", "mat_khau": "1234", "vai_tro": "hs"})
    assert r.status_code == 200
    uid = r.json()["id"]

    # đăng nhập được
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs99", "mat_khau": "1234"}).status_code == 200

    # khóa
    r2 = client.patch(f"/api/admin/users/{uid}/trang-thai", headers=h,
                      json={"trang_thai": "khoa"})
    assert r2.status_code == 200
    assert r2.json()["trang_thai"] == "khoa"

    # bị khóa → login 403
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs99", "mat_khau": "1234"}).status_code == 403


def test_tao_tai_khoan_trung_dang_nhap(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.post("/api/admin/users", headers=h, json={
        "ho_ten": "Trùng", "dang_nhap": "gv1", "mat_khau": "1234", "vai_tro": "gv"})
    assert r.status_code == 400


def test_khong_khoa_duoc_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    admin = db.query(User).filter(User.dang_nhap == "admin").first()
    r = client.patch(f"/api/admin/users/{admin.id}/trang-thai", headers=h,
                     json={"trang_thai": "khoa"})
    assert r.status_code == 400


def test_cau_hinh_get_va_set(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    r = client.get("/api/admin/config", headers=h)
    assert r.status_code == 200
    assert "nguong_co_khong_hieu" in r.json()
    assert "bang_bac_thang" in r.json()

    r2 = client.patch("/api/admin/config", headers=h,
                      json={"khoa": "nguong_co_khong_hieu", "gia_tri": 5})
    assert r2.status_code == 200
    assert r2.json()["nguong_co_khong_hieu"] == 5

    # đọc lại vẫn còn
    assert client.get("/api/admin/config", headers=h).json()["nguong_co_khong_hieu"] == 5


def test_cau_hinh_khoa_khong_hop_le(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.patch("/api/admin/config", headers=h,
                     json={"khoa": "khoa_la", "gia_tri": 1})
    assert r.status_code == 400


def test_users_list_admin(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    r = client.get("/api/admin/users", headers=h)
    assert r.status_code == 200
    assert len(r.json()) == 3
