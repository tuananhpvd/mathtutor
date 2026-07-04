"""
Sinh câu hỏi bằng LLM + validate (thuần, không phụ thuộc DB/web).
Service ở services/question_gen_service.py mới ghi DB.
"""

import re

from app.core.matching.cas import kiem_tra_bieu_thuc, parse_bieu_thuc_an_toan
from app.llm.client import LLMClient

_LOAI_HOP_LE = {"TN4PA", "TNDS", "TLN"}

# Hàm tổ hợp/giai thừa hay bị AI để NGUYÊN DẠNG chưa tính (vd "binomial(15, 3)") thay vì
# rút gọn ra số cụ thể ("455"). Chỉ coi là "trung gian chưa tính" khi biểu thức KHÔNG còn
# biến tự do (vd không phải hàm theo x) — biểu thức còn biến thì giữ dạng hàm là đúng.
_RE_HAM_TRUNG_GIAN = re.compile(
    r"\b(?:binomial|factorial|ff|combinations?|permutations?|comb|perm)\s*\(", re.IGNORECASE
)


def bieu_thuc_trung_gian_chua_tinh(bt: str) -> str | None:
    """None nếu ổn; ngược lại trả giá trị ĐÃ TÍNH gợi ý để thay vào chỗ biểu thức trung gian."""
    if not bt or not _RE_HAM_TRUNG_GIAN.search(str(bt)):
        return None
    try:
        expr = parse_bieu_thuc_an_toan(str(bt))
    except ValueError:
        return None
    if expr.free_symbols:
        return None  # còn biến (vd biểu thức theo x) — không phải kết quả trung gian
    return str(expr)

# Đáp án cuối TLN (định dạng THPT): số thập phân (nguyên hoặc có phần lẻ), tối đa
# 4 ký tự TÍNH CẢ dấu '-' và dấu '.'. Ví dụ hợp lệ: "125", "-125", "3.12", "-3.1".
_DO_DAI_TOI_DA_DAP_AN_TLN = 4
_RE_SO_THAP_PHAN = re.compile(r"^-?(\d+\.\d+|\d+|\.\d+)$")


def dap_an_tln_hop_le(dap_an_cuoi: str) -> bool:
    """True nếu đáp án TLN đúng dạng số thập phân và không quá 4 ký tự."""
    s = str(dap_an_cuoi).strip()
    if not s or len(s) > _DO_DAI_TOI_DA_DAP_AN_TLN:
        return False
    return bool(_RE_SO_THAP_PHAN.match(s))


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
        dap_an = meta.get("dap_an_cuoi", "")
        if not str(dap_an).strip():
            canh_bao.append("TLN thiếu dap_an_cuoi")
        elif not dap_an_tln_hop_le(dap_an):
            canh_bao.append(
                f"TLN dap_an_cuoi {dap_an!r} không hợp lệ: phải là số thập phân, "
                f"tối đa {_DO_DAI_TOI_DA_DAP_AN_TLN} ký tự (gồm cả dấu '-' và '.')"
            )

    # Validate SymPy mọi bieu_thuc_ket_qua
    steps = cau.get("solution_steps") or []
    if not steps:
        canh_bao.append("Thiếu solution_steps")
    for s in steps:
        bt = s.get("bieu_thuc_ket_qua", "")
        if not kiem_tra_bieu_thuc(bt):
            canh_bao.append(f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): "
                            f"SymPy không parse được '{bt}'")
        else:
            gia_tri_goi_y = bieu_thuc_trung_gian_chua_tinh(bt)
            if gia_tri_goi_y is not None:
                canh_bao.append(
                    f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): bieu_thuc_ket_qua "
                    f"{bt!r} là biểu thức trung gian chưa tính — nên thay bằng kết quả "
                    f"cụ thể {gia_tri_goi_y!r}"
                )
        if not s.get("danh_sach_goi_y"):
            canh_bao.append(f"Bước {s.get('thu_tu')} ({s.get('pham_vi')}): thiếu gợi ý")

    return canh_bao


def sinh_nhap(llm: LLMClient, yeu_cau: dict) -> list[dict]:
    """Gọi LLM sinh nháp, trả list[{cau, canh_bao}]."""
    ket_qua = llm.sinh_cau_hoi(yeu_cau)
    cau_hoi = ket_qua.get("cau_hoi", [])
    return [{"cau": c, "canh_bao": validate_cau_hoi(c)} for c in cau_hoi]
