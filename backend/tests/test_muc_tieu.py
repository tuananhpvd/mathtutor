"""Tests B1: mục tiêu học tập (HS tự đặt, GV đặt, đề xuất, tiến độ)."""

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _bai(db, chuyen_de, dang_id=None):
    p = Problem(
        chuyen_de=chuyen_de, dang_id=dang_id, loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]))
    return p


def _seed(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    db.add(gv)
    db.flush()
    lop.gv_id = gv.id
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    cd = ChuyenDe(ten="Khảo sát hàm số", thu_tu=1)
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Cực trị", thu_tu=1)
    db.add(dang)
    db.flush()
    p1 = _bai(db, "Khảo sát hàm số", dang_id=dang.id)
    p2 = _bai(db, "Khảo sát hàm số", dang_id=dang.id)
    db.commit()
    return {"hs": hs.id, "dang": dang.id, "p1": p1.id, "p2": p2.id}


def test_hs_tu_dat_va_tien_do_chu_de(db, client):
    s = _seed(db)
    h = _h(client, "hs1")
    r = client.post("/api/muc-tieu/hs", headers=h, json={
        "loai": "chu_de", "chi_tieu_so": 2, "dang_id": s["dang"],
    })
    assert r.status_code == 200, r.text

    ds = client.get("/api/muc-tieu/hs", headers=h).json()
    assert len(ds) == 1
    assert ds[0]["chi_tieu_so"] == 2 and ds[0]["hien_tai"] == 0 and ds[0]["da_dat"] is False
    assert ds[0]["dang_ten"] == "Cực trị"

    # Hoàn thành 1 bài thuộc dạng → tiến độ 1/2
    sid = client.post("/api/sessions", headers=h, json={"problem_id": s["p1"]}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})
    ds = client.get("/api/muc-tieu/hs", headers=h).json()
    assert ds[0]["hien_tai"] == 1 and ds[0]["da_dat"] is False

    # Hoàn thành bài thứ 2 → đạt
    sid2 = client.post("/api/sessions", headers=h, json={"problem_id": s["p2"]}).json()["session_id"]
    client.post(f"/api/sessions/{sid2}/message", headers=h, json={"dap_an_nhap": "5"})
    ds = client.get("/api/muc-tieu/hs", headers=h).json()
    assert ds[0]["hien_tai"] == 2 and ds[0]["da_dat"] is True


def test_tien_do_tuan(db, client):
    s = _seed(db)
    h = _h(client, "hs1")
    client.post("/api/muc-tieu/hs", headers=h, json={"loai": "tuan", "chi_tieu_so": 1})
    sid = client.post("/api/sessions", headers=h, json={"problem_id": s["p1"]}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})
    ds = client.get("/api/muc-tieu/hs", headers=h).json()
    assert ds[0]["loai"] == "tuan" and ds[0]["hien_tai"] == 1 and ds[0]["da_dat"] is True


def test_gv_dat_muc_tieu_bao_hs(db, client):
    s = _seed(db)
    h_gv = _h(client, "gv1")
    r = client.post(f"/api/muc-tieu/gv/{s['hs']}", headers=h_gv, json={
        "loai": "chu_de", "chi_tieu_so": 3, "dang_id": s["dang"],
        "tieu_de": "Luyện cực trị",
    })
    assert r.status_code == 200, r.text

    h_hs = _h(client, "hs1")
    # HS thấy mục tiêu + được thông báo
    ds = client.get("/api/muc-tieu/hs", headers=h_hs).json()
    assert len(ds) == 1 and ds[0]["nguon"] == "gv" and ds[0]["nguoi_tao_ten"] == "Cô Lan"
    assert client.get("/api/thong-bao/chua-doc", headers=h_hs).json()["so_luong"] == 1


def test_chu_de_thieu_dang_bi_chan(db, client):
    _seed(db)
    h = _h(client, "hs1")
    r = client.post("/api/muc-tieu/hs", headers=h, json={"loai": "chu_de", "chi_tieu_so": 2})
    assert r.status_code == 400


def test_de_xuat_co_muc_tieu_tuan(db, client):
    _seed(db)
    h = _h(client, "hs1")
    dx = client.get("/api/muc-tieu/hs/de-xuat", headers=h).json()
    assert any(g["loai"] == "tuan" for g in dx)
    # Tạo từ 1 gợi ý
    g = dx[0]
    r = client.post("/api/muc-tieu/hs", headers=h, json={
        "loai": g["loai"], "tieu_de": g["tieu_de"], "chi_tieu_so": g["chi_tieu_so"],
        "dang_id": g["dang_id"],
    })
    assert r.status_code == 200, r.text


def test_xoa_muc_tieu_va_phan_quyen(db, client):
    _seed(db)
    h = _h(client, "hs1")
    mt_id = client.post("/api/muc-tieu/hs", headers=h,
                        json={"loai": "tuan", "chi_tieu_so": 1}).json()["id"]
    # GV của lớp xóa được
    h_gv = _h(client, "gv1")
    assert client.delete(f"/api/muc-tieu/{mt_id}", headers=h_gv).status_code == 200
    assert client.get("/api/muc-tieu/hs", headers=h).json() == []
