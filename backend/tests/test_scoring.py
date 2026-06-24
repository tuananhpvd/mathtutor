import pytest

from app.core.matching.scoring import diem_bac_thang


def test_bang_bac_thang():
    assert diem_bac_thang(0) == 0.0
    assert diem_bac_thang(1) == 0.1
    assert diem_bac_thang(2) == 0.25
    assert diem_bac_thang(3) == 0.5
    assert diem_bac_thang(4) == 1.0


def test_k_out_of_range():
    with pytest.raises(ValueError):
        diem_bac_thang(5)
    with pytest.raises(ValueError):
        diem_bac_thang(-1)
