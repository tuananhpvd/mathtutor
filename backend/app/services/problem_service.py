"""Service: GV/Admin sửa & xóa câu hỏi (Problem) + các bước lời giải."""

from sqlalchemy.orm import Session

from app.models.danh_muc import Dang
from app.models.problem import DoKho, Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.solution_step import SolutionStep


def sua_problem(db: Session, problem_id: int, du_lieu: dict) -> Problem:
    """Cập nhật từng phần. du_lieu là dict đã exclude_unset (chỉ trường được gửi).

    - dang_id: nếu đổi, đồng bộ luôn `chuyen_de` (denormalized) theo chuyên đề của dạng.
    - solution_steps: nếu gửi, thay thế toàn bộ các bước cũ.
    """
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")

    if "dang_id" in du_lieu:
        dang_id = du_lieu["dang_id"]
        if dang_id is not None:
            dang = db.get(Dang, dang_id)
            if dang is None:
                raise ValueError("Không tìm thấy dạng")
            p.dang_id = dang.id
            # Đồng bộ tên chuyên đề trừ khi caller gửi chuyen_de tường minh.
            if "chuyen_de" not in du_lieu and dang.chuyen_de is not None:
                p.chuyen_de = dang.chuyen_de.ten
        else:
            p.dang_id = None

    if "chuyen_de" in du_lieu and du_lieu["chuyen_de"]:
        p.chuyen_de = du_lieu["chuyen_de"]
    if "de_bai" in du_lieu and du_lieu["de_bai"]:
        p.de_bai = du_lieu["de_bai"]
    if "do_kho" in du_lieu and du_lieu["do_kho"]:
        try:
            p.do_kho = DoKho(du_lieu["do_kho"])
        except ValueError:
            raise ValueError("do_kho phải là de | tb | kho")
    if "meta" in du_lieu and du_lieu["meta"] is not None:
        p.meta = du_lieu["meta"]
    if "trang_thai_duyet" in du_lieu and du_lieu["trang_thai_duyet"]:
        try:
            p.trang_thai_duyet = TrangThaiDuyet(du_lieu["trang_thai_duyet"])
        except ValueError:
            raise ValueError("trang_thai_duyet không hợp lệ")

    if "solution_steps" in du_lieu and du_lieu["solution_steps"] is not None:
        # Xóa các bước cũ rồi tạo lại từ danh sách mới.
        for s in list(p.solution_steps):
            db.delete(s)
        db.flush()
        for s in du_lieu["solution_steps"]:
            db.add(SolutionStep(
                problem_id=p.id,
                thu_tu=s.get("thu_tu", 1),
                pham_vi=s.get("pham_vi", "ca_bai"),
                mo_ta=s.get("mo_ta", ""),
                bieu_thuc_ket_qua=s.get("bieu_thuc_ket_qua", ""),
                danh_sach_goi_y=s.get("danh_sach_goi_y", []),
            ))

    db.commit()
    db.refresh(p)
    return p


def xoa_problem(db: Session, problem_id: int) -> None:
    p = db.get(Problem, problem_id)
    if p is None:
        raise ValueError("Không tìm thấy câu hỏi")
    if db.query(SessionModel).filter(SessionModel.problem_id == problem_id).count() > 0:
        raise ValueError("Câu hỏi đã có phiên học của HS, không thể xóa")
    for s in list(p.solution_steps):
        db.delete(s)
    db.delete(p)
    db.commit()
