"""Chốt chặn rò rỉ đáp án PHẢI rà cả lượt mở đầu phiên (lời chào đầu tiên), không chỉ
các lượt trả lời sau — đúng bất biến #3 (CLAUDE.md mục 3): rà MỌI phản hồi gửi HS.

Trước khi sửa, tao_phien() gọi llm.dien_dat() thẳng ra Turn mà KHÔNG qua kiem_tra_ro_ri
— nếu AI (hoặc 1 provider lỗi) vô tình để lộ đáp án ngay câu chào đầu, HS thấy luôn."""

from app.llm.client import LLMClient
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro
from app.services.tutor_service import tao_phien


class _LLMLoRiNgayCauChao(LLMClient):
    """Test double: câu chào đầu tiên (dien_dat) rò rỉ thẳng đáp án."""

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
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_leak",
              mat_khau_hash="x")
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_leak",
              mat_khau_hash="x", lop_id=lop.id)
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
    return hs, p


def test_loi_chao_mo_dau_bi_chot_chan_neu_ro_ri(db):
    hs, p = _seed(db)
    llm = _LLMLoRiNgayCauChao()

    session, van_ban = tao_phien(db, hs.id, p.id, llm)

    # HS KHÔNG được thấy đáp án "5" trong câu chào — dù LLM (provider) trả về rò rỉ
    assert "Đáp án là 5" not in van_ban
    assert van_ban == "[Nội dung bị lọc — có thể chứa đáp án]"

    from app.models.turn import Turn
    turn = db.query(Turn).filter(Turn.session_id == session.id).first()
    assert turn.co_bi_chot_chan is True
