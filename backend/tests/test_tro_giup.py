"""Tests A2: 'Nhờ thầy/cô' (HS→GV), GV trả lời ngay trong bài."""

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
    """gv1 phụ trách lớp có hs1; gv2 lớp khác. Trả problem_id."""
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="Thầy Nam", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv, gv2])
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
                     bieu_thuc_ket_qua="2", danh_sach_goi_y=["g1", "g2"]),
        SolutionStep(problem_id=p.id, thu_tu=2, pham_vi="ca_bai", mo_ta="b2",
                     bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]),
    ])
    db.commit()
    return p.id


def test_luong_nho_thay_co_va_tra_loi(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    # HS nhờ thầy/cô
    r = client.post("/api/tro-giup", headers=h_hs,
                    json={"session_id": sid, "noi_dung": "Em chưa biết bắt đầu từ đâu"})
    assert r.status_code == 200, r.text

    # GV được thông báo (chuông) + thấy trong hàng đợi
    h_gv = _h(client, "gv1")
    assert client.get("/api/thong-bao/chua-doc", headers=h_gv).json()["so_luong"] == 1
    ds = client.get("/api/tro-giup/gv", headers=h_gv).json()
    assert len(ds) == 1
    yc = ds[0]
    assert yc["hoc_sinh_ten"] == "HS A"
    assert yc["trang_thai"] == "cho_xu_ly"
    assert yc["noi_dung"] == "Em chưa biết bắt đầu từ đâu"

    # GV trả lời
    r = client.post(f"/api/tro-giup/{yc['id']}/tra-loi", headers=h_gv,
                    json={"noi_dung": "Em hãy tính đạo hàm trước nhé."})
    assert r.status_code == 200, r.text

    # Câu trả lời hiện trong khung hội thoại của bài (turn 'giao_vien')
    ct = client.get(f"/api/sessions/{sid}", headers=h_hs).json()
    gv_turns = [t for t in ct["turns"] if t["vai_tro"] == "giao_vien"]
    assert len(gv_turns) == 1
    assert "đạo hàm" in gv_turns[0]["noi_dung"]

    # HS được thông báo đã trả lời
    tb = client.get("/api/thong-bao", headers=h_hs).json()
    assert any(t["loai"] == "tra_loi" for t in tb)

    # Yêu cầu chuyển trạng thái đã trả lời
    ds2 = client.get("/api/tro-giup/gv", headers=h_gv).json()
    assert ds2[0]["trang_thai"] == "da_tra_loi"


def test_gv_khac_lop_khong_tra_loi_duoc(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    yc_id = client.post("/api/tro-giup", headers=h_hs, json={"session_id": sid}).json()["id"]

    # gv2 không phụ trách lớp của hs1 → không thấy & không trả lời được
    h_gv2 = _h(client, "gv2")
    assert client.get("/api/tro-giup/gv", headers=h_gv2).json() == []
    r = client.post(f"/api/tro-giup/{yc_id}/tra-loi", headers=h_gv2, json={"noi_dung": "x"})
    assert r.status_code == 400


def test_xoa_yeu_cau(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    yc_id = client.post("/api/tro-giup", headers=h_hs, json={"session_id": sid}).json()["id"]

    h_gv = _h(client, "gv1")
    # GV thấy 1 yêu cầu
    assert len(client.get("/api/tro-giup/gv", headers=h_gv).json()) == 1
    # Xóa → 204/200
    r = client.delete(f"/api/tro-giup/{yc_id}", headers=h_gv)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    # Không còn trong danh sách
    assert client.get("/api/tro-giup/gv", headers=h_gv).json() == []


def test_gv_khac_lop_khong_xoa_duoc(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    yc_id = client.post("/api/tro-giup", headers=h_hs, json={"session_id": sid}).json()["id"]

    h_gv2 = _h(client, "gv2")
    r = client.delete(f"/api/tro-giup/{yc_id}", headers=h_gv2)
    assert r.status_code == 400


def test_response_co_de_bai(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    client.post("/api/tro-giup", headers=h_hs, json={"session_id": sid})

    h_gv = _h(client, "gv1")
    ds = client.get("/api/tro-giup/gv", headers=h_gv).json()
    assert ds[0]["de_bai"] == "Tìm x."


def test_xem_chi_tiet_hoi_thoai_cat_dung_moc(db, client):
    """GV 'Xem chi tiết': thấy đúng hội thoại từ đầu ĐẾN LÚC nhờ — không thấy các lượt HS
    làm SAU khi nhờ (đang chờ GV), và câu trả lời của GV được nối vào CUỐI."""
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    # HS thử sai 1 lần trước khi nhờ — phải xuất hiện trong chi tiết (trước mốc nhờ)
    client.post(f"/api/sessions/{sid}/message", headers=h_hs,
               json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"})
    yc_id = client.post("/api/tro-giup", headers=h_hs,
                        json={"session_id": sid, "noi_dung": "Em chưa hiểu bước này"}).json()["id"]
    # HS tiếp tục hỏi gia sư AI trong lúc CHỜ GV trả lời — KHÔNG được xuất hiện trong chi tiết
    client.post(f"/api/sessions/{sid}/message", headers=h_hs, json={"noi_dung": "gợi ý thêm với"})

    h_gv = _h(client, "gv1")
    ct = client.get(f"/api/tro-giup/{yc_id}/chi-tiet", headers=h_gv)
    assert ct.status_code == 200, ct.text
    d = ct.json()
    assert d["hoc_sinh_ten"] == "HS A"
    assert d["de_bai"] == "Tìm x."

    noi_dung_ds = [t["noi_dung"] for t in d["turns"]]
    assert any("em nghĩ x=3" in n for n in noi_dung_ds)          # trước mốc nhờ — có
    assert any("Nhờ thầy/cô" in n for n in noi_dung_ds)          # chính lượt nhờ — có
    assert not any("gợi ý thêm với" in n for n in noi_dung_ds)   # SAU mốc nhờ — không có
    # Chưa trả lời → chưa có turn giao_vien ở cuối
    assert d["turns"][-1]["vai_tro"] != "giao_vien"

    # GV trả lời → gọi lại chi-tiết phải thấy câu trả lời nối CUỐI
    client.post(f"/api/tro-giup/{yc_id}/tra-loi", headers=h_gv,
               json={"noi_dung": "Em xem lại công thức nhé."})
    ct2 = client.get(f"/api/tro-giup/{yc_id}/chi-tiet", headers=h_gv).json()
    assert ct2["turns"][-1] == {"vai_tro": "giao_vien", "noi_dung": "Em xem lại công thức nhé."}
    # Vẫn KHÔNG lẫn lượt HS hỏi thêm lúc chờ (đứng ngay trước turn giao_vien theo id)
    assert not any("gợi ý thêm với" in t["noi_dung"] for t in ct2["turns"])


def test_tra_loi_them_giu_du_lich_su(db, client):
    """GV bấm 'Trả lời thêm' nhiều lần: chi tiết phải giữ ĐỦ các lượt trả lời trước đó, không
    chỉ câu cuối. `yc.tra_loi` bị GHI ĐÈ mỗi lần trả lời nên không dùng làm nguồn lịch sử —
    phải đọc từ các Turn giao_vien thật."""
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    yc_id = client.post("/api/tro-giup", headers=h_hs,
                        json={"session_id": sid, "noi_dung": "Em bí bước này"}).json()["id"]

    h_gv = _h(client, "gv1")
    client.post(f"/api/tro-giup/{yc_id}/tra-loi", headers=h_gv, json={"noi_dung": "Gợi ý thứ nhất"})
    client.post(f"/api/tro-giup/{yc_id}/tra-loi", headers=h_gv, json={"noi_dung": "Gợi ý thứ hai"})

    d = client.get(f"/api/tro-giup/{yc_id}/chi-tiet", headers=h_gv).json()
    tl = [t["noi_dung"] for t in d["turns"] if t["vai_tro"] == "giao_vien"]
    assert tl == ["Gợi ý thứ nhất", "Gợi ý thứ hai"], tl


def test_tra_loi_khong_lan_sang_yeu_cau_sau(db, client):
    """Cùng một phiên HS nhờ 2 lần: lượt trả lời của yêu cầu SAU không được gộp nhầm vào
    yêu cầu TRƯỚC (chặn trên theo turn_id của yêu cầu kế tiếp)."""
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    h_gv = _h(client, "gv1")

    yc1 = client.post("/api/tro-giup", headers=h_hs,
                      json={"session_id": sid, "noi_dung": "Nhờ lần 1"}).json()["id"]
    client.post(f"/api/tro-giup/{yc1}/tra-loi", headers=h_gv, json={"noi_dung": "Đáp lần 1"})

    yc2 = client.post("/api/tro-giup", headers=h_hs,
                      json={"session_id": sid, "noi_dung": "Nhờ lần 2"}).json()["id"]
    client.post(f"/api/tro-giup/{yc2}/tra-loi", headers=h_gv, json={"noi_dung": "Đáp lần 2"})

    d1 = client.get(f"/api/tro-giup/{yc1}/chi-tiet", headers=h_gv).json()
    tl1 = [t["noi_dung"] for t in d1["turns"] if t["vai_tro"] == "giao_vien"]
    assert tl1 == ["Đáp lần 1"], tl1


def test_gv_khac_lop_khong_xem_chi_tiet_duoc(db, client):
    pid = _seed(db)
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]
    yc_id = client.post("/api/tro-giup", headers=h_hs, json={"session_id": sid}).json()["id"]

    h_gv2 = _h(client, "gv2")
    r = client.get(f"/api/tro-giup/{yc_id}/chi-tiet", headers=h_gv2)
    assert r.status_code == 400


def test_hs_khong_nho_duoc_phien_nguoi_khac(db, client):
    _seed(db)
    # tạo HS khác chưa có lớp
    other = User(vai_tro=VaiTro.hs, ho_ten="HS B", dang_nhap="hs2",
                 mat_khau_hash=hash_password("password"))
    db.add(other)
    db.commit()
    pid = db.query(Problem).first().id
    h_hs = _h(client, "hs1")
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": pid}).json()["session_id"]

    h_hs2 = _h(client, "hs2")
    r = client.post("/api/tro-giup", headers=h_hs2, json={"session_id": sid})
    assert r.status_code == 400
