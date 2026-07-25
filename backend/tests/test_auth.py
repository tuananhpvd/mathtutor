
import bcrypt

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
    assert r.json()["db"] is True


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


def test_doi_mat_khau_vo_hieu_hoa_token_cu(client, db):
    """Điểm trừ bảo mật #1: đổi mật khẩu → MỌI JWT phát trước đó hết hiệu lực ngay
    (trước đây token cũ vẫn sống tới 8h vì JWT stateless không mang token_version)."""
    seed_users(db)
    token_cu = _get_token(client, "hs1", "hs123")
    h = {"Authorization": f"Bearer {token_cu}"}
    # Token còn dùng được TRƯỚC khi đổi mật khẩu
    assert client.get("/api/hs/ho-so", headers=h).status_code == 200
    # HS tự đổi mật khẩu (request này qua auth TRƯỚC khi version tăng nên vẫn 200)
    r = client.patch("/api/hs/ho-so", headers=h, json={"mat_khau": "matkhaumoi"})
    assert r.status_code == 200
    # Token cũ giờ đã hết hiệu lực (version lệch)
    assert client.get("/api/hs/ho-so", headers=h).status_code == 401
    # Đăng nhập lại bằng mật khẩu mới → token mới dùng được bình thường
    token_moi = _get_token(client, "hs1", "matkhaumoi")
    assert client.get(
        "/api/hs/ho-so", headers={"Authorization": f"Bearer {token_moi}"}
    ).status_code == 200


def test_token_doi_truoc_khong_co_tv_van_dung_duoc(client, db):
    """Tương thích ngược: token đời trước (KHÔNG có claim 'tv') vẫn hợp lệ khi tài khoản chưa
    từng đổi mật khẩu (token_version=0) — không đá văng ai lúc mới triển khai tính năng này."""
    from app.auth.security import create_access_token

    seed_users(db)
    hs = db.query(User).filter(User.dang_nhap == "hs1").first()
    token_khong_tv = create_access_token({"sub": str(hs.id), "vai_tro": hs.vai_tro.value})
    r = client.get("/api/hs/ho-so", headers={"Authorization": f"Bearer {token_khong_tv}"})
    assert r.status_code == 200


def test_khoa_tai_khoan_vo_hieu_hoa_token_ca_sau_khi_mo_lai(client, db):
    """Khóa tài khoản = công tắc thu hồi THẬT: token cũ chết ngay (do bị khóa), VÀ vẫn chết cả
    sau khi MỞ khóa lại (version đã tăng) — tránh token bị lộ 'sống lại' khi mở khóa về sau."""
    from app.services.admin_service import doi_trang_thai_tai_khoan

    seed_users(db)
    hs = db.query(User).filter(User.dang_nhap == "hs1").first()
    token = _get_token(client, "hs1", "hs123")
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/hs/ho-so", headers=h).status_code == 200
    # Khóa → token cũ 401
    doi_trang_thai_tai_khoan(db, hs.id, "khoa")
    assert client.get("/api/hs/ho-so", headers=h).status_code == 401
    # Mở khóa lại → token cũ VẪN 401 (không sống lại); đăng nhập lại mới dùng được
    doi_trang_thai_tai_khoan(db, hs.id, "hoat_dong")
    assert client.get("/api/hs/ho-so", headers=h).status_code == 401
    token_moi = _get_token(client, "hs1", "hs123")
    assert client.get(
        "/api/hs/ho-so", headers={"Authorization": f"Bearer {token_moi}"}
    ).status_code == 200


def test_bcrypt_ghim_duoi_4_0():
    """`passlib` 1.7.4 (chưa có bản vá chính thức) crash với bcrypt>=4.0 (mất
    thuộc tính `__about__` nội bộ mà passlib dựa vào) — pyproject.toml đang ghim
    cứng `bcrypt>=3.2,<4.0` để tránh việc này. Test này canh gác: nếu dependency
    resolver lỡ nới ghim (vd 1 gói khác đòi bcrypt>=4), CI báo lỗi NGAY ở đây
    thay vì để sập âm thầm ngay tại chỗ đăng nhập/đăng ký trên production."""
    major = int(bcrypt.__version__.split(".")[0])
    assert major < 4, (
        f"bcrypt {bcrypt.__version__} — passlib 1.7.4 không tương thích bcrypt>=4.0, "
        "kiểm tra lại ghim 'bcrypt>=3.2,<4.0' trong pyproject.toml trước khi deploy."
    )
