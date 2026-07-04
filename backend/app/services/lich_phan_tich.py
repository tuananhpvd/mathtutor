"""
Lịch chạy nền: tự động (tái) sinh phân tích năng lực AI cho học sinh đến hạn.

Thay cho việc GV/HS phải bấm "Cập nhật" thủ công. Đọc cấu hình admin mỗi vòng nên
admin bật/tắt hoặc đổi chu kỳ KHÔNG cần khởi động lại server. Lời gọi LLM chạy trong
thread riêng (asyncio.to_thread) để không chặn event loop.
"""

import asyncio
import logging
import os

from app.db.base import SessionLocal
from app.llm.client import StubLLMClient, get_llm_client
from app.services.admin_service import lay_cau_hinh
from app.services.llm_quota_service import LOAI_PHAN_TICH, ghi_luot, vuot_nguong_he_thong
from app.services.phan_tich_service import quet_tai_sinh

logger = logging.getLogger("mathtutor.lich_phan_tich")

CHU_KY_MAC_DINH_PHUT = 360
CHU_KY_TOI_THIEU_PHUT = 5

_task: asyncio.Task | None = None


def _chay_mot_lan() -> dict:
    """Một lần quét (đồng bộ — gọi trong thread). Tự mở/đóng DB session riêng."""
    db = SessionLocal()
    try:
        cau_hinh = lay_cau_hinh(db)
        llm = get_llm_client(cau_hinh)
        dung_llm_that = not isinstance(llm, StubLLMClient)
        if dung_llm_that and vuot_nguong_he_thong(db, cau_hinh):
            logger.info("Phân tích AI nền: bỏ qua vòng này — đã chạm giới hạn lượt LLM hôm nay")
            return {"da_quet": 0, "da_cap_nhat": 0, "loi": 0, "bo_qua_quota": True}
        ket = quet_tai_sinh(db, llm)
        if dung_llm_that:
            ghi_luot(db, None, LOAI_PHAN_TICH, so=ket.get("da_quet", 0))
        if ket["da_cap_nhat"] or ket["loi"]:
            logger.info(
                "Phân tích AI nền: quét %d, cập nhật %d, lỗi %d",
                ket["da_quet"], ket["da_cap_nhat"], ket["loi"],
            )
        return ket
    finally:
        db.close()


def _doc_cau_hinh() -> tuple[bool, int]:
    db = SessionLocal()
    try:
        ch = lay_cau_hinh(db)
    finally:
        db.close()
    bat = bool(ch.get("tu_dong_phan_tich", True))
    try:
        chu_ky = int(ch.get("chu_ky_phut_phan_tich", CHU_KY_MAC_DINH_PHUT) or CHU_KY_MAC_DINH_PHUT)
    except (TypeError, ValueError):
        chu_ky = CHU_KY_MAC_DINH_PHUT
    return bat, max(CHU_KY_TOI_THIEU_PHUT, chu_ky)


async def _vong_lap() -> None:
    while True:
        try:
            bat, chu_ky = _doc_cau_hinh()
            if bat:
                await asyncio.to_thread(_chay_mot_lan)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — lịch nền không bao giờ được làm sập app
            logger.exception("Lỗi vòng lặp phân tích AI nền")
            chu_ky = CHU_KY_MAC_DINH_PHUT
        await asyncio.sleep(chu_ky * 60)


def khoi_dong() -> None:
    """Khởi động lịch nền (gọi trong lifespan). Bỏ qua khi đang chạy test."""
    global _task
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    if _task is None or _task.done():
        _task = asyncio.create_task(_vong_lap())
        logger.info("Đã khởi động lịch phân tích AI nền.")


async def dung() -> None:
    """Dừng lịch nền (gọi khi tắt app)."""
    global _task
    if _task is not None and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
