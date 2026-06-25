"""Tests phân quyền giáo viên: hồ sơ, quản lý lớp & học sinh trong phạm vi."""

from app.auth.security import hash_password
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _seed(db):
    gv1 = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
               mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="Thầy Nam", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv1, gv2])
    db.commit()
    return gv1.id, gv2.id


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def test_gv_ho_so_xem_va_sua(db, client):
    _seed(db)
    h = _h(client, "gv1")
    r = client.get("/api/gv/ho-so", headers=h).json()
    assert r["dang_nhap"] == "gv1" and r["trang_thai"] == "hoat_dong"
    client.patch("/api/gv/ho-so", headers=h, json={"ho_ten": "Cô Lan A", "mat_khau": "moi123"})
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "gv1", "mat_khau": "moi123"}).status_code == 200


def test_gv_quan_ly_lop_va_hoc_sinh(db, client):
    _seed(db)
    h = _h(client, "gv1")
    # Tạo lớp
    lop_id = client.post("/api/gv/lop", headers=h, json={"ten": "12A1"}).json()["id"]
    # Tạo học sinh trong lớp
    r = client.post("/api/gv/hoc-sinh", headers=h,
                    json={"ho_ten": "HS A", "dang_nhap": "hsa", "mat_khau": "pass123", "lop_id": lop_id})
    assert r.status_code == 200, r.text
    hs_id = r.json()["id"]
    # Danh sách HS của GV
    hss = client.get("/api/gv/hoc-sinh", headers=h).json()
    assert len(hss) == 1 and hss[0]["lop_ten"] == "12A1"
    # Sửa + khóa
    client.patch(f"/api/gv/hoc-sinh/{hs_id}", headers=h, json={"ho_ten": "HS A1"})
    client.patch(f"/api/gv/hoc-sinh/{hs_id}/trang-thai", headers=h, json={"trang_thai": "khoa"})
    hss = client.get("/api/gv/hoc-sinh", headers=h).json()
    assert hss[0]["ho_ten"] == "HS A1" and hss[0]["trang_thai"] == "khoa"
    # Xóa (chưa có phiên) → OK
    assert client.delete(f"/api/gv/hoc-sinh/{hs_id}", headers=h).status_code == 200


def test_gv_khong_quan_ly_hoc_sinh_lop_khac(db, client):
    gv1_id, gv2_id = _seed(db)
    # gv2 tạo lớp + học sinh
    h2 = _h(client, "gv2")
    lop2 = client.post("/api/gv/lop", headers=h2, json={"ten": "12B"}).json()["id"]
    hs2 = client.post("/api/gv/hoc-sinh", headers=h2,
                      json={"ho_ten": "HS B", "dang_nhap": "hsb", "mat_khau": "pass123", "lop_id": lop2}
                      ).json()["id"]
    # gv1 KHÔNG được sửa/xóa học sinh của gv2
    h1 = _h(client, "gv1")
    assert client.patch(f"/api/gv/hoc-sinh/{hs2}", headers=h1, json={"ho_ten": "x"}).status_code == 400
    assert client.delete(f"/api/gv/hoc-sinh/{hs2}", headers=h1).status_code == 400
    # gv1 KHÔNG được sửa/xóa lớp của gv2
    assert client.patch(f"/api/gv/lop/{lop2}", headers=h1, json={"ten": "x"}).status_code == 400
    assert client.delete(f"/api/gv/lop/{lop2}", headers=h1).status_code == 400


def test_gv_tao_hs_phai_chon_lop_cua_minh(db, client):
    gv1_id, gv2_id = _seed(db)
    h2 = _h(client, "gv2")
    lop2 = client.post("/api/gv/lop", headers=h2, json={"ten": "12B"}).json()["id"]
    # gv1 tạo HS vào lớp của gv2 → chặn
    h1 = _h(client, "gv1")
    r = client.post("/api/gv/hoc-sinh", headers=h1,
                    json={"ho_ten": "X", "dang_nhap": "x1", "mat_khau": "pass123", "lop_id": lop2})
    assert r.status_code == 400


def test_hs_khong_goi_duoc_api_gv(db, client):
    _seed(db)
    db.add(User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hsx",
                mat_khau_hash=hash_password("password")))
    db.commit()
    h = _h(client, "hsx")
    assert client.get("/api/gv/lop", headers=h).status_code == 403
