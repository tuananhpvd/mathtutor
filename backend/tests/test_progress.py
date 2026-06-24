"""Tests Phase 6 — tiến độ + làm tiếp bài dở."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


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

    # Bài TLN 2 bước đã duyệt
    p = Problem(
        chuyen_de="Khảo sát hàm số", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add_all([
        SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                     bieu_thuc_ket_qua="2", danh_sach_goi_y=["g1", "g2"]),
        SolutionStep(problem_id=p.id, thu_tu=2, pham_vi="ca_bai", mo_ta="b2",
                     bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]),
    ])
    db.commit()
    return p.id


def test_lam_do_roi_vao_lai_tiep_dung_cho(db, client):
    pid = _seed(db)
    token = _login(client, "hs1")
    h = {"Authorization": f"Bearer {token}"}

    # Tạo phiên + làm đúng bước 1 (kết quả "2") → sang bước 2, bỏ dở
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    r = client.post(f"/api/sessions/{sid}/message", headers=h,
                    json={"noi_dung": "em tính ra 2", "dap_an_nhap": "2"})
    assert r.json()["buoc_hien_tai"] == 2
    assert r.json()["da_xong"] is False

    # Lấy danh sách phiên dang dở → phải có phiên này ở bước 2
    dd = client.get("/api/sessions/dang-do", headers=h).json()
    assert len(dd) == 1
    assert dd[0]["session_id"] == sid
    assert dd[0]["buoc_hien_tai"] == 2

    # Làm tiếp đúng bước 2 ("5") → hoàn thành
    r2 = client.post(f"/api/sessions/{sid}/message", headers=h,
                     json={"noi_dung": "em ra 5", "dap_an_nhap": "5"})
    assert r2.json()["da_xong"] is True
    assert r2.json()["diem"] == 1.0

    # Không còn phiên dở
    assert client.get("/api/sessions/dang-do", headers=h).json() == []


def test_progress_me_sau_khi_hoan_thanh(db, client):
    pid = _seed(db)
    token = _login(client, "hs1")
    h = {"Authorization": f"Bearer {token}"}

    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h,
                json={"noi_dung": "2", "dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h,
                json={"noi_dung": "5", "dap_an_nhap": "5"})

    prog = client.get("/api/progress/me", headers=h).json()
    assert len(prog) == 1
    assert prog[0]["chuyen_de"] == "Khảo sát hàm số"
    assert prog[0]["so_bai_lam"] == 1
    assert prog[0]["so_bai_hoan_thanh"] == 1
    assert prog[0]["ty_le_dung_trung_binh"] == 1.0


def test_progress_students_gv_xem_lop_minh(db, client):
    pid = _seed(db)
    hs_token = _login(client, "hs1")
    hh = {"Authorization": f"Bearer {hs_token}"}
    sid = client.post("/api/sessions", headers=hh, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=hh, json={"noi_dung": "2", "dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=hh, json={"noi_dung": "5", "dap_an_nhap": "5"})

    gv_token = _login(client, "gv1")
    r = client.get("/api/progress/students", headers={"Authorization": f"Bearer {gv_token}"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["ho_ten"] == "HS A"
    assert data[0]["tien_do"][0]["so_bai_hoan_thanh"] == 1


def test_chi_tiet_phien_dung_lai_dung_cho(db, client):
    pid = _seed(db)
    token = _login(client, "hs1")
    h = {"Authorization": f"Bearer {token}"}

    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h,
                json={"noi_dung": "2", "dap_an_nhap": "2"})

    r = client.get(f"/api/sessions/{sid}", headers=h)
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == sid
    assert data["buoc_hien_tai"] == 2
    assert data["loai_cau"] == "TLN"
    # Có lịch sử lượt (mở đầu + HS + gia sư)
    assert len(data["turns"]) >= 3
    # Meta đã strip đáp án (TLN không lộ dap_an_cuoi)
    assert "dap_an_cuoi" not in data["meta"]


def test_chi_tiet_phien_khong_xem_phien_nguoi_khac(db, client):
    pid = _seed(db)
    # hs1 tạo phiên
    h1 = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h1, json={"problem_id": pid}).json()["session_id"]

    # tạo hs2 và đăng nhập
    from app.models.user import User, VaiTro
    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS B", dang_nhap="hs2",
               mat_khau_hash=hash_password("password"))
    db.add(hs2)
    db.commit()
    h2 = {"Authorization": f"Bearer {_login(client, 'hs2')}"}
    r = client.get(f"/api/sessions/{sid}", headers=h2)
    assert r.status_code == 404


def test_thoi_gian_hoan_thanh_duoc_ghi(db, client):
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"noi_dung": "2", "dap_an_nhap": "2"})
    r = client.post(f"/api/sessions/{sid}/message", headers=h,
                    json={"noi_dung": "5", "dap_an_nhap": "5"}).json()
    assert r["da_xong"] is True
    assert r["thoi_gian_giay"] is not None
    assert r["thoi_gian_giay"] >= 0

    # Tiến độ có tổng thời gian
    prog = client.get("/api/progress/me", headers=h).json()
    assert "tong_thoi_gian_giay" in prog[0]


def test_nhat_ky_hoan_thanh_gv(db, client):
    pid = _seed(db)
    hh = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=hh, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=hh, json={"noi_dung": "2", "dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=hh, json={"noi_dung": "5", "dap_an_nhap": "5"})

    gh = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.get("/api/monitor/sessions-hoan-thanh", headers=gh)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["ho_ten"] == "HS A"
    assert data[0]["thoi_gian_giay"] is not None

    # HS không xem được nhật ký
    assert client.get("/api/monitor/sessions-hoan-thanh", headers=hh).status_code == 403


def test_progress_me_phan_quyen_gv_bi_chan(db, client):
    _seed(db)
    gv_token = _login(client, "gv1")
    r = client.get("/api/progress/me", headers={"Authorization": f"Bearer {gv_token}"})
    assert r.status_code == 403


def test_dang_do_phan_quyen_gv_bi_chan(db, client):
    _seed(db)
    gv_token = _login(client, "gv1")
    r = client.get("/api/sessions/dang-do", headers={"Authorization": f"Bearer {gv_token}"})
    assert r.status_code == 403


def test_progress_service_tinh_lai_idempotent(db):
    """Gọi cap_nhat_tien_do nhiều lần không cộng dồn trùng."""
    from app.models.session import Session as SessionModel
    from app.models.session import TrangThaiSession
    from app.services.progress_service import cap_nhat_tien_do

    pid = _seed(db)
    hs = db.query(User).filter(User.dang_nhap == "hs1").first()

    s = SessionModel(hoc_sinh_id=hs.id, problem_id=pid,
                     trang_thai=TrangThaiSession.hoan_thanh, diem=1.0)
    db.add(s)
    db.commit()

    p1 = cap_nhat_tien_do(db, hs.id, "Khảo sát hàm số")
    p2 = cap_nhat_tien_do(db, hs.id, "Khảo sát hàm số")
    db.commit()
    assert p1.id == p2.id
    assert p2.so_bai_lam == 1
    assert p2.so_bai_hoan_thanh == 1
