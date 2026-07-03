"""Test CRUD API danh mục chuyên đề / dạng."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import CheDoSoKhopEnum, DoKho, LoaiCau, Problem
from app.models.user import User, VaiTro


def _seed_users(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_dm", mat_khau_hash=hash_password("pass"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_dm", mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin_dm", mat_khau_hash=hash_password("pass"))
    db.add_all([gv, hs, admin])
    db.flush()
    lop.gv_id = gv.id  # HS đọc danh mục của GV chủ nhiệm lớp
    db.commit()
    return gv, hs, admin


def _tok(client, dang_nhap):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": "pass"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_them_chuyen_de_gv(client, db):
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "gv_dm")
    r = client.post("/api/danh-muc/chuyen-de", json={"ten": "Hình học không gian", "thu_tu": 1}, headers=h)
    assert r.status_code == 200
    assert r.json()["ten"] == "Hình học không gian"


def test_them_chuyen_de_trung(client, db):
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "gv_dm")
    client.post("/api/danh-muc/chuyen-de", json={"ten": "Xác suất", "thu_tu": 1}, headers=h)
    r = client.post("/api/danh-muc/chuyen-de", json={"ten": "Xác suất", "thu_tu": 1}, headers=h)
    assert r.status_code == 400


def test_hs_khong_them_duoc_chuyen_de(client, db):
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "hs_dm")
    r = client.post("/api/danh-muc/chuyen-de", json={"ten": "Test", "thu_tu": 1}, headers=h)
    assert r.status_code == 403


def test_them_dang(client, db):
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "gv_dm")
    cd = client.post("/api/danh-muc/chuyen-de", json={"ten": "Xác suất", "thu_tu": 1}, headers=h).json()
    r = client.post("/api/danh-muc/dang", json={"chuyen_de_id": cd["id"], "ten": "Xác suất cổ điển", "thu_tu": 1}, headers=h)
    assert r.status_code == 200
    assert r.json()["ten"] == "Xác suất cổ điển"
    assert r.json()["chuyen_de_id"] == cd["id"]


def test_xoa_chuyen_de_con_dang_bi_chan(client, db):
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "gv_dm")
    cd = client.post("/api/danh-muc/chuyen-de", json={"ten": "Test CD", "thu_tu": 1}, headers=h).json()
    client.post("/api/danh-muc/dang", json={"chuyen_de_id": cd["id"], "ten": "Dạng A", "thu_tu": 1}, headers=h)
    r = client.delete(f"/api/danh-muc/chuyen-de/{cd['id']}", headers=h)
    assert r.status_code == 400
    assert "dạng" in r.json()["detail"]


def test_sua_ten_chuyen_de_cascade_problems(client, db):
    """Đổi tên chuyên đề phải cập nhật chuyen_de denormalized trên tất cả câu hỏi thuộc dạng đó."""
    gv, hs, admin = _seed_users(db)
    h = _tok(client, "gv_dm")
    cd = client.post("/api/danh-muc/chuyen-de", json={"ten": "Đại số", "thu_tu": 1}, headers=h).json()
    dang = client.post("/api/danh-muc/dang", json={"chuyen_de_id": cd["id"], "ten": "Phương trình", "thu_tu": 1}, headers=h).json()
    # Tạo câu hỏi thuộc dạng này để ghi chuyen_de = "Đại số"
    p = Problem(
        loai_cau=LoaiCau.TLN, do_kho=DoKho.de, de_bai="Tìm x",
        loai_dap_an_nhap="so", che_do_so_khop=CheDoSoKhopEnum.tuong_duong,
        dang_id=dang["id"], chuyen_de="Đại số", nguoi_tao_id=gv.id,
    )
    db.add(p); db.commit(); db.refresh(p)
    assert p.chuyen_de == "Đại số"
    # Đổi tên chuyên đề
    r = client.patch(f"/api/danh-muc/chuyen-de/{cd['id']}", json={"ten": "Đại số - Giải tích"}, headers=h)
    assert r.status_code == 200
    db.refresh(p)
    assert p.chuyen_de == "Đại số - Giải tích"


def test_lay_danh_muc(client, db):
    gv, hs, admin = _seed_users(db)
    h_gv = _tok(client, "gv_dm")
    h_hs = _tok(client, "hs_dm")
    cd = client.post("/api/danh-muc/chuyen-de", json={"ten": "Số phức", "thu_tu": 1}, headers=h_gv).json()
    client.post("/api/danh-muc/dang", json={"chuyen_de_id": cd["id"], "ten": "Dạng đại số", "thu_tu": 1}, headers=h_gv)
    # HS cũng đọc được
    r = client.get("/api/danh-muc", headers=h_hs)
    assert r.status_code == 200
    assert any(c["ten"] == "Số phức" for c in r.json())
