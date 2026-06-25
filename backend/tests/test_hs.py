"""Tests hồ sơ cá nhân học sinh: xem & cập nhật trong phạm vi của mình."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _seed(db):
    lop = Lop(ten="12A1", gv_id=None)
    db.add(lop)
    db.commit()
    hs = User(vai_tro=VaiTro.hs, ho_ten="Trò A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    db.commit()
    return hs.id


def test_hs_xem_ho_so(db, client):
    _seed(db)
    r = client.get("/api/hs/ho-so", headers=_h(client, "hs1")).json()
    assert r["dang_nhap"] == "hs1"
    assert r["lop_ten"] == "12A1"
    assert r["trang_thai"] == "hoat_dong"


def test_hs_sua_ho_ten_va_mat_khau(db, client):
    _seed(db)
    h = _h(client, "hs1")
    client.patch("/api/hs/ho-so", headers=h, json={"ho_ten": "Trò A1", "mat_khau": "moi123"})
    r = client.get("/api/hs/ho-so", headers=h).json()
    assert r["ho_ten"] == "Trò A1"
    # mật khẩu mới đăng nhập được
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs1", "mat_khau": "moi123"}).status_code == 200


def test_hs_khong_thay_doi_duoc_trang_thai_qua_ho_so(db, client):
    _seed(db)
    h = _h(client, "hs1")
    # gửi kèm trang_thai sẽ bị bỏ qua (schema không nhận)
    client.patch("/api/hs/ho-so", headers=h, json={"ho_ten": "X", "trang_thai": "khoa"})
    r = client.get("/api/hs/ho-so", headers=h).json()
    assert r["trang_thai"] == "hoat_dong"


def test_gv_khong_goi_duoc_api_hs(db, client):
    _seed(db)
    db.add(User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gvx",
                mat_khau_hash=hash_password("password")))
    db.commit()
    assert client.get("/api/hs/ho-so", headers=_h(client, "gvx")).status_code == 403
