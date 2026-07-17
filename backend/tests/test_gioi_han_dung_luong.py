"""Middleware chặn request quá lớn (main.py::gioi_han_dung_luong_request) — phòng vệ toàn
app qua header Content-Length, không chỉ dựa vào max_length/kiểm tra từng field riêng lẻ."""

import app.main as main_module


def test_request_vuot_gioi_han_bi_chan_413(client, monkeypatch):
    monkeypatch.setattr(main_module, "_MAX_BODY_BYTES", 10)
    r = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "password"})
    assert r.status_code == 413


def test_request_binh_thuong_khong_bi_chan(client):
    r = client.post("/api/auth/login", json={"dang_nhap": "admin", "mat_khau": "sai"})
    assert r.status_code != 413
