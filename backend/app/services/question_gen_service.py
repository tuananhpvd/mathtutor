"""
Service: sinh câu hỏi AI → lưu DB ở trạng thái cho_duyet; GV duyệt/loại.
"""

from sqlalchemy.orm import Session

from app.llm.client import LLMClient
from app.llm.question_gen import sinh_nhap, validate_cau_hoi
from app.models.danh_muc import Dang
from app.models.problem import (
    CheDoSoKhopEnum,
    DoKho,
    LoaiCau,
    Nguon,
    Problem,
    TrangThaiDuyet,
)
from app.models.solution_step import SolutionStep

_LOAI_DAP_AN = {"TN4PA": "chon_phuong_an", "TNDS": "dung_sai_4y", "TLN": "gia_tri"}


def _enum_an_toan(enum_cls, gia_tri, mac_dinh):
    try:
        return enum_cls(gia_tri)
    except (ValueError, KeyError):
        return mac_dinh


def _luu_mot_cau(db: Session, cau: dict, nguoi_tao_id: int | None) -> Problem:
    # Phòng thủ kiểu dữ liệu để KHÔNG bao giờ sập khi LLM trả bất thường.
    steps = cau.get("solution_steps")
    steps = steps if isinstance(steps, list) else []
    meta = cau.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    loai = _enum_an_toan(LoaiCau, cau.get("loai_cau"), LoaiCau.TLN)
    loai_dap_an = cau.get("loai_dap_an_nhap") or _LOAI_DAP_AN.get(loai.value, "")

    problem = Problem(
        chuyen_de=str(cau.get("chuyen_de") or ""),
        dang_id=cau.get("dang_id"),
        loai_cau=loai,
        do_kho=_enum_an_toan(DoKho, cau.get("do_kho", "tb"), DoKho.tb),
        de_bai=str(cau.get("de_bai") or ""),
        loai_dap_an_nhap=loai_dap_an,
        che_do_so_khop=_enum_an_toan(
            CheDoSoKhopEnum, cau.get("che_do_so_khop", "tuong_duong"),
            CheDoSoKhopEnum.tuong_duong,
        ),
        trang_thai_duyet=TrangThaiDuyet.cho_duyet,
        nguon=Nguon.ai_sinh,
        nguoi_tao_id=nguoi_tao_id,
        meta=meta,
    )
    db.add(problem)
    db.flush()
    for s in steps:
        if not isinstance(s, dict):
            continue
        gy = s.get("danh_sach_goi_y")
        db.add(SolutionStep(
            problem_id=problem.id,
            thu_tu=int(s.get("thu_tu", 1) or 1),
            pham_vi=str(s.get("pham_vi") or "ca_bai"),
            mo_ta=str(s.get("mo_ta") or ""),
            bieu_thuc_ket_qua=str(s.get("bieu_thuc_ket_qua") or ""),
            danh_sach_goi_y=gy if isinstance(gy, list) else [],
        ))
    return problem


def sinh_va_luu(
    db: Session,
    yeu_cau: dict,
    nguoi_tao_id: int | None,
    llm: LLMClient,
) -> list[dict]:
    """Sinh nháp, lưu mỗi câu (kèm cảnh báo) ở cho_duyet. Trả list mô tả.

    Gắn câu sinh ra vào dạng được chọn (dang_id) và đồng bộ tên chuyên đề theo dạng;
    đồng thời truyền tên dạng cho LLM để sinh đúng dạng bài.
    """
    dang_id = yeu_cau.get("dang_id")
    dang = db.get(Dang, dang_id) if dang_id else None
    if dang is not None:
        yeu_cau = {**yeu_cau, "dang": dang.ten}
        if dang.chuyen_de is not None:
            yeu_cau["chuyen_de"] = dang.chuyen_de.ten

    nhap = sinh_nhap(llm, yeu_cau)
    ket_qua = []
    for item in nhap:
        if not isinstance(item.get("cau"), dict):
            continue
        cau = dict(item["cau"])
        # Ép các trường ĐÃ BIẾT từ yêu cầu GV (tránh phụ thuộc LLM trả đúng tên khóa).
        cau["loai_cau"] = yeu_cau.get("loai_cau", cau.get("loai_cau"))
        cau["do_kho"] = yeu_cau.get("do_kho", cau.get("do_kho", "tb"))
        if dang is not None:
            cau["dang_id"] = dang.id
            cau["chuyen_de"] = yeu_cau.get("chuyen_de", cau.get("chuyen_de", ""))
        # Bỏ qua câu rỗng/không có đề (không lưu rác).
        if not str(cau.get("de_bai") or "").strip():
            continue
        # Savepoint cho từng câu: một câu hỏng chỉ hủy chính nó, không sập cả mẻ.
        sp = db.begin_nested()
        try:
            canh_bao = validate_cau_hoi(cau)
            problem = _luu_mot_cau(db, cau, nguoi_tao_id)
            db.flush()
            sp.commit()
        except Exception:
            sp.rollback()
            continue
        ket_qua.append({
            "id": problem.id,
            "loai_cau": problem.loai_cau.value,
            "do_kho": problem.do_kho.value,
            "chuyen_de": problem.chuyen_de,
            "de_bai": problem.de_bai,
            "meta": problem.meta or {},
            "trang_thai_duyet": problem.trang_thai_duyet.value,
            "canh_bao": canh_bao,
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
