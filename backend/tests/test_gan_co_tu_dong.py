"""Test 'Cờ theo dõi': tự động gắn cờ ro_ri_dap_an (từng lượt bị chốt chặn) và
noi_dung_khong_phu_hop (chat AI bị chặn an toàn + yêu cầu 'Nhờ thầy/cô' nhạy cảm)."""

from app.auth.security import hash_password
from app.llm.client import LLMClient
from app.models.flag import Flag, LoaiCo
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.thong_bao import ThongBao
from app.models.turn import Turn
from app.models.user import User, VaiTro
from app.services.tutor_service import tao_phien


class _LLMLoRiNgayCauChao(LLMClient):
    """Test double: câu chào đầu tiên (dien_dat) rò rỉ thẳng đáp án — mirror
    test_leak_guard_opening_turn.py để tái dùng kịch bản chốt chặn có sẵn."""

    def dien_dat(self, chi_thi):
        return "Chào em! Đáp án là 5, em hãy trình bày lại cách làm nhé."

    def sinh_cau_hoi(self, yeu_cau):
        return {"cau_hoi": []}

    def tao_buoc_goi_y(self, yeu_cau):
        return {"cau_hoi": []}

    def doc_de_tu_anh(self, anh_bytes, mime_type, loai_cau_ky_vong):
        raise NotImplementedError


def _seed(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Cờ", dang_nhap="gv_co",
              mat_khau_hash=hash_password("pass"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Cờ", dang_nhap="hs_co",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add_all([gv, hs])
    db.flush()
    lop.gv_id = gv.id

    p = Problem(chuyen_de="Test", loai_cau="TLN", do_kho="tb", de_bai="Tìm x.",
               loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
               nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "5"})
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]))
    db.commit()
    return hs, gv, p


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_leak_tao_co_ro_ri_dap_an_kem_turn_id(db):
    hs, gv, p = _seed(db)
    llm = _LLMLoRiNgayCauChao()

    session, van_ban = tao_phien(db, hs.id, p.id, llm)
    assert "5" not in van_ban  # đã bị viết lại, không lộ đáp án

    turn = db.query(Turn).filter(Turn.session_id == session.id).first()
    assert turn.co_bi_chot_chan is True

    flag = db.query(Flag).filter(
        Flag.session_id == session.id, Flag.loai_co == LoaiCo.ro_ri_dap_an
    ).first()
    assert flag is not None
    assert flag.turn_id == turn.id


def test_khong_ro_ri_thi_khong_tao_co(db):
    """Đối chứng: lượt bình thường (không chốt chặn) KHÔNG tạo cờ ro_ri_dap_an."""
    from app.llm.client import StubLLMClient

    hs, gv, p = _seed(db)
    session, _ = tao_phien(db, hs.id, p.id, StubLLMClient())

    flag = db.query(Flag).filter(
        Flag.session_id == session.id, Flag.loai_co == LoaiCo.ro_ri_dap_an
    ).first()
    assert flag is None


def test_chat_ai_noi_dung_khong_phu_hop_tra_loi_than_thien_khong_lap_tu(db, client):
    """Nội dung 'không phù hợp' thường (không phải khủng hoảng): KHÔNG còn trả lỗi HTTP kỹ
    thuật lặp lại từ khóa — trả 200 kèm 1 lượt chat thân thiện, hướng về bài học, vẫn gắn cờ
    + báo GV như cũ."""
    hs, gv, p = _seed(db)
    h_hs = _h(_login(client, "hs_co"))
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h_hs).json()["session_id"]

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "thầy ơi em mua ma túy được không"}, headers=h_hs)
    assert r.status_code == 200
    body = r.json()
    assert "ma túy" not in body["van_ban"]  # không lặp lại từ khóa nhạy cảm
    assert "bài toán" in body["van_ban"]  # hướng về bài học

    flag = db.query(Flag).filter(
        Flag.session_id == sid, Flag.loai_co == LoaiCo.noi_dung_khong_phu_hop
    ).first()
    assert flag is not None
    assert "ma túy" in flag.ghi_chu  # GV vẫn thấy đúng từ khóa để đánh giá, chỉ HS không thấy

    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    assert tb is not None
    assert tb.tieu_de == "⚠️ Nội dung cần chú ý"
    # Bấm vào thông báo phải mở ĐÚNG cờ này (không chỉ trỏ chung chung về session) — để GV
    # không phải tự tìm trong danh sách "Cờ theo dõi".
    assert tb.lien_ket_loai == "co"
    assert tb.lien_ket_id == flag.id


def test_chat_ai_ngoai_pham_vi_tra_loi_than_thien_khong_gan_co(db, client):
    """Hỏi việc ngoài phạm vi Toán (vd nhờ viết code): trả lời thân thiện, hướng về bài học,
    KHÔNG gắn cờ/báo GV (không phải vấn đề an toàn, chỉ lệch trọng tâm)."""
    hs, gv, p = _seed(db)
    h_hs = _h(_login(client, "hs_co"))
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h_hs).json()["session_id"]

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "thầy ơi viết code Python giúp em với"}, headers=h_hs)
    assert r.status_code == 200
    body = r.json()
    assert "ngoài" in body["van_ban"]

    flag = db.query(Flag).filter(Flag.session_id == sid).first()
    assert flag is None
    assert db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first() is None


def test_chat_ai_khan_cap_khong_chan_tra_loi_am_ap_va_bao_gv(db, client):
    """Dấu hiệu khủng hoảng/tự hại: KHÔNG chặn lạnh bằng lỗi (phản tác dụng với HS đang
    thật sự cần giúp đỡ) — trả 200 kèm câu trả lời ấm áp cố định, phiên vẫn tiếp tục,
    đồng thời gắn cờ + báo GV mức ưu tiên cao nhất (🆘)."""
    hs, gv, p = _seed(db)
    h_hs = _h(_login(client, "hs_co"))
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h_hs).json()["session_id"]

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "em muốn chết"}, headers=h_hs)
    assert r.status_code == 200
    body = r.json()
    assert "quan tâm" in body["van_ban"]
    assert body["da_xong"] is False

    flag = db.query(Flag).filter(
        Flag.session_id == sid, Flag.loai_co == LoaiCo.noi_dung_khong_phu_hop
    ).first()
    assert flag is not None
    assert "KHẨN CẤP" in flag.ghi_chu

    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    assert tb is not None
    assert tb.tieu_de == "🆘 Cần quan tâm khẩn cấp"

    # Cả 2 lượt (HS nói + câu trả lời ấm áp) đều được lưu lại để GV xem lại ngữ cảnh.
    turns = db.query(Turn).filter(Turn.session_id == sid).all()
    assert any(t.noi_dung == "em muốn chết" for t in turns)


def test_nho_thay_co_noi_dung_nhay_cam_van_toi_gv_nhung_gan_co(db, client):
    """Khác chat AI: KHÔNG chặn (có thể là lời kêu cứu thật) — vẫn tạo yêu cầu, vẫn báo
    GV, chỉ khác là gắn thêm cờ + tiêu đề thông báo nâng mức khẩn cấp cao nhất."""
    hs, gv, p = _seed(db)
    h_hs = _h(_login(client, "hs_co"))
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h_hs).json()["session_id"]

    r = client.post("/api/tro-giup", headers=h_hs,
                    json={"session_id": sid, "noi_dung": "em muốn chết"})
    assert r.status_code == 200  # KHÔNG bị chặn — vẫn tạo yêu cầu tới GV

    flag = db.query(Flag).filter(
        Flag.session_id == sid, Flag.loai_co == LoaiCo.noi_dung_khong_phu_hop
    ).first()
    assert flag is not None
    assert "KHẨN CẤP" in flag.ghi_chu

    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    assert tb is not None
    assert tb.tieu_de.startswith("🆘")


def test_nho_thay_co_binh_thuong_khong_gan_co(db, client):
    hs, gv, p = _seed(db)
    h_hs = _h(_login(client, "hs_co"))
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=h_hs).json()["session_id"]

    r = client.post("/api/tro-giup", headers=h_hs,
                    json={"session_id": sid, "noi_dung": "em chưa hiểu bước này ạ"})
    assert r.status_code == 200

    flag = db.query(Flag).filter(
        Flag.session_id == sid, Flag.loai_co == LoaiCo.noi_dung_khong_phu_hop
    ).first()
    assert flag is None

    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).first()
    assert tb.tieu_de == "Học sinh nhờ trợ giúp"
