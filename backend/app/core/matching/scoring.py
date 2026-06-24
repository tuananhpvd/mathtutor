BANG_BAC_THANG = {0: 0.0, 1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}


def diem_bac_thang(k: int) -> float:
    """Điểm TNDS theo số ý đúng k trong [0..4]."""
    if k not in BANG_BAC_THANG:
        raise ValueError(f"k phải trong [0..4], nhận được: {k}")
    return BANG_BAC_THANG[k]
