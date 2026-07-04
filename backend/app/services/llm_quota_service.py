"""
Đếm & giới hạn lượt gọi LLM theo ngày (phanh chi phí quota).

Nguyên tắc: KHÔNG chặn việc học. Hội thoại gia sư vượt ngưỡng chỉ chuyển lời
diễn đạt sang mẫu cố định (StubLLMClient) — logic dẫn dắt/CAS/chấm điểm chạy
y nguyên vì vốn không phụ thuộc LLM. Tác vụ chủ động (sinh câu hỏi, phân tích)
vượt ngưỡng thì báo lỗi rõ ràng thay vì âm thầm tạo nội dung mẫu.

Giới hạn đặt trong Cấu hình Admin (0 = không giới hạn):
- `gioi_han_llm_hs_ngay`: lượt hội thoại LLM thật / học sinh / ngày.
- `gioi_han_llm_he_thong_ngay`: tổng lượt LLM thật toàn hệ thống / ngày.
"""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.llm.client import LLMClient, StubLLMClient
from app.models.llm_su_dung import LLMSuDung

LOAI_HOI_THOAI = "hoi_thoai"
LOAI_SINH_CAU_HOI = "sinh_cau_hoi"
LOAI_PHAN_TICH = "phan_tich"
CAC_LOAI = (LOAI_HOI_THOAI, LOAI_SINH_CAU_HOI, LOAI_PHAN_TICH)


def hom_nay_utc() -> str:
    """Ngày UTC dạng YYYY-MM-DD — cùng múi giờ với các timestamp trong DB."""
    return datetime.now(timezone.utc).date().isoformat()


def ghi_luot(db: Session, user_id: int | None, loai: str, so: int = 1) -> None:
    """Cộng `so` lượt gọi LLM thật cho (hôm nay, user_id, loai)."""
    if so <= 0:
        return
    ngay = hom_nay_utc()
    row = (
        db.query(LLMSuDung)
        .filter(LLMSuDung.ngay == ngay, LLMSuDung.user_id == user_id, LLMSuDung.loai == loai)
        .first()
    )
    if row is None:
        row = LLMSuDung(ngay=ngay, user_id=user_id, loai=loai, so_luot=0)
        db.add(row)
    row.so_luot += so
    db.commit()


def tong_hom_nay(db: Session, *, user_id: int | None = None, loai: str | None = None) -> int:
    q = db.query(func.coalesce(func.sum(LLMSuDung.so_luot), 0)).filter(
        LLMSuDung.ngay == hom_nay_utc()
    )
    if user_id is not None:
        q = q.filter(LLMSuDung.user_id == user_id)
    if loai is not None:
        q = q.filter(LLMSuDung.loai == loai)
    return int(q.scalar() or 0)


def _gioi_han(cau_hinh: dict, khoa: str) -> int:
    try:
        return max(0, int(cau_hinh.get(khoa, 0) or 0))
    except (TypeError, ValueError):
        return 0


def vuot_nguong_he_thong(db: Session, cau_hinh: dict) -> bool:
    gh = _gioi_han(cau_hinh, "gioi_han_llm_he_thong_ngay")
    return gh > 0 and tong_hom_nay(db) >= gh


def vuot_nguong_hs(db: Session, cau_hinh: dict, hoc_sinh_id: int) -> bool:
    gh = _gioi_han(cau_hinh, "gioi_han_llm_hs_ngay")
    return gh > 0 and tong_hom_nay(db, user_id=hoc_sinh_id, loai=LOAI_HOI_THOAI) >= gh


def ap_quota_hoi_thoai(
    db: Session, cau_hinh: dict, hoc_sinh_id: int, llm: LLMClient
) -> LLMClient:
    """Hội thoại gia sư: vượt ngưỡng → thay bằng stub, KHÔNG chặn học; còn quota → đếm 1 lượt."""
    if isinstance(llm, StubLLMClient):
        return llm
    if vuot_nguong_hs(db, cau_hinh, hoc_sinh_id) or vuot_nguong_he_thong(db, cau_hinh):
        return StubLLMClient()
    ghi_luot(db, hoc_sinh_id, LOAI_HOI_THOAI)
    return llm


def ap_quota_tac_vu(
    db: Session, cau_hinh: dict, user_id: int | None, llm: LLMClient, loai: str
) -> LLMClient | None:
    """Sinh câu hỏi / phân tích: vượt ngưỡng hệ thống → None (nơi gọi báo lỗi rõ)."""
    if isinstance(llm, StubLLMClient):
        return llm
    if vuot_nguong_he_thong(db, cau_hinh):
        return None
    ghi_luot(db, user_id, loai)
    return llm


LOI_HET_QUOTA = (
    "Hệ thống đã dùng hết hạn mức gọi AI hôm nay. "
    "Vui lòng thử lại ngày mai hoặc tăng giới hạn trong Cấu hình → AI."
)


def thong_ke_su_dung(db: Session, cau_hinh: dict) -> dict:
    """Số liệu hôm nay cho trang Cấu hình Admin."""
    return {
        "ngay": hom_nay_utc(),
        "tong": tong_hom_nay(db),
        "theo_loai": {loai: tong_hom_nay(db, loai=loai) for loai in CAC_LOAI},
        "gioi_han_hs_ngay": _gioi_han(cau_hinh, "gioi_han_llm_hs_ngay"),
        "gioi_han_he_thong_ngay": _gioi_han(cau_hinh, "gioi_han_llm_he_thong_ngay"),
    }
