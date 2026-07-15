"""Tests A4: khép vòng cờ — báo HS khi gặp khó + GV xử lý kèm lời nhắn."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


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
                     bieu_thuc_ket_qua="2", danh_sach_goi_y=["g1", "g2", "g3", "g4"]),
        SolutionStep(problem_id=p.id, thu_tu=2, pham_vi="ca_bai", mo_ta="b2",
                     bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2", "g3", "g4"]),
    ])
    db.commit()
    return p.id


def test_bao_hs_khi_gap_kho_va_gv_khep_vong(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    # HS xin gợi ý 3 lần (ngưỡng mặc định) → tự gắn cờ + báo HS
    for _ in range(3):
        client.post(f"/api/sessions/{sid}/message", headers=h_hs,
                    json={"noi_dung": "Em chưa hiểu", "yeu_cau_goi_y": True})

    # HS nhận thông báo 'đang gặp khó' (trung tính, minh bạch, nêu phần)
    tb = client.get("/api/thong-bao", headers=h_hs).json()
    co_tb = [t for t in tb if t["loai"] == "co"]
    assert len(co_tb) == 1
    assert "gặp khó" in co_tb[0]["noi_dung"]
    assert "Khảo sát hàm số" in co_tb[0]["noi_dung"]

    # GV thấy cờ kèm tên HS + bài
    h_gv = _h(client, "gv1")
    flags = client.get("/api/monitor/flags", headers=h_gv).json()
    co = next((f for f in flags if f["loai_co"] == "khong_hieu_nhieu"), None)
    assert co is not None
    assert co["hoc_sinh_ten"] == "HS A"
    assert co["chuyen_de"] == "Khảo sát hàm số"

    # GV xử lý kèm lời nhắn → HS nhận thêm thông báo
    r = client.patch(f"/api/monitor/flags/{co['id']}", headers=h_gv,
                     params={"trang_thai": "da_xu_ly", "loi_nhan": "Em xem lại ví dụ mẫu nhé!"})
    assert r.status_code == 200, r.text

    tb2 = client.get("/api/thong-bao", headers=h_hs).json()
    loi_nhan = [t for t in tb2 if t["tieu_de"] == "Lời nhắn từ thầy/cô"]
    assert len(loi_nhan) == 1
    assert "ví dụ mẫu" in loi_nhan[0]["noi_dung"]
    assert loi_nhan[0]["nguoi_gui_ten"] == "Cô Lan"


def test_xu_ly_co_khong_loi_nhan_khong_tao_thong_bao(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    for _ in range(3):
        client.post(f"/api/sessions/{sid}/message", headers=h_hs,
                    json={"noi_dung": "Em chưa hiểu", "yeu_cau_goi_y": True})

    h_gv = _h(client, "gv1")
    co = next(f for f in client.get("/api/monitor/flags", headers=h_gv).json()
              if f["loai_co"] == "khong_hieu_nhieu")
    truoc = len(client.get("/api/thong-bao", headers=h_hs).json())
    # Bỏ qua, không lời nhắn → không phát sinh thông báo mới
    client.patch(f"/api/monitor/flags/{co['id']}", headers=h_gv,
                 params={"trang_thai": "bo_qua"})
    sau = len(client.get("/api/thong-bao", headers=h_hs).json())
    assert sau == truoc


def _seed_de_2_goi_y(db):
    """Thêm bài Dễ 1 bước, CHỈ 2 gợi ý — cạn sạch chỉ cần 1 lần, dưới ngưỡng cờ cũ (3)."""
    gv = db.query(User).filter(User.dang_nhap == "gv1").first()
    p = Problem(
        chuyen_de="Đạo hàm", loai_cau="TLN", do_kho="de",
        de_bai="Tính.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=gv.id,
        meta={"dap_an_cuoi": "3"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="3", danh_sach_goi_y=["g1", "g2"]))
    db.commit()
    return p.id


def test_het_sach_goi_y_gan_co_du_duoi_nguong(db, client):
    """Tầng 3: HS cạn SẠCH thang gợi ý (bài Dễ 2 gợi ý) → gắn cờ dù số lần xin gợi ý (1)
    còn dưới ngưỡng 3 — lấp lỗ hổng bài dễ trước đây tàng hình với GV."""
    from app.models.session import Session as SessionModel

    _seed(db)
    pid = _seed_de_2_goi_y(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    # Chỉ xin gợi ý 1 lần → cap_goi_y chạm trần (2 gợi ý) → hết sạch thang
    client.post(f"/api/sessions/{sid}/message", headers=h_hs,
                json={"noi_dung": "Em chưa hiểu", "yeu_cau_goi_y": True})

    s = db.get(SessionModel, sid)
    db.refresh(s)
    assert s.so_lan_het_goi_y == 1
    assert s.so_lan_khong_hieu == 1  # dưới ngưỡng cờ cũ (3)

    h_gv = _h(client, "gv1")
    co = next((f for f in client.get("/api/monitor/flags", headers=h_gv).json()
               if f["loai_co"] == "khong_hieu_nhieu"), None)
    assert co is not None  # vẫn gắn cờ nhờ điều kiện hết sạch gợi ý


def test_dem_het_goi_y_khong_trung(db, client):
    """so_lan_het_goi_y đếm theo CẠNH LÊN: xin gợi ý thêm sau khi đã cạn không tăng nữa."""
    from app.models.session import Session as SessionModel

    _seed(db)
    pid = _seed_de_2_goi_y(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    for _ in range(3):
        client.post(f"/api/sessions/{sid}/message", headers=h_hs,
                    json={"noi_dung": "?", "yeu_cau_goi_y": True})

    s = db.get(SessionModel, sid)
    db.refresh(s)
    assert s.so_lan_het_goi_y == 1  # cạn 1 lần, các lần sau không đếm trùng


def test_danh_dau_xem_ly_thuyet(db, client):
    """POST /sessions/{id}/xem-ly-thuyet tăng bộ đếm; phiên người khác → 404."""
    from app.models.session import Session as SessionModel

    _seed(db)
    pid = _seed_de_2_goi_y(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    r = client.post(f"/api/sessions/{sid}/xem-ly-thuyet", headers=h_hs)
    assert r.status_code == 200 and r.json()["so_lan_xem_ly_thuyet"] == 1
    client.post(f"/api/sessions/{sid}/xem-ly-thuyet", headers=h_hs)
    s = db.get(SessionModel, sid)
    db.refresh(s)
    assert s.so_lan_xem_ly_thuyet == 2

    # GV không có route này (chỉ HS) + không phải phiên của mình
    h_gv = _h(client, "gv1")
    assert client.post(f"/api/sessions/{sid}/xem-ly-thuyet", headers=h_gv).status_code == 403
