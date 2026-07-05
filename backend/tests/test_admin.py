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


def test_stats_llm_provider_theo_cau_hinh_db_khong_phai_env(db, client):
    """Bug đã sửa: badge Dashboard từng đọc settings.llm_provider (env, luôn 'stub'
    trong test) thay vì cấu hình Admin đã lưu trong DB — khiến hiện sai provider
    thật đang chạy (get_llm_client ưu tiên đọc DB, không đọc settings)."""
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    # Chưa cấu hình gì trong DB → dùng mặc định CAU_HINH_MAC_DINH (gemini), không phải "stub".
    r = client.get("/api/admin/stats", headers=h)
    assert r.json()["llm_provider"] == "gemini"

    # Admin đổi provider trong Cấu hình → Dashboard phải phản ánh đúng ngay.
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_provider", "gia_tri": "anthropic"})
    r = client.get("/api/admin/stats", headers=h)
    assert r.json()["llm_provider"] == "anthropic"


def test_gan_lop_cho_tai_khoan(db, client):
    _seed(db)
    from app.models.lop import Lop
    lop = Lop(ten="12A1")
    db.add(lop)
    db.commit()
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    lops = client.get("/api/admin/lop", headers=h).json()
    assert any(item["ten"] == "12A1" for item in lops)

    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    r = client.patch(f"/api/admin/users/{hs.id}/lop", headers=h, json={"lop_id": lop.id})
    assert r.status_code == 200 and r.json()["lop_id"] == lop.id

    users = client.get("/api/admin/users", headers=h).json()
    u = next(x for x in users if x["dang_nhap"] == "hs1")
    assert u["lop_ten"] == "12A1"


def test_crud_lop_va_quan_ly(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    gv = db.query(User).filter_by(dang_nhap="gv1").first()

    # Tạo lớp gán GV
    r = client.post("/api/admin/lop", headers=h, json={"ten": "12A2", "gv_id": gv.id})
    assert r.status_code == 200, r.text
    lop_id = r.json()["id"]

    # Danh sách lớp chi tiết có GV
    lct = client.get("/api/admin/lop-chi-tiet", headers=h).json()
    lop = next(x for x in lct if x["id"] == lop_id)
    assert lop["gv_ten"] == "Cô Lan" and lop["so_hoc_sinh"] == 0

    # Gán học sinh vào lớp
    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    client.patch(f"/api/admin/users/{hs.id}/lop", headers=h, json={"lop_id": lop_id})

    # Quản lý theo giáo viên: GV có lớp + học sinh
    gvs = client.get("/api/admin/giao-vien", headers=h).json()
    g = next(x for x in gvs if x["id"] == gv.id)
    assert any(lp["id"] == lop_id and len(lp["hoc_sinhs"]) == 1 for lp in g["lops"])

    # Quản lý theo học sinh: có lop_ten + gv_ten
    hss = client.get("/api/admin/hoc-sinh", headers=h).json()
    hrow = next(x for x in hss if x["id"] == hs.id)
    assert hrow["lop_ten"] == "12A2" and hrow["gv_ten"] == "Cô Lan"

    # Sửa lớp: đổi tên + gỡ GV
    client.patch(f"/api/admin/lop/{lop_id}", headers=h, json={"ten": "12A3", "gv_id": None})
    lct = client.get("/api/admin/lop-chi-tiet", headers=h).json()
    lop = next(x for x in lct if x["id"] == lop_id)
    assert lop["ten"] == "12A3" and lop["gv_id"] is None

    # Xóa lớp → học sinh bị gỡ khỏi lớp
    client.delete(f"/api/admin/lop/{lop_id}", headers=h)
    hss = client.get("/api/admin/hoc-sinh", headers=h).json()
    assert next(x for x in hss if x["id"] == hs.id)["lop_id"] is None


def test_sua_va_xoa_tai_khoan(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    hs = db.query(User).filter_by(dang_nhap="hs1").first()

    # Sửa họ tên + đổi mật khẩu
    r = client.patch(f"/api/admin/users/{hs.id}", headers=h,
                     json={"ho_ten": "HS Mới", "mat_khau": "moi123"})
    assert r.status_code == 200 and r.json()["ho_ten"] == "HS Mới"
    # Đăng nhập bằng mật khẩu mới
    assert client.post("/api/auth/login",
                       json={"dang_nhap": "hs1", "mat_khau": "moi123"}).status_code == 200

    # Xóa HS chưa có phiên → OK
    assert client.delete(f"/api/admin/users/{hs.id}", headers=h).status_code == 200
    assert not db.query(User).filter_by(dang_nhap="hs1").first()


def test_xoa_hs_co_phien_bi_chan(db, client):
    _seed(db)
    from app.models.problem import Problem, TrangThaiDuyet
    from app.models.session import Session as S
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    hs = db.query(User).filter_by(dang_nhap="hs1").first()
    p = Problem(chuyen_de="X", loai_cau="TLN", do_kho="tb", de_bai="?",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                meta={"dap_an_cuoi": "1"})
    db.add(p)
    db.flush()
    db.add(S(hoc_sinh_id=hs.id, problem_id=p.id))
    db.commit()
    r = client.delete(f"/api/admin/users/{hs.id}", headers=h)
    assert r.status_code == 400 and "Khóa" in r.json()["detail"]


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


def test_cau_hinh_llm_provider_va_khoa_an(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'admin')}"}

    # Mặc định provider gemini; khóa chưa đặt
    r = client.get("/api/admin/config", headers=h).json()
    assert r["llm_provider"] == "gemini"
    assert r["llm_api_key_gemini_da_dat"] is False
    assert "llm_api_key_gemini" not in r  # KHÔNG lộ khóa nguyên văn

    # Đặt khóa Gemini → cờ da_dat = True, vẫn không lộ khóa
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_api_key_gemini", "gia_tri": "AIza-secret-123"})
    r2 = client.get("/api/admin/config", headers=h).json()
    assert r2["llm_api_key_gemini_da_dat"] is True
    assert "AIza-secret-123" not in str(r2)

    # Gửi khóa rỗng KHÔNG xóa khóa cũ
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_api_key_gemini", "gia_tri": ""})
    assert client.get("/api/admin/config", headers=h).json()["llm_api_key_gemini_da_dat"] is True

    # Đổi provider sang anthropic
    client.patch("/api/admin/config", headers=h,
                 json={"khoa": "llm_provider", "gia_tri": "anthropic"})
    assert client.get("/api/admin/config", headers=h).json()["llm_provider"] == "anthropic"


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
