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

    # Bài TLN 2 bước đã duyệt, thuộc GV chủ nhiệm lớp HS (điều kiện HS tự luyện)
    p = Problem(
        chuyen_de="Khảo sát hàm số", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gv.id,
        meta={"dap_an_cuoi": "5"},
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


def test_thong_ke_chi_tiet(db, client):
    pid = _seed(db)  # TLN, chuyên đề "Khảo sát hàm số", mức tb, không gán dạng
    token = _login(client, "hs1")
    h = {"Authorization": f"Bearer {token}"}

    # Chưa làm → 1 bài chưa làm
    r = client.get("/api/progress/me/thong-ke", headers=h).json()
    assert r["tong_quan"] == {"tong": 1, "hoan_thanh": 0, "dang_lam": 0, "chua_lam": 1}

    # Tạo phiên → đang làm dở
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    r = client.get("/api/progress/me/thong-ke", headers=h).json()
    assert r["tong_quan"]["dang_lam"] == 1 and r["tong_quan"]["chua_lam"] == 0

    # Hoàn thành (b1=2, b2=5)
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    r = client.get("/api/progress/me/thong-ke", headers=h).json()
    assert r["tong_quan"]["hoan_thanh"] == 1 and r["tong_quan"]["chua_lam"] == 0
    tb = next(x for x in r["theo_do_kho"] if x["do_kho"] == "tb")
    assert tb["tong"] == 1 and tb["hoan_thanh"] == 1
    assert r["thoi_gian"]["nhanh_nhat"]["tb"] is not None
    assert r["theo_dang"][0]["chuyen_de"] == "Khảo sát hàm số"
    assert r["theo_dang"][0]["dang"][0]["hoan_thanh"] == 1

    # Mất nhiều thời gian (Pha per-HS, không cộng dồn với HS khác — bài chưa gán dạng nên
    # ten = tên chuyên đề).
    assert r["dang_mat_thoi_gian"] == [
        {"ten": "Khảo sát hàm số", "thoi_gian_giay": r["thoi_gian"]["tong_thoi_gian_giay"]}
    ]
    assert r["loai_mat_thoi_gian"] == [
        {"loai": "TLN", "thoi_gian_giay": r["thoi_gian"]["tong_thoi_gian_giay"]}
    ]


def test_phan_tich_nang_luc_hs_va_gv(db, client):
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}

    # Chưa có dữ liệu → đề xuất bắt đầu luyện
    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert r["tong_hoan_thanh"] == 0
    assert r["du_lieu_du"] is False
    assert len(r["de_xuat_hs"]) >= 1

    # Hoàn thành 1 bài → có dữ liệu nhóm
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert r["tong_hoan_thanh"] == 1
    assert any(g["so_hoan_thanh"] == 1 for g in r["theo_chuyen_de"])
    assert any(g.get("loai") == "TLN" for g in r["theo_loai_cau"])

    # GV xem phân tích HS lớp mình
    gh = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    hid = client.get("/api/progress/students", headers=gh).json()[0]["hoc_sinh_id"]
    rg = client.get(f"/api/progress/students/{hid}/phan-tich", headers=gh)
    assert rg.status_code == 200
    assert "de_xuat_gv" in rg.json()


class _LLMPhanTich:
    """LLM giả: luôn trả bản phân tích AI."""
    def phan_tich(self, ho_so):
        return {"cho_hoc_sinh": "Em tiến bộ tốt.", "cho_giao_vien": "HS ổn, theo dõi tiếp."}


def test_phan_tich_ai_cache_va_cap_nhat(db, client, monkeypatch):
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    # Hoàn thành 1 bài để có dữ liệu
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    # Chưa cập nhật → chưa có bản AI, nhưng nên cập nhật (có dữ liệu)
    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert r["ai"] is None and r["nen_cap_nhat"] is True

    # Cập nhật với LLM giả → có bản AI lưu cache
    import app.api.progress as prog
    monkeypatch.setattr(prog, "get_llm_client", lambda cfg=None: _LLMPhanTich())
    r2 = client.post("/api/progress/me/phan-tich/cap-nhat", headers=h).json()
    assert r2["ai"]["cho_hoc_sinh"] == "Em tiến bộ tốt."

    # GET lại (không cần LLM) vẫn còn bản cache
    r3 = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert r3["ai"]["cho_giao_vien"] == "HS ổn, theo dõi tiếp."
    assert r3["nen_cap_nhat"] is False


class _LLMTrong:
    """LLM giả không khả dụng (vd hết quota) → phan_tich luôn trả None."""
    def phan_tich(self, ho_so):
        return None


def test_phan_tich_du_phong_theo_luat(db, client):
    """LLM không khả dụng → vẫn ghi bản dự phòng theo luật, đánh dấu nguồn 'luat'
    và tiếp tục nên cập nhật (để lần sau nâng cấp lên AI)."""
    from app.services.phan_tich_service import cap_nhat_phan_tich, lay_phan_tich
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    hid = client.get("/api/progress/students",
                     headers={"Authorization": f"Bearer {_login(client, 'gv1')}"}).json()[0][
        "hoc_sinh_id"]

    r = cap_nhat_phan_tich(db, hid, _LLMTrong())
    assert r["ai_kha_dung"] is False
    assert r["ai"] is not None and r["ai"]["nguon"] == "luat"
    assert r["ai"]["cho_hoc_sinh"]  # có nội dung theo luật
    # Bản theo luật luôn nên nâng cấp lên AI
    assert lay_phan_tich(db, hid)["nen_cap_nhat"] is True

    # Khi AI khả dụng → ghi đè bản 'ai'
    r2 = cap_nhat_phan_tich(db, hid, _LLMPhanTich())
    assert r2["ai"]["nguon"] == "ai"
    assert lay_phan_tich(db, hid)["nen_cap_nhat"] is False


def test_tong_hop_lop_gv(db, client):
    _seed(db)
    gh = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.get("/api/progress/lop/tong-hop", headers=gh)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["so_hoc_sinh"] >= 1
    for k in ("dang_yeu_chung", "hoc_sinh_can_chu_y", "so_hoc_sinh_co_du_lieu"):
        assert k in d


def test_phan_tich_co_xu_huong_va_dang_id(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert "xu_huong" in r
    # mỗi nhóm dạng có khóa dang_id (có thể None nếu bài chưa gán dạng)
    assert all("dang_id" in g for g in r["theo_dang"])


def test_quet_tai_sinh_va_endpoint_admin(db, client):
    """Quét nền tái sinh phân tích AI cho HS đến hạn (admin gọi quét ngay)."""
    pid = _seed(db)
    # Tạo tài khoản admin
    db.add(User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin1",
                mat_khau_hash=hash_password("password")))
    db.commit()

    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    # Hàm quét trực tiếp với LLM giả → cập nhật được 1 HS
    from app.services.phan_tich_service import quet_tai_sinh
    ket = quet_tai_sinh(db, _LLMPhanTich())
    assert ket["da_quet"] >= 1 and ket["da_cap_nhat"] == 1 and ket["loi"] == 0

    # Đã có bản cache → GET không cần LLM vẫn thấy nhận định
    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert r["ai"] is not None and r["nen_cap_nhat"] is False

    # Endpoint admin "quét ngay" — không có HS nào đến hạn nữa (vừa cập nhật)
    ah = {"Authorization": f"Bearer {_login(client, 'admin1')}"}
    ra = client.post("/api/admin/phan-tich/quet", headers=ah)
    assert ra.status_code == 200, ra.text
    assert ra.json()["da_cap_nhat"] == 0

    # HS thường không gọi được endpoint admin
    assert client.post("/api/admin/phan-tich/quet", headers=h).status_code == 403


def test_gv_xem_thong_ke_hoc_sinh(db, client):
    _seed(db)
    gh = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    students = client.get("/api/progress/students", headers=gh).json()
    hid = students[0]["hoc_sinh_id"]
    # GV xem được HS lớp mình
    r = client.get(f"/api/progress/students/{hid}/thong-ke", headers=gh)
    assert r.status_code == 200
    assert "tong_quan" in r.json() and "theo_dang" in r.json()
    # HS không có quyền gọi endpoint của GV
    hh = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    assert client.get(f"/api/progress/students/{hid}/thong-ke", headers=hh).status_code == 403


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


def test_xu_huong_dung_diem_qua_trinh(db):
    """Xu hướng phải đo bằng diem_qua_trinh (ít sai/ít gợi ý hơn = tiến bộ) — vì diem của
    TLN/TN4PA hoàn thành luôn = 1.0, đo bằng diem thì xu hướng 'mù'. Phiên cũ chưa có
    diem_qua_trinh → fallback diem."""
    from datetime import datetime, timedelta
    from types import SimpleNamespace

    from app.models.session import TrangThaiSession
    from app.services.phan_tich_service import _xu_huong

    t0 = datetime(2026, 7, 1)

    def phien(i, diem, dqt):
        return SimpleNamespace(trang_thai=TrangThaiSession.hoan_thanh, diem=diem,
                               diem_qua_trinh=dqt, cap_nhat_luc=t0 + timedelta(days=i))

    # diem luôn 1.0 nhưng quá trình tốt dần (0.5 → 0.9): PHẢI ra 'tien_bo' (đo diem sẽ ra on_dinh)
    assert _xu_huong([phien(0, 1.0, 0.5), phien(1, 1.0, 0.5),
                      phien(2, 1.0, 0.9), phien(3, 1.0, 0.9)]) == "tien_bo"
    # quá trình kém dần → 'giam'
    assert _xu_huong([phien(0, 1.0, 0.9), phien(1, 1.0, 0.9),
                      phien(2, 1.0, 0.5), phien(3, 1.0, 0.5)]) == "giam"
    # dữ liệu cũ không có diem_qua_trinh → fallback diem (TNDS bậc thang vẫn đo được)
    assert _xu_huong([phien(0, 0.25, None), phien(1, 0.25, None),
                      phien(2, 1.0, None), phien(3, 1.0, None)]) == "tien_bo"
    # < 4 bài → chưa đủ
    assert _xu_huong([phien(0, 1.0, 0.5)]) == "chua_du"


def test_theo_dang_co_xu_huong_rieng(db, client):
    """Mỗi nhóm dạng trong hồ sơ năng lực có xu hướng riêng (1 bài → 'chua_du')."""
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    r = client.get("/api/progress/me/phan-tich", headers=h).json()
    assert all("xu_huong" in g for g in r["theo_dang"])
    assert r["theo_dang"][0]["xu_huong"] == "chua_du"  # mới 1 bài trong dạng


def test_so_sanh_7_ngay(db, client):
    """Thống kê chi tiết trả so sánh 7 ngày qua vs 7 ngày trước (bài vừa xong → kỳ này)."""
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    r = client.get("/api/progress/me/thong-ke", headers=h).json()
    ss = r["so_sanh_7_ngay"]
    assert ss["ky_nay"]["so_bai"] == 1
    assert ss["ky_nay"]["thoi_gian_tb_giay"] is not None
    assert ss["ky_truoc"] == {"so_bai": 0, "thoi_gian_tb_giay": None, "goi_y_tb": None}


def test_chan_doan_vat_lon_theo_dang(db):
    """ho_so_nang_luc thêm cột chẩn đoán theo dạng/loại: số lần cạn gợi ý / xem lý thuyết /
    nhờ thầy cô — để GV thấy hành trình vật lộn. so_lan_het_goi_y của các phiên ĐÃ HOÀN
    THÀNH giờ CŨNG góp phần vào điểm thành thạo (xem test_het_goi_y_giam_diem_thanh_thao),
    khác với trước đây khi cột này chỉ để hiển thị, hoàn toàn tách biệt khỏi công thức."""
    from app.models.session import Session as SessionModel
    from app.models.session import TrangThaiSession
    from app.models.yeu_cau_tro_giup import YeuCauTroGiup
    from app.services.phan_tich_service import ho_so_nang_luc

    pid = _seed(db)  # bài "Khảo sát hàm số", TLN
    hs = db.query(User).filter(User.dang_nhap == "hs1").first()

    s = SessionModel(hoc_sinh_id=hs.id, problem_id=pid,
                     trang_thai=TrangThaiSession.hoan_thanh, diem=1.0,
                     so_lan_het_goi_y=2, so_lan_xem_ly_thuyet=3)
    db.add(s)
    db.flush()
    db.add(YeuCauTroGiup(hoc_sinh_id=hs.id, session_id=s.id, problem_id=pid))
    db.commit()

    ho_so = ho_so_nang_luc(db, hs.id)
    dang = ho_so["theo_dang"][0]
    assert dang["so_lan_het_goi_y"] == 2
    assert dang["so_lan_xem_ly_thuyet"] == 3
    assert dang["so_lan_nho_thay_co"] == 1
    assert "diem_thanh_thao" in dang
    # 1 bài, cạn gợi ý 2 lần → phạt kịch trần (min 0.15), mastery < 100
    assert dang["diem_thanh_thao"] < 100
    assert dang["nhan_hien_thi"]  # nhãn hiển thị chuẩn hoá luôn có mặt
    assert dang["ly_do"]  # câu giải thích ngắn luôn có mặt


def test_het_goi_y_giam_diem_thanh_thao():
    """so_lan_het_goi_y (KHÔNG reset trong phiên) giờ ảnh hưởng thật đến điểm thành thạo —
    khác với cap_goi_y_hien_tai (reset về 0 mỗi khi trả lời đúng) trước đây gần như vô dụng
    để phát hiện học sinh đã vật lộn cả phiên rồi mới đúng ở bước cuối."""
    from app.services.phan_tich_service import _diem_thanh_thao

    khong_vat_lon = _diem_thanh_thao(ty_le_hoan_thanh=1.0, diem_chat_luong_tb=1.0, het_goi_y_tb=0.0)
    vat_lon = _diem_thanh_thao(ty_le_hoan_thanh=1.0, diem_chat_luong_tb=1.0, het_goi_y_tb=2.0)
    assert khong_vat_lon == 100
    assert vat_lon < khong_vat_lon


def test_me_hieu_qua(db, client):
    """HS tự xem chuỗi 8 tuần của mình; GV không gọi được route /me (dành riêng HS)."""
    pid = _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'hs1')}"}
    sid = client.post("/api/sessions", headers=h, json={"problem_id": pid}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "2"})
    client.post(f"/api/sessions/{sid}/message", headers=h, json={"dap_an_nhap": "5"})

    r = client.get("/api/progress/me/hieu-qua", headers=h)
    assert r.status_code == 200
    d = r.json()
    # Tuần tương đối theo mốc riêng: vừa làm bài đầu tiên hôm nay → chỉ có Tuần 1
    assert len(d["theo_tuan"]) == 1
    assert d["theo_tuan"][0]["tuan_so"] == 1
    assert d["theo_tuan"][0]["so_bai"] == 1

    gh = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    assert client.get("/api/progress/me/hieu-qua", headers=gh).status_code == 403
