"""Turn phải ghi lại bước/ý mà lượt đó thuộc về (cột turns.buoc / turns.y).

FE dùng dữ liệu này để dựng "dải phân cách bước" trong khung chat — nhờ vậy HS biết mình
đang ở bước nào, KỂ CẢ khi thoát ra rồi bấm "Làm tiếp" (tải lại lịch sử từ CSDL). Trước đây
turns không lưu bước nên lịch sử cũ không thể dựng lại được mốc chuyển bước.

Mô tả bước KHÔNG lưu vào turn — tra động lúc render qua "mo_ta_cac_buoc", để GV sửa mô tả
thì lịch sử hiển thị theo bản mới, không lệch.
"""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.turn import Turn
from app.models.user import User, VaiTro


def _seed_tln_2_buoc(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_buoc",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_buoc",
              mat_khau_hash=hash_password("pass"))
    db.add_all([hs, gv])
    db.flush()
    lop.gv_id = gv.id

    p = Problem(chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "7"})
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="Bước một",
                        bieu_thuc_ket_qua="3", danh_sach_goi_y=["g1", "g2"]))
    db.add(SolutionStep(problem_id=p.id, thu_tu=2, pham_vi="ca_bai", mo_ta="Bước hai",
                        bieu_thuc_ket_qua="7", danh_sach_goi_y=["g3", "g4"]))
    db.commit()
    return hs, p


def _tok(client, dang_nhap):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": "pass"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_turn_ghi_buoc_va_phan_cach_khi_chuyen_buoc(client, db):
    hs, p = _seed_tln_2_buoc(db)
    h = _tok(client, "hs_buoc")

    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h).json()["session_id"]

    # Lượt mở đầu phải thuộc bước 1
    turn_dau = db.query(Turn).filter(Turn.session_id == sid).order_by(Turn.id).first()
    assert turn_dau.buoc == 1

    # Trả lời ĐÚNG bước 1 → sang bước 2
    r = client.post(f"/api/sessions/{sid}/message", json={"dap_an_nhap": "3"}, headers=h)
    assert r.status_code == 200
    assert r.json()["buoc_hien_tai"] == 2

    turns = db.query(Turn).filter(Turn.session_id == sid).order_by(Turn.id).all()
    # Làm đúng + chuyển bước → 3 lượt, theo đúng mạch hội thoại tự nhiên:
    #   HS trả lời (bước CŨ) → gia sư CHỐT KHEN (bước CŨ) → gia sư DẪN bước mới (bước MỚI)
    # Nhờ vậy dải phân cách (FE dựng ở chỗ bước đổi) rơi vào GIỮA câu khen và lời dẫn — trước
    # đây gộp 1 lượt nên câu khen bị đẩy sang phía bước sau, đọc rất ngược.
    assert turns[-3].vai_tro.value == "hoc_sinh" and turns[-3].buoc == 1
    assert turns[-2].vai_tro.value == "gia_su" and turns[-2].buoc == 1
    assert turns[-1].vai_tro.value == "gia_su" and turns[-1].buoc == 2

    # Câu chốt khen là văn bản TẤT ĐỊNH (không tốn thêm lượt LLM) và được trả về cho FE
    body = r.json()
    assert body["van_ban_chot"]
    assert body["van_ban_chot"] == turns[-2].noi_dung


def test_khong_tach_loi_chot_khi_van_o_cung_buoc(client, db):
    """Trả lời SAI (không chuyển bước) → không có câu chốt khen, chỉ 1 lượt gia sư như cũ."""
    hs, p = _seed_tln_2_buoc(db)
    h = _tok(client, "hs_buoc")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h).json()["session_id"]

    truoc = db.query(Turn).filter(Turn.session_id == sid).count()
    r = client.post(f"/api/sessions/{sid}/message", json={"dap_an_nhap": "999"}, headers=h)
    assert r.json()["van_ban_chot"] is None
    # chỉ thêm 2 lượt (HS + gia sư), không có lượt chốt khen xen vào
    assert db.query(Turn).filter(Turn.session_id == sid).count() == truoc + 2


def test_chi_tiet_phien_tra_buoc_va_mo_ta_cac_buoc_da_toi(client, db):
    hs, p = _seed_tln_2_buoc(db)
    h = _tok(client, "hs_buoc")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h).json()["session_id"]

    # Còn ở bước 1 → CHỈ được thấy mô tả bước 1; mô tả bước 2 là gợi ý trước, không lộ.
    ct = client.get(f"/api/sessions/{sid}", headers=h).json()
    assert ct["mo_ta_cac_buoc"] == {"1": "Bước một"}
    assert all("buoc" in t for t in ct["turns"])

    # Sang bước 2 → mới thấy mô tả bước 2
    client.post(f"/api/sessions/{sid}/message", json={"dap_an_nhap": "3"}, headers=h)
    ct2 = client.get(f"/api/sessions/{sid}", headers=h).json()
    assert ct2["mo_ta_cac_buoc"] == {"1": "Bước một", "2": "Bước hai"}


def test_mo_ta_buoc_tra_dong_theo_ban_moi_nhat(client, db):
    """GV sửa mô tả bước → lịch sử hội thoại hiển thị theo bản MỚI (không lưu cứng vào turn)."""
    hs, p = _seed_tln_2_buoc(db)
    h = _tok(client, "hs_buoc")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h).json()["session_id"]

    buoc1 = db.query(SolutionStep).filter(
        SolutionStep.problem_id == p.id, SolutionStep.thu_tu == 1).first()
    buoc1.mo_ta = "Mô tả đã sửa"
    db.commit()

    ct = client.get(f"/api/sessions/{sid}", headers=h).json()
    assert ct["mo_ta_cac_buoc"]["1"] == "Mô tả đã sửa"


def test_mo_ta_rong_thi_khong_tra_ve(client, db):
    """Bước chưa có mô tả (GV bỏ trống) → không có khóa trong map; FE chỉ hiện 'BƯỚC x/y'."""
    hs, p = _seed_tln_2_buoc(db)
    buoc1 = db.query(SolutionStep).filter(
        SolutionStep.problem_id == p.id, SolutionStep.thu_tu == 1).first()
    buoc1.mo_ta = ""
    db.commit()

    h = _tok(client, "hs_buoc")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h).json()["session_id"]
    ct = client.get(f"/api/sessions/{sid}", headers=h).json()
    assert "1" not in (ct["mo_ta_cac_buoc"] or {})
