"""
Sinh câu hỏi bằng LLM + validate (thuần, không phụ thuộc DB/web).
Service ở services/question_gen_service.py mới ghi DB.
"""

from app.core.matching.cas import kiem_tra_bieu_thuc
from app.llm.client import LLMClient

_LOAI_HOP_LE = {"TN4PA", "TNDS", "TLN"}


def validate_cau_hoi(cau: dict) -> list[str]:
    """Trả danh sách cảnh báo cho một câu hỏi nháp. Rỗng = hợp lệ."""
    canh_bao: list[str] = []

    loai = cau.get("loai_cau")
    if loai not in _LOAI_HOP_LE:
        canh_bao.append(f"loai_cau không hợp lệ: {loai!r}")

    if not cau.get("de_bai", "").strip():
        canh_bao.append("Thiếu đề bài")

    meta = cau.get("meta") or {}
    if loai == "TN4PA":
        pa = meta.get("phuong_an") or {}
        if set(pa.keys()) != {"A", "B", "C", "D"}:
            canh_bao.append("TN4PA cần đủ 4 phương án A/B/C/D")
        if meta.get("dap_an_dung") not in {"A", "B", "C", "D"}:
            canh_bao.append("TN4PA thiếu/sai dap_an_dung")
    elif loai == "TNDS":
        y = meta.get("y") or []
        if len(y) != 4:
            canh_bao.append("TNDS cần đúng 4 ý")
        for item in y:
            if item.get("dap_an") not in {"Dung", "Sai"}:
                canh_bao.append(f"Ý {item.get('ky_hieu')} có dap_an không hợp lệ")
    elif loai == "TLN":
        if not str(meta.get("dap_an_cuoi", "")).strip():
            canh_bao.append("TLN thiếu dap_an_cuoi")

    # Validate SymPy mọi bieu_thuc_ket_qua
    steps = cau.get("solution_steps") or []
    if not steps:
        canh_bao.append("Thiếu solution_steps")
    for s in steps:
        bt = s.get("bieu_thuc_ket_qua", "")
        if not kiem_tra_bieu_thuc(bt):
            canh_bao.append(f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): "
                            f"SymPy không parse được '{bt}'")
        if not s.get("danh_sach_goi_y"):
            canh_bao.append(f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): thiếu gợi ý")

    return canh_bao


def sinh_nhap(llm: LLMClient, yeu_cau: dict) -> list[dict]:
    """Gọi LLM sinh nháp, trả list[{cau, canh_bao}]."""
    ket_qua = llm.sinh_cau_hoi(yeu_cau)
    cau_hoi = ket_qua.get("cau_hoi", [])
    return [{"cau": c, "canh_bao": validate_cau_hoi(c)} for c in cau_hoi]
