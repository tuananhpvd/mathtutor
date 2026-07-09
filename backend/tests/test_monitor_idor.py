"""Regression IDOR — monitor.py PHẢI kiểm quyền sở hữu HS theo GV (bất biến #6,
CLAUDE.md mục 3: "GV chỉ thấy lớp mình"). Trước khi vá, cả 5 endpoint không lọc theo
GV — bất kỳ GV nào cũng đọc/sửa được cờ, hội thoại, nhật ký của HS lớp KHÁC."""

from app.auth.security import hash_password
from app.models.flag import Flag, LoaiCo, TrangThaiCo
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed_2_gv(db):
    """gv1 sở hữu hs1 (có 1 phiên hoàn thành + 1 cờ); gv2 là GV KHÁC, không liên quan."""
    lop1 = Lop(ten="12A1")
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin1",
                 mat_khau_hash=hash_password("pass"))
    db.add_all([lop1, admin])
    db.flush()

    gv1 = User(vai_tro=VaiTro.gv, ho_ten="GV Một", dang_nhap="gv1",
               mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV Hai", dang_nhap="gv2",
               mat_khau_hash=hash_password("pass"))
    db.add_all([gv1, gv2])
    db.flush()
    lop1.gv_id = gv1.id

    hs1 = User(vai_tro=VaiTro.hs, ho_ten="HS Của GV1", dang_nhap="hs1",
               mat_khau_hash=hash_password("pass"), lop_id=lop1.id)
    db.add(hs1)
    db.flush()

    p = Problem(chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
               loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
               nguoi_tao_id=gv1.id, meta={"dap_an_cuoi": "5"})
    db.add(p)
    db.flush()

    session = SessionModel(hoc_sinh_id=hs1.id, problem_id=p.id,
                           trang_thai=TrangThaiSession.hoan_thanh, buoc_hien_tai=1,
                           cap_goi_y_hien_tai=0, diem=10)
    db.add(session)
    db.flush()

    flag = Flag(session_id=session.id, loai_co=LoaiCo.thu_cong,
               trang_thai=TrangThaiCo.cho_xu_ly, ghi_chu="cần chú ý")
    db.add(flag)
    db.commit()
    return gv1, gv2, admin, hs1, session, flag


def test_gv_khac_khong_thay_co_cua_gv_khac(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv2 = _h(_login(client, "gv2"))

    flags = client.get("/api/monitor/flags", headers=h_gv2).json()
    assert flag.id not in [f["id"] for f in flags]


def test_gv_khac_khong_gan_co_cho_session_khong_thuoc(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv2 = _h(_login(client, "gv2"))

    r = client.post("/api/monitor/flags", headers=h_gv2,
                    params={"session_id": session.id, "ghi_chu": "chiếm quyền"})
    assert r.status_code == 403


def test_gv_khac_khong_sua_co_cua_gv_khac(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv2 = _h(_login(client, "gv2"))

    r = client.patch(f"/api/monitor/flags/{flag.id}", headers=h_gv2,
                     params={"trang_thai": "da_xu_ly"})
    assert r.status_code == 403


def test_gv_khac_khong_xem_hoi_thoai_cua_hs_khong_thuoc(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv2 = _h(_login(client, "gv2"))

    r = client.get(f"/api/monitor/sessions/{session.id}/turns", headers=h_gv2)
    assert r.status_code == 403


def test_gv_khac_khong_thay_nhat_ky_hoan_thanh_cua_gv_khac(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv2 = _h(_login(client, "gv2"))

    data = client.get("/api/monitor/sessions-hoan-thanh", headers=h_gv2).json()
    assert session.id not in [s["session_id"] for s in data]


def test_gv_chinh_chu_van_thao_tac_binh_thuong(db, client):
    """Vá IDOR không được làm hỏng luồng hợp lệ — gv1 vẫn thấy/sửa được dữ liệu của mình."""
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_gv1 = _h(_login(client, "gv1"))

    flags = client.get("/api/monitor/flags", headers=h_gv1).json()
    assert flag.id in [f["id"] for f in flags]

    r = client.patch(f"/api/monitor/flags/{flag.id}", headers=h_gv1,
                     params={"trang_thai": "da_xu_ly"})
    assert r.status_code == 200

    r = client.get(f"/api/monitor/sessions/{session.id}/turns", headers=h_gv1)
    assert r.status_code in (200, 404)  # 404 hợp lệ nếu không có turn nào, KHÔNG phải 403

    data = client.get("/api/monitor/sessions-hoan-thanh", headers=h_gv1).json()
    assert session.id in [s["session_id"] for s in data]


def test_admin_thay_toan_bo_khong_bi_loc(db, client):
    gv1, gv2, admin, hs1, session, flag = _seed_2_gv(db)
    h_admin = _h(_login(client, "admin1"))

    flags = client.get("/api/monitor/flags", headers=h_admin).json()
    assert flag.id in [f["id"] for f in flags]

    data = client.get("/api/monitor/sessions-hoan-thanh", headers=h_admin).json()
    assert session.id in [s["session_id"] for s in data]
