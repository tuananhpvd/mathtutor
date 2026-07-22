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


# Chuỗi đáp án 4 ý a→d đúng khuôn few-shot từng bị rò rỉ vào prompt (xem ghi chú trong
# prompts.py _MAU_TNDS, sự cố v137): AI có xu hướng CHÉP nguyên khuôn này thay vì tự giải độc
# lập từng ý. Không chặn lưu — chỉ nhắc GV kiểm kỹ, vì 4 ý độc lập vẫn có xác suất nhỏ ra
# đúng khuôn xen kẽ một cách tự nhiên (1/16 mỗi chiều).
_KHUON_MAU_TNDS_NGHI_NGO = [
    ["Dung", "Sai", "Dung", "Sai"],
    ["Sai", "Dung", "Sai", "Dung"],
]


def canh_bao_khuon_mau_tnds(y: list[dict]) -> list[str]:
    """Cảnh báo khi 4 đáp án a→d khớp NGUYÊN VĂN khuôn xen kẽ nghi ngờ chép mẫu."""
    if len(y) != 4:
        return []
    theo_ky_hieu = {item.get("ky_hieu"): item.get("dap_an") for item in y}
    day = [theo_ky_hieu.get(k) for k in ("a", "b", "c", "d")]
    if day in _KHUON_MAU_TNDS_NGHI_NGO:
        return [
            "4 ý ra đúng khuôn xen kẽ Đúng/Sai — trùng mẫu ví dụ hay bị AI copy thay vì tự "
            "giải độc lập từng ý. Hãy đối chiếu KỸ từng ý với lời giải chi tiết trước khi duyệt."
        ]
    return []


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
        canh_bao += canh_bao_khuon_mau_tnds(y)
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

    if not str(cau.get("loi_giai_chi_tiet") or "").strip():
        canh_bao.append("Thiếu lời giải chi tiết — GV nên tự bổ sung trước khi cho HS xem lại")

    return canh_bao


def sinh_nhap(llm: LLMClient, yeu_cau: dict) -> list[dict]:
    """Gọi LLM sinh nháp, trả list[{cau, canh_bao}]."""
    ket_qua = llm.sinh_cau_hoi(yeu_cau)
    cau_hoi = ket_qua.get("cau_hoi", [])
    return [{"cau": c, "canh_bao": validate_cau_hoi(c)} for c in cau_hoi]


def _doi_chieu_cau_truc_buoc(cau: dict, cau_truc: list[dict]) -> list[str]:
    """So số bước + số gợi ý AI THỰC TRẢ với cau_truc GV yêu cầu — không chặn lưu, chỉ
    cảnh báo để GV biết mà tự bổ sung/sửa trong bước xem trước trước khi lưu."""
    canh_bao: list[str] = []
    steps = cau.get("solution_steps") or []
    if len(steps) != len(cau_truc):
        canh_bao.append(
            f"Số bước AI trả ({len(steps)}) khác số bước yêu cầu ({len(cau_truc)})"
        )
    theo_pham_vi = {s.get("pham_vi"): s for s in steps if isinstance(s, dict)}
    for i, b in enumerate(cau_truc):
        pham_vi = b.get("pham_vi", "ca_bai")
        so_goi_y_yc = int(b.get("so_goi_y", 0) or 0)
        s = theo_pham_vi.get(pham_vi) if pham_vi != "ca_bai" else (
            steps[i] if i < len(steps) and isinstance(steps[i], dict) else None
        )
        if s is None:
            continue  # đã báo lệch số bước ở trên, khỏi lặp lại
        so_goi_y_thuc = len(s.get("danh_sach_goi_y") or [])
        if so_goi_y_thuc != so_goi_y_yc:
            nhan = f"ý {pham_vi}" if pham_vi != "ca_bai" else f"bước {i + 1}"
            canh_bao.append(
                f"Số gợi ý AI viết cho {nhan} ({so_goi_y_thuc}) khác số yêu cầu ({so_goi_y_yc})"
            )
    return canh_bao


def sinh_buoc_goi_y(llm: LLMClient, yeu_cau: dict) -> dict:
    """AI tạo bước và gợi ý: GV đã viết đề bài (+ phương án/ý) — AI CHỈ giải + chia bước +
    viết gợi ý. Trả {"cau": {...}, "canh_bao": [...]} — CHƯA lưu DB (caller tự lưu sau khi
    GV xem/sửa bản nháp).

    Ép các trường GV đã biết/đã viết (đề bài, phương án/ý, loại câu, độ khó, chuyên đề/dạng)
    — không phụ thuộc AI giữ nguyên, tránh sai lệch nội dung GV đã cung cấp.
    """
    ket_qua = llm.tao_buoc_goi_y(yeu_cau)
    cau_hoi = ket_qua.get("cau_hoi") or []
    if not cau_hoi or not isinstance(cau_hoi[0], dict):
        raise ValueError("AI không trả về câu hỏi hợp lệ")
    cau = dict(cau_hoi[0])

    loai_cau = yeu_cau.get("loai_cau", cau.get("loai_cau", "TLN"))
    cau["loai_cau"] = loai_cau
    cau["do_kho"] = yeu_cau.get("do_kho", cau.get("do_kho", "tb"))
    cau["de_bai"] = yeu_cau.get("de_bai", cau.get("de_bai", ""))
    cau["chuyen_de"] = yeu_cau.get("chuyen_de", cau.get("chuyen_de", ""))
    if yeu_cau.get("dang_id") is not None:
        cau["dang_id"] = yeu_cau["dang_id"]

    meta = cau.get("meta")
    meta = dict(meta) if isinstance(meta, dict) else {}
    meta_nhap = yeu_cau.get("meta_nhap") or {}
    if loai_cau == "TN4PA" and meta_nhap.get("phuong_an"):
        meta["phuong_an"] = dict(meta_nhap["phuong_an"])
    elif loai_cau == "TNDS" and meta_nhap.get("y"):
        y_nhap = {y.get("ky_hieu"): y.get("noi_dung_y", "") for y in meta_nhap["y"]}
        y_ai = {y.get("ky_hieu"): y for y in (meta.get("y") or []) if isinstance(y, dict)}
        meta["y"] = [
            {**y_ai.get(k, {}), "ky_hieu": k, "noi_dung_y": y_nhap.get(k, "")}
            for k in ("a", "b", "c", "d")
        ]
    cau["meta"] = meta

    canh_bao = validate_cau_hoi(cau)
    canh_bao += _doi_chieu_cau_truc_buoc(cau, yeu_cau.get("cau_truc_buoc") or [])
    return {"cau": cau, "canh_bao": canh_bao}
