"""
Service: sinh câu hỏi AI → lưu DB ở trạng thái cho_duyet; GV duyệt/loại.
"""

from sqlalchemy.orm import Session

from app.llm.client import LLMClient
from app.llm.question_gen import sinh_nhap
from app.models.problem import (
    CheDoSoKhopEnum,
    DoKho,
    LoaiCau,
    Nguon,
    Problem,
    TrangThaiDuyet,
)
from app.models.solution_step import SolutionStep


def _luu_mot_cau(db: Session, cau: dict, nguoi_tao_id: int | None) -> Problem:
    steps = cau.pop("solution_steps", [])
    problem = Problem(
        chuyen_de=cau.get("chuyen_de", ""),
        dang_id=cau.get("dang_id"),
        loai_cau=LoaiCau(cau["loai_cau"]),
        do_kho=DoKho(cau.get("do_kho", "tb")),
        de_bai=cau.get("de_bai", ""),
        loai_dap_an_nhap=cau.get("loai_dap_an_nhap", ""),
        che_do_so_khop=CheDoSoKhopEnum(cau.get("che_do_so_khop", "tuong_duong")),
        trang_thai_duyet=TrangThaiDuyet.cho_duyet,
        nguon=Nguon.ai_sinh,
        nguoi_tao_id=nguoi_tao_id,
        meta=cau.get("meta", {}),
    )
    db.add(problem)
    db.flush()
    for s in steps:
        db.add(SolutionStep(
            problem_id=problem.id,
            thu_tu=s.get("thu_tu", 1),
            pham_vi=s.get("pham_vi", "ca_bai"),
            mo_ta=s.get("mo_ta", ""),
            bieu_thuc_ket_qua=s.get("bieu_thuc_ket_qua", ""),
            danh_sach_goi_y=s.get("danh_sach_goi_y", []),
        ))
    return problem


def sinh_va_luu(
    db: Session,
    yeu_cau: dict,
    nguoi_tao_id: int | None,
    llm: LLMClient,
) -> list[dict]:
    """Sinh nháp, lưu mỗi câu (kèm cảnh báo) ở cho_duyet. Trả list mô tả."""
    nhap = sinh_nhap(llm, yeu_cau)
    ket_qua = []
    for item in nhap:
        problem = _luu_mot_cau(db, dict(item["cau"]), nguoi_tao_id)
        ket_qua.append({
            "id": problem.id,
            "loai_cau": problem.loai_cau.value,
            "do_kho": problem.do_kho.value,
            "de_bai": problem.de_bai,
            "trang_thai_duyet": problem.trang_thai_duyet.value,
            "canh_bao": item["canh_bao"],
        })
    db.commit()
    return ket_qua


def duyet_cau(db: Session, problem_id: int, hanh_dong: str) -> Problem:
    """hanh_dong: 'duyet' → da_duyet, 'loai' → loai."""
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise ValueError("Không tìm thấy câu hỏi")
    if hanh_dong == "duyet":
        problem.trang_thai_duyet = TrangThaiDuyet.da_duyet
    elif hanh_dong == "loai":
        problem.trang_thai_duyet = TrangThaiDuyet.loai
    else:
        raise ValueError("hanh_dong phải là 'duyet' hoặc 'loai'")
    db.commit()
    db.refresh(problem)
    return problem
