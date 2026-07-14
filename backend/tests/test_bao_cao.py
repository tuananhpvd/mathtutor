"""Tests — xuất báo cáo kết quả HS cho phụ huynh (Mô hình C, GV in ra PDF).

Kiểm: cổng cấu hình (mặc định TẮT → 403), Admin luôn được, phân quyền GV chỉ lớp mình,
và lọc theo khoảng thời gian (tu_ngay/den_ngay theo bat_dau_luc của phiên)."""

from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import User, VaiTro
from app.services.admin_service import dat_cau_hinh


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed(db):
    """gv1 chủ nhiệm lop1 (hs1); gv2 lớp khác; 1 admin. hs1 có 2 phiên hoàn thành ở 2 mốc."""
    gv1 = User(vai_tro=VaiTro.gv, ho_ten="GV Một", dang_nhap="gv1",
               mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV Hai", dang_nhap="gv2",
               mat_khau_hash=hash_password("pass"))
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin1",
                 mat_khau_hash=hash_password("pass"))
    db.add_all([gv1, gv2, admin])
    db.flush()
    lop1 = Lop(ten="12A1", gv_id=gv1.id)
    db.add(lop1)
    db.flush()
    hs1 = User(vai_tro=VaiTro.hs, ho_ten="HS Một", dang_nhap="hs1",
               mat_khau_hash=hash_password("pass"), lop_id=lop1.id)
    db.add(hs1)
    p = Problem(chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                nguoi_tao_id=gv1.id, meta={"dap_an_cuoi": "5"})
    db.add(p)
    db.flush()
    # Phiên tháng 6 (ngoài khoảng) + phiên tháng 7 (trong khoảng)
    for luc in (datetime(2026, 6, 1, tzinfo=timezone.utc).replace(tzinfo=None),
                datetime(2026, 7, 10, tzinfo=timezone.utc).replace(tzinfo=None)):
        db.add(SessionModel(hoc_sinh_id=hs1.id, problem_id=p.id,
                            trang_thai=TrangThaiSession.hoan_thanh, buoc_hien_tai=1,
                            cap_goi_y_hien_tai=0, diem=10, bat_dau_luc=luc, cap_nhat_luc=luc))
    db.commit()
    return gv1, gv2, admin, lop1, hs1


def _bat_xuat(db):
    dat_cau_hinh(db, "cho_phep_gv_xuat_bao_cao", True)


def test_mac_dinh_tat_gv_bi_chan(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    h = _h(_login(client, "gv1"))
    assert client.get(f"/api/progress/students/{hs1.id}/bao-cao", headers=h).status_code == 403
    assert client.get(f"/api/progress/lop/{lop1.id}/bao-cao", headers=h).status_code == 403
    assert client.get("/api/progress/bao-cao/cho-phep", headers=h).json()["cho_phep"] is False


def test_admin_luon_duoc_du_tat(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    h = _h(_login(client, "admin1"))
    assert client.get(f"/api/progress/students/{hs1.id}/bao-cao", headers=h).status_code == 200
    assert client.get("/api/progress/bao-cao/cho-phep", headers=h).json()["cho_phep"] is True


def test_bat_thi_gv_xuat_duoc(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    _bat_xuat(db)
    h = _h(_login(client, "gv1"))
    r = client.get(f"/api/progress/students/{hs1.id}/bao-cao", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["hoc_sinh"]["ho_ten"] == "HS Một"
    assert data["hoc_sinh"]["lop_ten"] == "12A1"
    assert data["tong_quan"]["so_phien"] == 2  # cả 2 phiên khi không lọc ngày
    assert set(["diem_manh", "diem_yeu", "theo_dang"]).issubset(data.keys())


def test_loc_theo_khoang_thoi_gian(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    _bat_xuat(db)
    h = _h(_login(client, "gv1"))
    # Chỉ tháng 7 → 1 phiên
    r = client.get(f"/api/progress/students/{hs1.id}/bao-cao",
                   params={"tu_ngay": "2026-07-01", "den_ngay": "2026-07-31"}, headers=h)
    assert r.status_code == 200
    assert r.json()["tong_quan"]["so_phien"] == 1


def test_gv_khac_khong_xuat_duoc(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    _bat_xuat(db)
    h = _h(_login(client, "gv2"))
    assert client.get(f"/api/progress/students/{hs1.id}/bao-cao", headers=h).status_code == 403
    assert client.get(f"/api/progress/lop/{lop1.id}/bao-cao", headers=h).status_code == 403


def test_bao_cao_ca_lop(db, client):
    gv1, gv2, admin, lop1, hs1 = _seed(db)
    _bat_xuat(db)
    h = _h(_login(client, "gv1"))
    r = client.get(f"/api/progress/lop/{lop1.id}/bao-cao", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["lop"]["ten"] == "12A1"
    assert len(data["danh_sach"]) == 1
    assert data["danh_sach"][0]["hoc_sinh"]["ho_ten"] == "HS Một"
