"""Tests B1: mục tiêu học tập (HS tự đặt, GV đặt, đề xuất, tiến độ, bộ lọc tùy chọn)."""

from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.muc_tieu import MucTieu
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro
from app.services import muc_tieu_service


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _bai(db, chuyen_de, dang_id=None, nguoi_tao_id=None):
    p = Problem(
        chuyen_de=chuyen_de, dang_id=dang_id, loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=nguoi_tao_id,
        meta={"dap_an_cuoi": "5"},
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
    p1 = _bai(db, "Khảo sát hàm số", dang_id=dang.id, nguoi_tao_id=gv.id)
    p2 = _bai(db, "Khảo sát hàm số", dang_id=dang.id, nguoi_tao_id=gv.id)
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


# ---- Mục tiêu nhiều dòng (loai='nhieu') ----

def _bai_lc(db, dang_id, loai_cau, do_kho, cd="Khảo sát hàm số"):
    p = Problem(chuyen_de=cd, dang_id=dang_id, loai_cau=loai_cau, do_kho=do_kho,
                de_bai="x", loai_dap_an_nhap="gia_tri",
                trang_thai_duyet=TrangThaiDuyet.da_duyet, meta={"dap_an_cuoi": "5"})
    db.add(p)
    db.flush()
    return p


def _xong(db, hs_id, pid):
    """Phiên HOÀN THÀNH trực tiếp qua ORM (thời điểm cố định) — tất định, không qua luồng chấm."""
    db.add(SessionModel(hoc_sinh_id=hs_id, problem_id=pid,
                        trang_thai=TrangThaiSession.hoan_thanh, diem=1.0, thoi_gian_giay=60,
                        cap_nhat_luc=datetime(2024, 1, 1, tzinfo=timezone.utc)))
    db.commit()


def _mt_nhieu(db, hs, tieu_de, muc):
    """Tạo mục tiêu nhiều dòng rồi LÙI moc_bat_dau về quá khứ để đếm phiên hoàn thành (mốc
    2024 ở trên) — tách biến thời gian khỏi logic đang kiểm."""
    mid = muc_tieu_service.tao(db, hs, hs, "hs", "nhieu", tieu_de, muc=muc)["id"]
    mt = db.get(MucTieu, mid)
    mt.moc_bat_dau = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.commit()


def _mt(db, hs_id, tieu_de):
    return next(m for m in muc_tieu_service.danh_sach(db, hs_id) if m["tieu_de"] == tieu_de)


def test_nhieu_dong_loc_do_kho(db, client):
    s = _seed(db)
    hs = s["hs"]
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "kho").id)
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "kho").id)
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "tb").id)  # KHÔNG khớp mức Khó
    _mt_nhieu(db, hs, "MT", [{"do_kho": "kho", "chi_tieu_so": 2}])
    mt = _mt(db, hs, "MT")
    assert mt["muc"][0]["hien_tai"] == 2 and mt["muc"][0]["da_dat"] is True
    assert mt["da_dat"] is True


def test_nhieu_dong_loc_loai_cau(db, client):
    s = _seed(db)
    hs = s["hs"]
    _xong(db, hs, _bai_lc(db, s["dang"], "TNDS", "tb").id)
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "tb").id)  # KHÔNG khớp loại TNDS
    _mt_nhieu(db, hs, "MT", [{"loai_cau": "TNDS", "chi_tieu_so": 5}])
    assert _mt(db, hs, "MT")["muc"][0]["hien_tai"] == 1


def test_nhieu_dong_ket_hop_and(db, client):
    s = _seed(db)
    hs = s["hs"]
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "kho").id)   # khớp CẢ 2 tiêu chí
    _xong(db, hs, _bai_lc(db, s["dang"], "TNDS", "kho").id)  # sai loại
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "de").id)    # sai mức
    _mt_nhieu(db, hs, "MT", [{"loai_cau": "TLN", "do_kho": "kho", "chi_tieu_so": 5}])
    assert _mt(db, hs, "MT")["muc"][0]["hien_tai"] == 1


def test_nhieu_dong_tong_hop_dat_khi_moi_dong_dat(db, client):
    """Mục tiêu 2 dòng: dạng Cực trị (2 bài) + mức Khó (1 bài). ĐẠT khi CẢ 2 dòng đạt."""
    s = _seed(db)
    hs = s["hs"]
    _mt_nhieu(db, hs, "Kế hoạch", [
        {"dang_id": s["dang"], "chi_tieu_so": 2},
        {"do_kho": "kho", "chi_tieu_so": 1},
    ])
    # Hoàn thành 2 bài dạng Cực trị (mức tb) → dòng 1 đủ; dòng 2 (Khó) chưa
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "tb").id)
    _xong(db, hs, _bai_lc(db, s["dang"], "TLN", "tb").id)
    mt = _mt(db, hs, "Kế hoạch")
    assert mt["muc"][0]["da_dat"] is True and mt["muc"][1]["da_dat"] is False
    assert mt["da_dat"] is False
    # Hoàn thành 1 bài Khó (dạng khác) → dòng 2 đủ → cả mục tiêu ĐẠT
    _xong(db, hs, _bai_lc(db, None, "TLN", "kho", cd="Xác suất").id)
    mt = _mt(db, hs, "Kế hoạch")
    assert mt["muc"][1]["da_dat"] is True and mt["da_dat"] is True


def test_nhieu_dong_endpoint(db, client):
    """Endpoint HS nhận danh sách dòng con + trả về chi tiết từng dòng."""
    s = _seed(db)
    h = _h(client, "hs1")
    r = client.post("/api/muc-tieu/hs", headers=h, json={
        "loai": "nhieu", "tieu_de": "Kế hoạch tuần",
        "muc": [
            {"dang_id": s["dang"], "chi_tieu_so": 3},
            {"do_kho": "kho", "loai_cau": "TLN", "chi_tieu_so": 2},
        ],
    })
    assert r.status_code == 200, r.text
    mt = client.get("/api/muc-tieu/hs", headers=h).json()[0]
    assert mt["loai"] == "nhieu" and len(mt["muc"]) == 2
    assert mt["muc"][0]["dang_ten"] == "Cực trị" and mt["muc"][0]["chi_tieu_so"] == 3
    assert mt["muc"][1]["do_kho"] == "kho" and mt["muc"][1]["loai_cau"] == "TLN"
    assert mt["chi_tieu_so"] == 5  # tổng chỉ tiêu các dòng


def test_nhieu_dong_rong_bi_chan(db, client):
    _seed(db)
    h = _h(client, "hs1")
    r = client.post("/api/muc-tieu/hs", headers=h,
                    json={"loai": "nhieu", "tieu_de": "x", "muc": []})
    assert r.status_code == 400


def test_xoa_muc_tieu_va_phan_quyen(db, client):
    _seed(db)
    h = _h(client, "hs1")
    mt_id = client.post("/api/muc-tieu/hs", headers=h,
                        json={"loai": "tuan", "chi_tieu_so": 1}).json()["id"]
    # GV của lớp xóa được
    h_gv = _h(client, "gv1")
    assert client.delete(f"/api/muc-tieu/{mt_id}", headers=h_gv).status_code == 200
    assert client.get("/api/muc-tieu/hs", headers=h).json() == []
