"""Test trang 'sản phẩm đang hoàn thiện' — chặn người ngoài, không chặn người có mã xem trước."""

from app.services.admin_service import dat_cau_hinh


def test_bao_tri_tat_mac_dinh(client):
    r = client.get("/api/trang-thai-bao-tri")
    assert r.status_code == 200
    assert r.json() == {"bao_tri": False, "hop_le": False}


def test_bao_tri_bat_khong_co_ma(client, db):
    dat_cau_hinh(db, "bao_tri_bat", True)
    dat_cau_hinh(db, "bao_tri_ma", "bi-mat-123")
    r = client.get("/api/trang-thai-bao-tri")
    assert r.json() == {"bao_tri": True, "hop_le": False}


def test_bao_tri_bat_ma_sai(client, db):
    dat_cau_hinh(db, "bao_tri_bat", True)
    dat_cau_hinh(db, "bao_tri_ma", "bi-mat-123")
    r = client.get("/api/trang-thai-bao-tri", params={"ma": "sai"})
    assert r.json() == {"bao_tri": True, "hop_le": False}


def test_bao_tri_bat_ma_dung(client, db):
    dat_cau_hinh(db, "bao_tri_bat", True)
    dat_cau_hinh(db, "bao_tri_ma", "bi-mat-123")
    r = client.get("/api/trang-thai-bao-tri", params={"ma": "bi-mat-123"})
    assert r.json() == {"bao_tri": True, "hop_le": True}


def test_bao_tri_khong_lo_ma_qua_response(client, db):
    dat_cau_hinh(db, "bao_tri_bat", True)
    dat_cau_hinh(db, "bao_tri_ma", "bi-mat-123")
    r = client.get("/api/trang-thai-bao-tri", params={"ma": "sai"})
    assert "bi-mat-123" not in r.text
