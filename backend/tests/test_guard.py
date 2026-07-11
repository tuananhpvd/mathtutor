"""Tests cho core/guard Phase 4."""

from app.core.guard.leak import MucDoRoRi, kiem_tra_ro_ri
from app.core.guard.safety import kiem_tra_an_toan
from app.core.guard.scope import kiem_tra_pham_vi

# ----- Leak detection -----

def test_van_ban_sach():
    k = kiem_tra_ro_ri("Em hãy nghĩ xem bước đầu tiên là gì?")
    assert k.muc_do == MucDoRoRi.sach


def test_chua_gia_tri_dap_an():
    # "là 42" sau từ khoá → phải phát hiện
    k = kiem_tra_ro_ri("Đáp án là 42", gia_tri_dap_an="42")
    assert k.muc_do == MucDoRoRi.ro_ri

    # Số "0" xuất hiện TỰ NHIÊN trong biểu thức toán → KHÔNG được filter
    k2 = kiem_tra_ro_ri("Em hãy xét x=0 và x=2, đâu là cực tiểu?", gia_tri_dap_an="0")
    assert k2.muc_do != MucDoRoRi.ro_ri


def test_chua_cum_tu_ro_ri():
    k = kiem_tra_ro_ri("Đáp án là: x = 5")
    assert k.muc_do == MucDoRoRi.ro_ri


def test_tu_khoa_chon_phuong_an():
    k = kiem_tra_ro_ri("Em nên chọn B nhé")
    assert k.muc_do == MucDoRoRi.ro_ri


def test_van_ban_thay_the_khi_ro_ri():
    k = kiem_tra_ro_ri("kết quả là 10")
    assert k.muc_do == MucDoRoRi.ro_ri
    assert "lọc" in k.van_ban_thay_the or "Nội dung" in k.van_ban_thay_the
    assert k.van_ban_goc == "kết quả là 10"


def test_goi_y_hop_le_khong_ro_ri():
    k = kiem_tra_ro_ri("Em hãy áp dụng công thức đạo hàm. Bước tiếp theo là gì?")
    assert k.muc_do in (MucDoRoRi.sach, MucDoRoRi.nghi_ngo)


def test_guard_khong_import_llm():
    import ast
    import pathlib
    for fname in ["leak.py", "safety.py", "scope.py"]:
        src = pathlib.Path(f"app/core/guard/{fname}").read_text(encoding="utf-8")
        tree = ast.parse(src)
        imports = [
            n.names[0].name if isinstance(n, ast.Import) else n.module
            for n in ast.walk(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        assert not any("llm" in (imp or "") for imp in imports), f"{fname} imports llm"
        assert not any("fastapi" in (imp or "") for imp in imports), f"{fname} imports fastapi"


# ----- Safety filter -----

def test_noi_dung_hop_le():
    k = kiem_tra_an_toan("Em không hiểu bước này, nhờ thầy gợi ý")
    assert k.an_toan is True


def test_noi_dung_khong_phu_hop():
    k = kiem_tra_an_toan("thầy ơi em mua ma túy được không")
    assert k.an_toan is False
    assert "ma túy" in k.ly_do
    assert k.khan_cap is False


def test_dau_hieu_khan_cap_tu_tu():
    k = kiem_tra_an_toan("thầy dạy em tự tử đi")
    assert k.an_toan is False
    assert k.khan_cap is True


def test_dau_hieu_khan_cap_muon_chet():
    """'em muốn chết' KHÔNG chứa 'tự tử' nhưng vẫn phải bắt được — đây chính là lỗ hổng
    thực tế đã phát hiện qua báo cáo người dùng trước khi mở rộng danh sách này."""
    k = kiem_tra_an_toan("em muốn chết")
    assert k.an_toan is False
    assert k.khan_cap is True


def test_dau_hieu_khan_cap_khong_muon_song():
    k = kiem_tra_an_toan("em không muốn sống nữa")
    assert k.an_toan is False
    assert k.khan_cap is True


def test_cuong_dieu_van_bi_bat_co_tinh_thien_ve_an_toan():
    """Quyết định thiết kế CÓ CHỦ ĐÍCH: 'mệt muốn chết' (cường điệu, vô hại) cũng bị bắt vì
    không thể phân biệt chắc chắn với lời nói thật bằng regex — chấp nhận báo động giả rẻ
    (1 câu quan tâm hơi thừa) hơn là bỏ lọt lời kêu cứu thật. KHÔNG coi đây là bug cần fix."""
    k = kiem_tra_an_toan("bài này khó quá, em mệt muốn chết")
    assert k.an_toan is False
    assert k.khan_cap is True


def test_bai_toan_binh_thuong_khong_bi_bat_nham_khan_cap():
    k = kiem_tra_an_toan("em tính ra kết quả là hết nghiệm, bài này khó thật")
    assert k.an_toan is True
    assert k.khan_cap is False


def test_ngoai_pham_vi():
    k = kiem_tra_an_toan("thầy ơi viết code Python giúp em")
    assert k.an_toan is False


def test_bai_toan_binh_thuong():
    k = kiem_tra_an_toan("Em tính đạo hàm ra f'(x) = 3x^2 + 2")
    assert k.an_toan is True


# ----- Danh sách từ khóa nạp từ ngoài (admin quản lý) -----

def test_khong_dau_van_bat_duoc_tu_khoa_mac_dinh():
    """HS gõ không dấu ('tu tu' thay vì 'tự tử') vẫn phải bị phát hiện — chuẩn hóa bỏ dấu
    áp dụng cho cả từ khóa mặc định, không chỉ từ khóa admin tự thêm."""
    k = kiem_tra_an_toan("thay day em tu tu di")
    assert k.an_toan is False
    assert k.khan_cap is True


def test_truyen_danh_sach_rieng_ghi_de_mac_dinh():
    """Truyền danh sách rỗng → không còn bắt được từ khóa mặc định 'ma túy' (chứng minh
    caller có thể ghi đè hoàn toàn danh sách mặc định, đúng như tầng admin sẽ làm)."""
    k = kiem_tra_an_toan("thầy ơi em mua ma túy được không", [], [], [])
    assert k.an_toan is True


def test_tu_khoa_tuy_chinh_khong_dau_duoc_bat():
    """Từ khóa do admin tự thêm ('bỏ học đi lang thang') cũng được chuẩn hóa bỏ dấu khi
    so khớp, không chỉ danh sách mặc định."""
    k = kiem_tra_an_toan(
        "em tinh bo hoc di lang thang", [], ["bỏ học đi lang thang"], []
    )
    assert k.an_toan is False
    assert "bỏ học đi lang thang" in k.ly_do


def test_tu_khoa_don_tu_khong_khop_nham_ben_trong_tu_khac():
    """'kill' phải có ranh giới từ — không khớp nhầm bên trong 'skill' (kỹ năng)."""
    k = kiem_tra_an_toan("em cần luyện skill làm bài nhanh hơn", [], ["kill"], [])
    assert k.an_toan is True


# ----- Scope lock -----

def test_chuyen_de_duoc_phep():
    k = kiem_tra_pham_vi("Hàm số", ["Hàm số", "Tích phân"])
    assert k.cho_phep is True


def test_chuyen_de_khong_duoc_phep():
    k = kiem_tra_pham_vi("Hình học không gian", ["Hàm số"])
    assert k.cho_phep is False
    assert "Hình học không gian" in k.ly_do


def test_khong_gioi_han():
    k = kiem_tra_pham_vi("Bất kỳ chuyên đề nào", None)
    assert k.cho_phep is True


def test_danh_sach_rong():
    k = kiem_tra_pham_vi("Hàm số", [])
    assert k.cho_phep is False


# ----- API monitor -----

def _seed_users(db):
    from app.auth.security import hash_password
    from app.models.lop import Lop
    from app.models.user import User, VaiTro
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    db.add_all([hs, gv])
    db.commit()


def test_monitor_flags_phan_quyen(db, client):
    """HS không được xem flags."""
    _seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "hs1", "mat_khau": "password"})
    token = r.json()["access_token"]
    r2 = client.get("/api/monitor/flags", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403


def test_monitor_flags_gv_duoc_xem(db, client):
    """GV xem được flags (danh sách rỗng)."""
    _seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "gv1", "mat_khau": "password"})
    token = r.json()["access_token"]
    r2 = client.get("/api/monitor/flags", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


def test_monitor_session_turns_phan_quyen(db, client):
    """HS không được xem turns của session."""
    _seed_users(db)
    r = client.post("/api/auth/login", json={"dang_nhap": "hs1", "mat_khau": "password"})
    token = r.json()["access_token"]
    r2 = client.get("/api/monitor/sessions/1/turns", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403
