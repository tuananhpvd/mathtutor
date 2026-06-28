"""Test GV đặt lại tiến độ HS trực tiếp."""

from tests.test_api_flow import _h, _token, seed_all


def seed_with_lop_gv(db):
    """seed_all + gán GV phụ trách lớp."""
    from app.models.lop import Lop

    hs, gv, admin, p = seed_all(db)
    lop = db.query(Lop).filter(Lop.ten == "12A1").first()
    lop.gv_id = gv.id
    db.commit()
    return hs, gv, admin, p


def test_gv_dat_lai_truc_tiep(client, db):
    hs, gv, admin, p = seed_with_lop_gv(db)
    from app.models.session import Session as SessionModel

    # HS tạo phiên
    hs_tok = _token(client, "hs_test")
    client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(hs_tok))

    so_phien_truoc = db.query(SessionModel).filter(
        SessionModel.hoc_sinh_id == hs.id, SessionModel.bi_an == False  # noqa: E712
    ).count()
    assert so_phien_truoc > 0

    # GV đặt lại ngay
    gv_tok = _token(client, "gv_test")
    r = client.post(f"/api/gv/dat-lai/{hs.id}", headers=_h(gv_tok))
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert r.json()["so_phien_da_an"] == so_phien_truoc

    # Session phải bị ẩn
    so_phien_sau = db.query(SessionModel).filter(
        SessionModel.hoc_sinh_id == hs.id, SessionModel.bi_an == False  # noqa: E712
    ).count()
    assert so_phien_sau == 0


def test_gv_khong_co_quyen_lop_khac(client, db):
    hs, gv, admin, _ = seed_with_lop_gv(db)
    # Tạo GV khác không phụ trách lớp này
    from app.auth.security import hash_password
    from app.models.user import User, VaiTro

    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_test",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()

    gv2_tok = _token(client, "gv2_test")
    r = client.post(f"/api/gv/dat-lai/{hs.id}", headers=_h(gv2_tok))
    assert r.status_code == 400


def test_hs_khong_truy_cap_duoc(client, db):
    hs, _, _, _ = seed_with_lop_gv(db)
    tok = _token(client, "hs_test")
    r = client.post(f"/api/gv/dat-lai/{hs.id}", headers=_h(tok))
    assert r.status_code == 403


def test_dat_lai_hs_khong_co_phien(client, db):
    hs, gv, _, _ = seed_with_lop_gv(db)
    gv_tok = _token(client, "gv_test")
    r = client.post(f"/api/gv/dat-lai/{hs.id}", headers=_h(gv_tok))
    assert r.status_code == 200
    assert r.json()["so_phien_da_an"] == 0


def test_dat_lai_xoa_phan_tich(client, db):
    hs, gv, _, p = seed_with_lop_gv(db)
    from app.models.phan_tich import PhanTich

    # Thêm bản ghi phân tích giả
    pt = PhanTich(hoc_sinh_id=hs.id, noi_dung_hs="test", noi_dung_gv="ok",
                  so_bai_luc_tao=1, nguon="ai")
    db.add(pt)
    db.commit()

    gv_tok = _token(client, "gv_test")
    client.post(f"/api/gv/dat-lai/{hs.id}", headers=_h(gv_tok))

    con_lai = db.query(PhanTich).filter(PhanTich.hoc_sinh_id == hs.id).count()
    assert con_lai == 0
