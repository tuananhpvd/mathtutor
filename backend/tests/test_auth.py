
from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.user import User, VaiTro


def seed_users(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()

    users = [
        User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
             mat_khau_hash=hash_password("admin123")),
        User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
             mat_khau_hash=hash_password("gv123")),
        User(vai_tro=VaiTro.hs, ho_ten="Học sinh A", dang_nhap="hs1",
             mat_khau_hash=hash_password("hs123"), lop_id=lop.id),
    ]
    lop.gv_id = None  # gv chưa có id lúc này
    for u in users:
        db.add(u)
    db.commit()

    # Gắn GV
    gv = db.query(User).filter(User.dang_nhap == "gv1").first()
    lop.gv_id = gv.id
    db.commit()
    return users


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_admin(client, db):
    seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "admin123"})
    assert r.status_code == 200
    data = r.json()
    assert data["vai_tro"] == "admin"
    assert "access_token" in data


def test_login_gv(client, db):
    seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "gv1", "mat_khau": "gv123"})
    assert r.status_code == 200
    assert r.json()["vai_tro"] == "gv"


def test_login_hs(client, db):
    seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "hs1", "mat_khau": "hs123"})
    assert r.status_code == 200
    assert r.json()["vai_tro"] == "hs"


def test_login_wrong_password(client, db):
    seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "wrong"})
    assert r.status_code == 401


def test_login_wrong_user(client, db):
    seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "nobody", "mat_khau": "x"})
    assert r.status_code == 401


def _get_token(client, dang_nhap, mat_khau):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": mat_khau})
    return r.json()["access_token"]


def test_role_admin_route(client, db):
    seed_users(db)
    token = _get_token(client, "admin", "admin123")
    r = client.get("/api/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_role_block_hs_from_admin(client, db):
    seed_users(db)
    token = _get_token(client, "hs1", "hs123")
    r = client.get("/api/admin/ping", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_role_block_gv_from_hs_route(client, db):
    seed_users(db)
    token = _get_token(client, "gv1", "gv123")
    r = client.get("/api/hs/ping", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_no_token_returns_403_or_401(client):
    r = client.get("/api/admin/ping")
    assert r.status_code in (401, 403)
