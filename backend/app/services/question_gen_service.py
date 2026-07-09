"""
Service: sinh câu hỏi AI → lưu DB ở trạng thái cho_duyet; GV duyệt/loại.
"""

import base64
import logging

from sqlalchemy.orm import Session

from app.llm.client import SO_LAN_THU, LLMClient
from app.llm.question_gen import sinh_buoc_goi_y, sinh_nhap, validate_cau_hoi
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

logger = logging.getLogger(__name__)

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
        # AI sinh hàng loạt không tạo trường này (rỗng mặc định); luồng "AI tạo bước và
        # gợi ý" thì GV xem/sửa bản nháp qua ThanCauHoiForm trước khi lưu nên có thể có.
        loi_giai_chi_tiet=str(cau.get("loi_giai_chi_tiet") or "").strip(),
        hien_loi_giai_chi_tiet=bool(cau.get("hien_loi_giai_chi_tiet", False)),
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


def _loc_va_luu_nhap(
    db: Session,
    nhap: list[dict],
    yeu_cau: dict,
    dang,
    nguoi_tao_id: int | None,
) -> list[dict]:
    """Lọc từng câu AI sinh ra (bỏ câu hỏng), lưu câu hợp lệ ở cho_duyet. Trả list mô tả."""
    ket_qua = []
    for item in nhap:
        if not isinstance(item.get("cau"), dict):
            logger.warning("Bỏ câu AI sinh: 'cau' không phải dict (%r)", type(item.get("cau")))
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
            logger.warning("Bỏ câu AI sinh: đề bài rỗng")
            continue
        # Savepoint cho từng câu: một câu hỏng chỉ hủy chính nó, không sập cả mẻ.
        sp = db.begin_nested()
        try:
            canh_bao = validate_cau_hoi(cau)
            problem = _luu_mot_cau(db, cau, nguoi_tao_id)
            db.flush()
            sp.commit()
        except Exception as e:
            sp.rollback()
            logger.warning("Bỏ câu AI sinh: lỗi validate/lưu — %s: %s", type(e).__name__, e)
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
    return ket_qua


def sinh_va_luu(
    db: Session,
    yeu_cau: dict,
    nguoi_tao_id: int | None,
    llm: LLMClient,
) -> list[dict]:
    """Sinh nháp, lưu mỗi câu (kèm cảnh báo) ở cho_duyet. Trả list mô tả.

    Gắn câu sinh ra vào dạng được chọn (dang_id) và đồng bộ tên chuyên đề theo dạng;
    đồng thời truyền tên dạng cho LLM để sinh đúng dạng bài.

    Vì nhiệt độ sinh > 0 khiến thỉnh thoảng AI trả nội dung không hợp lệ (bị lọc bỏ hết),
    tự thử sinh lại tối đa SO_LAN_THU lần trước khi trả rỗng cho GV.
    """
    dang_id = yeu_cau.get("dang_id")
    dang = db.get(Dang, dang_id) if dang_id else None
    if dang is not None:
        yeu_cau = {**yeu_cau, "dang": dang.ten}
        if dang.chuyen_de is not None:
            yeu_cau["chuyen_de"] = dang.chuyen_de.ten

    ket_qua: list[dict] = []
    for lan in range(SO_LAN_THU):
        nhap = sinh_nhap(llm, yeu_cau)
        ket_qua = _loc_va_luu_nhap(db, nhap, yeu_cau, dang, nguoi_tao_id)
        if ket_qua:
            break
        logger.warning(
            "Lần %d/%d: AI sinh %d câu nhưng không câu nào hợp lệ, thử lại.",
            lan + 1, SO_LAN_THU, len(nhap),
        )
    db.commit()
    return ket_qua


def duyet_cau(db: Session, problem_id: int, hanh_dong: str) -> Problem:
    """hanh_dong: 'duyet' → da_duyet (câu vẫn thuộc riêng người tạo); 'loai' → loai."""
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


def _validate_cau_truc(loai_cau: str, cau_truc: list[dict]) -> None:
    """Ràng buộc cấu trúc bước theo loại câu (khớp mô hình dữ liệu có sẵn của hệ thống)."""
    if loai_cau == "TNDS":
        if [b.get("pham_vi") for b in cau_truc] != ["a", "b", "c", "d"]:
            raise ValueError("TNDS phải có đúng 4 bước theo thứ tự ý a, b, c, d")
    else:
        if any(b.get("pham_vi", "ca_bai") != "ca_bai" for b in cau_truc):
            raise ValueError(f"{loai_cau} chỉ dùng pham_vi 'ca_bai' cho mọi bước")


def tao_nhap_buoc_goi_y(db: Session, yeu_cau: dict, llm: LLMClient) -> dict:
    """AI tạo bước và gợi ý: gắn dạng/chuyên đề, validate cấu trúc bước, gọi AI giải + chia
    bước + viết gợi ý cho đề GV đã viết sẵn. CHƯA lưu DB — trả bản nháp {"cau", "canh_bao"}
    để GV xem/sửa trước khi gọi luu_cau_nhap()."""
    loai_cau = yeu_cau.get("loai_cau", "TLN")
    _validate_cau_truc(loai_cau, yeu_cau.get("cau_truc_buoc") or [])

    dang = db.get(Dang, yeu_cau.get("dang_id"))
    if dang is None:
        raise ValueError("Không tìm thấy dạng đã chọn")
    yeu_cau = {
        **yeu_cau,
        "dang": dang.ten,
        "chuyen_de": dang.chuyen_de.ten if dang.chuyen_de else "",
    }
    return sinh_buoc_goi_y(llm, yeu_cau)


def luu_cau_nhap(db: Session, cau: dict, nguoi_tao_id: int | None) -> Problem:
    """Lưu 1 câu GV đã xem/sửa bản nháp (AI tạo bước và gợi ý) — cùng cơ chế _luu_mot_cau
    (nguon=ai_sinh, trang_thai_duyet=cho_duyet) để nội dung AI góp phần luôn qua duyệt,
    dù chính GV là người bấm lưu."""
    problem = _luu_mot_cau(db, cau, nguoi_tao_id)
    db.commit()
    db.refresh(problem)
    return problem


_MIME_ANH_HO_TRO = {"image/png", "image/jpeg", "image/webp"}
_ANH_TOI_DA_BYTES = 5 * 1024 * 1024  # 5MB — tránh phí AI cao bất thường với ảnh quá nặng


def doc_de_tu_anh(llm: LLMClient, anh_base64: str, mime_type: str, loai_cau_ky_vong: str) -> dict:
    """Giải mã + kiểm tra ảnh GV dán, nhờ AI đọc — nhận dạng loại câu + trích đề bài/phương án/ý.

    Không tự sinh nếu ảnh không khớp loại câu GV đang chọn (llm.doc_de_tu_anh tự trả
    khop_loai_cau=False kèm lý do, KHÔNG raise — caller/API tự quyết định hiển thị thế nào)."""
    if loai_cau_ky_vong not in {"TN4PA", "TNDS", "TLN"}:
        raise ValueError("loai_cau_ky_vong không hợp lệ")
    if mime_type not in _MIME_ANH_HO_TRO:
        raise ValueError(f"Định dạng ảnh '{mime_type}' không được hỗ trợ (chỉ PNG/JPEG/WEBP)")

    du_lieu = anh_base64.split(",", 1)[-1] if anh_base64.startswith("data:") else anh_base64
    try:
        anh_bytes = base64.b64decode(du_lieu, validate=True)
    except Exception as e:
        raise ValueError(f"Dữ liệu ảnh không hợp lệ: {e}") from e
    if not anh_bytes:
        raise ValueError("Dữ liệu ảnh rỗng")
    if len(anh_bytes) > _ANH_TOI_DA_BYTES:
        raise ValueError(
            f"Ảnh quá lớn ({len(anh_bytes) / 1024 / 1024:.1f}MB) — tối đa "
            f"{_ANH_TOI_DA_BYTES // 1024 // 1024}MB"
        )
    return llm.doc_de_tu_anh(anh_bytes, mime_type, loai_cau_ky_vong)
