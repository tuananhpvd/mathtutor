"""
Lớp khóa phạm vi: HS chỉ được học bài thuộc chuyên đề đã mở.
Không import LLM, không import web framework.
"""

from dataclasses import dataclass


@dataclass
class KetQuaPhamVi:
    cho_phep: bool
    ly_do: str = ""


def kiem_tra_pham_vi(
    chuyen_de_bai: str,
    chuyen_de_duoc_phep: list[str] | None,
) -> KetQuaPhamVi:
    """
    Kiểm tra bài có thuộc chuyên đề HS được phép không.

    chuyen_de_duoc_phep=None → không giới hạn (mặc định mở tất cả).
    """
    if chuyen_de_duoc_phep is None:
        return KetQuaPhamVi(cho_phep=True)

    if not chuyen_de_duoc_phep:
        return KetQuaPhamVi(cho_phep=False, ly_do="Không có chuyên đề nào được phép")

    if chuyen_de_bai in chuyen_de_duoc_phep:
        return KetQuaPhamVi(cho_phep=True)

    return KetQuaPhamVi(
        cho_phep=False,
        ly_do=f"Chuyên đề '{chuyen_de_bai}' chưa được mở cho học sinh này",
    )
