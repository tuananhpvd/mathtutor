"""Sự cố thực tế trên production (2026-08-03, giám khảo phát hiện): sau khi HS làm ĐÚNG
bước 1 (tính đạo hàm y' = 3x^2-3) và sang bước 2 (xét dấu y'), AI tự đạo hàm lại rồi CHÈN
THẲNG biểu thức "3x^2-3" (viết bằng ký hiệu LaTeX, khác cú pháp SymPy lưu trong CSDL) vào lời
dẫn — dù prompt cấm "tự tính ra kết quả thay học sinh" và "tự suy ra thêm gợi ý mới ngoài
y_goi_y". Chốt chặn cũ chỉ biết đáp án CUỐI (chữ cái TN4PA) nên không phát hiện được.

Test này tái tạo ĐÚNG kịch bản đó qua xu_ly_luot() (không chỉ unit test leak.py đơn lẻ) để
xác nhận toàn bộ đường dây — tutor_service truyền đủ giá trị mọi bước, leak.py so khớp đúng
ngữ nghĩa — hoạt động khớp nhau khi ghép lại."""

from app.llm.client import LLMClient, StubLLMClient
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.turn import Turn, VaiTroTurn
from app.models.user import User, VaiTro
from app.services.tutor_service import tao_phien, xu_ly_luot


class _LLMLoBieuThucBuocTruoc(LLMClient):
    """Test double: mô phỏng ĐÚNG hành vi AI thật gây sự cố — tự đạo hàm rồi viết ra biểu
    thức cụ thể (LaTeX) thay vì giữ ký hiệu y' như "y_goi_y" yêu cầu."""

    def dien_dat(self, chi_thi):
        return "Đúng rồi! Giờ em hãy giải phương trình $3x^2 - 3 = 0$ để tìm nghiệm x nhé."

    def sinh_cau_hoi(self, yeu_cau):
        return {"cau_hoi": []}

    def tao_buoc_goi_y(self, yeu_cau):
        return {"cau_hoi": []}

    def doc_de_tu_anh(self, anh_bytes, mime_type, loai_cau_ky_vong):
        raise NotImplementedError


def _seed_tn4pa_2_buoc(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_leak2", mat_khau_hash="x")
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_leak2", mat_khau_hash="x",
              lop_id=lop.id)
    db.add_all([gv, hs])
    db.flush()
    lop.gv_id = gv.id

    p = Problem(
        chuyen_de="Test", loai_cau="TN4PA", do_kho="de",
        de_bai="Hàm số $y = x^3 - 3x + 3$ đồng biến trên khoảng nào sau đây?",
        loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
        nguoi_tao_id=gv.id,
        meta={
            "dap_an_dung": "B",
            "phuong_an": {"A": "(-oo;1)", "B": "(1;+oo)", "C": "(-oo;2)", "D": "(-1;1)"},
            "bat_buoc_suy_luan": True,
        },
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
                        mo_ta="Tính đạo hàm y'", bieu_thuc_ket_qua="3*x**2 - 3",
                        danh_sach_goi_y=["g1", "g2"]))
    db.add(SolutionStep(problem_id=p.id, thu_tu=2, pham_vi="ca_bai",
                        mo_ta="Xét dấu y' và kết luận", bieu_thuc_ket_qua="",
                        danh_sach_goi_y=["g1", "g2"]))
    db.commit()
    return hs, p


def test_khong_lo_bieu_thuc_buoc_da_qua_khi_ai_tu_tinh_lai(db):
    hs, p = _seed_tn4pa_2_buoc(db)
    session, _ = tao_phien(db, hs.id, p.id, StubLLMClient())

    # HS trả lời ĐÚNG bước 1 (đạo hàm) → orchestrator chuyển sang bước 2 và gọi dien_dat()
    # cho lời dẫn bước mới — đây là lượt mà AI thật đã lộ đáp án trên production.
    kq = xu_ly_luot(
        db, session, p, "em tính ra 3x^2-3", "3*x**2 - 3", False,
        _LLMLoBieuThucBuocTruoc(),
    )

    assert kq["buoc_hien_tai"] == 2  # xác nhận đã CHUYỂN bước, đúng bối cảnh sự cố
    assert "3x^2 - 3" not in kq["van_ban"]
    assert "3x^2" not in kq["van_ban"]

    turn = (
        db.query(Turn)
        .filter(Turn.session_id == session.id, Turn.vai_tro == VaiTroTurn.gia_su)
        .order_by(Turn.id.desc())
        .first()
    )
    assert turn.co_bi_chot_chan is True
