"""Chặn dò mật khẩu: khóa mềm sau nhiều lần đăng nhập sai liên tiếp cùng 1 tài khoản."""

import pytest

from app.auth import throttle
from app.auth.security import hash_password
from app.models.user import User, VaiTro


@pytest.fixture(autouse=True)
def _reset_throttle():
    throttle._lan_sai.clear()
    yield
    throttle._lan_sai.clear()


def _seed_hs(db):
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Test", dang_nhap="hs_throttle",
              mat_khau_hash=hash_password("dung-mat-khau"))
    db.add(hs)
    db.commit()


def test_khoa_mem_sau_qua_nhieu_lan_sai(db, client):
    _seed_hs(db)
    for _ in range(throttle.SO_LAN_SAI_TOI_DA):
        r = client.post("/api/auth/login",
                        json={"dang_nhap": "hs_throttle", "mat_khau": "sai-roi"})
        assert r.status_code == 401

    # Lần kế tiếp bị chặn 429 — kể cả khi gõ ĐÚNG mật khẩu (chặn dò, không phải chặn tài khoản)
    r = client.post("/api/auth/login",
                    json={"dang_nhap": "hs_throttle", "mat_khau": "dung-mat-khau"})
    assert r.status_code == 429


def test_dang_nhap_dung_som_khong_bi_khoa_va_reset_bo_dem(db, client):
    _seed_hs(db)
    for _ in range(throttle.SO_LAN_SAI_TOI_DA - 1):
        client.post("/api/auth/login", json={"dang_nhap": "hs_throttle", "mat_khau": "sai-roi"})

    r = client.post("/api/auth/login",
                    json={"dang_nhap": "hs_throttle", "mat_khau": "dung-mat-khau"})
    assert r.status_code == 200  # còn dưới ngưỡng nên không bị chặn

    # Đăng nhập đúng xóa lịch sử sai — sai lại từ đầu KHÔNG bị khóa ngay
    r = client.post("/api/auth/login", json={"dang_nhap": "hs_throttle", "mat_khau": "sai-roi"})
    assert r.status_code == 401


def test_tai_khoan_khac_khong_bi_anh_huong(db, client):
    """Khóa theo TÊN ĐĂNG NHẬP, không phải toàn hệ thống — tài khoản khác vẫn đăng nhập được."""
    _seed_hs(db)
    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS Khác", dang_nhap="hs_khac",
              mat_khau_hash=hash_password("mat-khau-2"))
    db.add(hs2)
    db.commit()

    for _ in range(throttle.SO_LAN_SAI_TOI_DA):
        client.post("/api/auth/login", json={"dang_nhap": "hs_throttle", "mat_khau": "sai-roi"})
    # hs_throttle đã bị khóa mềm...
    r = client.post("/api/auth/login",
                    json={"dang_nhap": "hs_throttle", "mat_khau": "dung-mat-khau"})
    assert r.status_code == 429
    # ...nhưng hs_khac không liên quan, vẫn đăng nhập bình thường
    r = client.post("/api/auth/login",
                    json={"dang_nhap": "hs_khac", "mat_khau": "mat-khau-2"})
    assert r.status_code == 200
