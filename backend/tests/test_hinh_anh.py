"""Test tính năng ảnh minh họa câu hỏi (Giai đoạn 1): upload + tạo/sửa + HS xem."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.user import User, VaiTro

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32  # magic PNG hợp lệ


def _seed_users(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_h", mat_khau_hash=hash_password("pass"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_h",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add_all([gv, hs])
    db.flush()
    lop.gv_id = gv.id  # HS thuộc lớp của GV → xem được bài GV tạo
    db.commit()
    return gv, hs


def _tok(client, dang_nhap):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": "pass"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _tao_bai_tln(client, headers, hinh_anh=None):
    body = {
        "loai_cau": "TLN", "do_kho": "de", "chuyen_de": "Tích phân",
        "de_bai": "Tính $\\int_0^1 x\\,dx$.", "meta": {"dap_an_cuoi": "0,5"},
    }
    if hinh_anh is not None:
        body["hinh_anh"] = hinh_anh
    return client.post("/api/problems", json=body, headers=headers)


# ---------- Upload ----------

def test_upload_hinh_gv_ok(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.uploads.UPLOADS_DIR", tmp_path)
    _seed_users(db)
    h = _tok(client, "gv_h")
    r = client.post("/api/problems/upload-hinh",
                    files={"file": ("a.png", PNG, "image/png")}, headers=h)
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.startswith("/uploads/") and url.endswith(".png")
    # File thật đã được lưu vào thư mục (tmp)
    assert (tmp_path / url.split("/")[-1]).exists()


def test_upload_hinh_qua_lon(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.uploads.UPLOADS_DIR", tmp_path)
    _seed_users(db)
    h = _tok(client, "gv_h")
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (3 * 1024 * 1024)  # > 3MB
    r = client.post("/api/problems/upload-hinh",
                    files={"file": ("big.png", big, "image/png")}, headers=h)
    assert r.status_code == 400
    assert "3MB" in r.json()["detail"]


def test_upload_hinh_sai_dinh_dang(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.uploads.UPLOADS_DIR", tmp_path)
    _seed_users(db)
    h = _tok(client, "gv_h")
    r = client.post("/api/problems/upload-hinh",
                    files={"file": ("x.txt", b"khong phai anh", "image/png")}, headers=h)
    assert r.status_code == 400  # dù content-type nói png, magic bytes không khớp


def test_upload_hinh_hs_bi_cam(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.uploads.UPLOADS_DIR", tmp_path)
    _seed_users(db)
    h = _tok(client, "hs_h")
    r = client.post("/api/problems/upload-hinh",
                    files={"file": ("a.png", PNG, "image/png")}, headers=h)
    assert r.status_code == 403  # chỉ GV/Admin được upload


# ---------- Tạo / sửa / HS xem ----------

def test_tao_cau_hoi_co_hinh(client, db):
    _seed_users(db)
    h = _tok(client, "gv_h")
    r = _tao_bai_tln(client, h, hinh_anh="/uploads/abc.png")
    assert r.status_code == 200
    pid = r.json()["id"]
    # GV xem chi tiết → có hinh_anh
    ct = client.get(f"/api/problems/{pid}", headers=h)
    assert ct.status_code == 200
    assert ct.json()["hinh_anh"] == "/uploads/abc.png"


def test_hs_xem_cau_hoi_co_hinh_khong_lo_dap_an(client, db):
    gv, hs = _seed_users(db)
    hg = _tok(client, "gv_h")
    pid = _tao_bai_tln(client, hg, hinh_anh="/uploads/abc.png").json()["id"]
    # HS xem → thấy hình nhưng KHÔNG lộ đáp án cuối
    hh = _tok(client, "hs_h")
    r = client.get(f"/api/problems/{pid}", headers=hh)
    assert r.status_code == 200
    data = r.json()
    assert data["hinh_anh"] == "/uploads/abc.png"
    assert "dap_an_cuoi" not in (data.get("meta") or {})
    assert "dap_an_cuoi" not in str(data)


def test_sua_go_hinh(client, db):
    _seed_users(db)
    h = _tok(client, "gv_h")
    pid = _tao_bai_tln(client, h, hinh_anh="/uploads/abc.png").json()["id"]
    # Gỡ ảnh: gửi hinh_anh = null
    r = client.patch(f"/api/problems/{pid}", json={"hinh_anh": None}, headers=h)
    assert r.status_code == 200
    assert r.json()["hinh_anh"] is None
