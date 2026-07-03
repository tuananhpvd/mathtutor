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


def test_sua_truong_khac_giu_nguyen_hinh_anh(client, db):
    """Sửa câu hỏi mà KHÔNG gửi hinh_anh (vd chỉ đổi độ khó) phải giữ nguyên ảnh cũ —
    phân biệt "không gửi trường" (giữ nguyên) với "gửi null" (gỡ ảnh, xem test_sua_go_hinh)."""
    _seed_users(db)
    h = _tok(client, "gv_h")
    pid = _tao_bai_tln(client, h, hinh_anh="/uploads/abc.png").json()["id"]
    r = client.patch(f"/api/problems/{pid}", json={"do_kho": "kho"}, headers=h)
    assert r.status_code == 200
    assert r.json()["hinh_anh"] == "/uploads/abc.png"
    assert r.json()["do_kho"] == "kho"


def test_danh_sach_gv_co_hinh_anh(client, db):
    """Danh sách câu hỏi của GV phải có hinh_anh để hiện chỉ báo 🖼️ — trước đây thiếu trường này."""
    _seed_users(db)
    h = _tok(client, "gv_h")
    _tao_bai_tln(client, h, hinh_anh="/uploads/abc.png")
    _tao_bai_tln(client, h)
    r = client.get("/api/problems", headers=h)
    assert r.status_code == 200
    rows = r.json()
    co_hinh = [row for row in rows if row["hinh_anh"]]
    khong_hinh = [row for row in rows if not row["hinh_anh"]]
    assert len(co_hinh) == 1 and co_hinh[0]["hinh_anh"] == "/uploads/abc.png"
    assert len(khong_hinh) == 1


# ---------- Import hàng loạt có ảnh (GĐ2) ----------

def test_import_batch_co_hinh(client, db):
    _seed_users(db)
    h = _tok(client, "gv_h")
    items = [
        {
            "loai_cau": "TLN", "chuyen_de": "Tích phân", "do_kho": "de",
            "de_bai": "Tính $\\int_0^1 x\\,dx$.", "hinh_anh": "/uploads/bbt.png",
            "meta": {"dap_an_cuoi": "0,5"},
        },
        {  # câu không ảnh vẫn import bình thường
            "loai_cau": "TLN", "chuyen_de": "Tích phân", "do_kho": "de",
            "de_bai": "Tính $\\int_0^2 x\\,dx$.", "meta": {"dap_an_cuoi": "2"},
        },
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=h)
    assert r.status_code == 200
    assert r.json()["da_tao"] == 2
    ids = r.json()["ids"]
    ct0 = client.get(f"/api/problems/{ids[0]}", headers=h).json()
    ct1 = client.get(f"/api/problems/{ids[1]}", headers=h).json()
    assert ct0["hinh_anh"] == "/uploads/bbt.png"
    assert ct1["hinh_anh"] is None
