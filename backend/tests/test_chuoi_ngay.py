"""Tests C1: chuỗi ngày học + cột mốc nhẹ."""

from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.session import Session as SessionModel, TrangThaiSession
from app.models.user import User, VaiTro
from app.services.chuoi_ngay_service import (
    DINH_NGHIA_COT_MOC,
    dem_bai_hoan_thanh,
    ho_so_chuoi_va_moc,
    kiem_tra_va_cap_nhat_cot_moc,
    tinh_chuoi_ngay,
)


def _user(db, dn="hs1"):
    u = User(
        vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap=dn,
        mat_khau_hash=hash_password("pw"),
    )
    db.add(u)
    db.flush()
    return u


def _session(db, hs_id, trang_thai=TrangThaiSession.hoan_thanh, ngay_truoc=0, problem_id=1):
    dt = datetime.now(timezone.utc) - timedelta(days=ngay_truoc)
    s = SessionModel(
        hoc_sinh_id=hs_id,
        problem_id=problem_id,
        trang_thai=trang_thai,
        bat_dau_luc=dt,
        cap_nhat_luc=dt,
        bi_an=False,
    )
    db.add(s)
    db.flush()
    return s


# --- Streak tests ---

def test_streak_khong_co_session(db):
    hs = _user(db)
    assert tinh_chuoi_ngay(db, hs.id) == 0


def test_streak_hom_nay(db):
    hs = _user(db)
    _session(db, hs.id, ngay_truoc=0)
    db.commit()
    assert tinh_chuoi_ngay(db, hs.id) == 1


def test_streak_lien_tiep_3_ngay(db):
    hs = _user(db)
    for i in range(3):
        _session(db, hs.id, ngay_truoc=i)
    db.commit()
    assert tinh_chuoi_ngay(db, hs.id) == 3


def test_streak_bi_dut(db):
    hs = _user(db)
    # Hôm nay và 2 ngày trước (bỏ qua hôm qua → streak chỉ = 1)
    _session(db, hs.id, ngay_truoc=0)
    _session(db, hs.id, ngay_truoc=2)
    db.commit()
    assert tinh_chuoi_ngay(db, hs.id) == 1


def test_streak_hom_qua_khong_hom_nay(db):
    hs = _user(db)
    _session(db, hs.id, ngay_truoc=1)
    _session(db, hs.id, ngay_truoc=2)
    db.commit()
    # Chưa học hôm nay, nhưng hôm qua có → tính từ hôm qua
    assert tinh_chuoi_ngay(db, hs.id) == 2


def test_streak_session_bi_an_khong_tinh(db):
    hs = _user(db)
    s = _session(db, hs.id, ngay_truoc=0)
    s.bi_an = True
    db.commit()
    assert tinh_chuoi_ngay(db, hs.id) == 0


# --- Dem bai hoan thanh ---

def test_dem_bai_hoan_thanh(db):
    hs = _user(db)
    _session(db, hs.id, trang_thai=TrangThaiSession.hoan_thanh)
    _session(db, hs.id, trang_thai=TrangThaiSession.dang_lam)
    db.commit()
    assert dem_bai_hoan_thanh(db, hs.id) == 1


# --- Cột mốc ---

def test_cot_moc_bai_dau_tien(db):
    hs = _user(db)
    _session(db, hs.id)
    db.commit()
    kiem_tra_va_cap_nhat_cot_moc(db, hs.id)
    db.commit()
    ho_so = ho_so_chuoi_va_moc(db, hs.id)
    loai_ds = [m["loai"] for m in ho_so["cot_moc_da_dat"]]
    assert "bai_dau_tien" in loai_ds


def test_cot_moc_khong_trao_lai_lan_2(db):
    hs = _user(db)
    _session(db, hs.id)
    db.commit()
    kiem_tra_va_cap_nhat_cot_moc(db, hs.id)
    kiem_tra_va_cap_nhat_cot_moc(db, hs.id)
    db.commit()
    from app.models.cot_moc import CotMoc
    so_moc_bai_dau = (
        db.query(CotMoc)
        .filter(CotMoc.hoc_sinh_id == hs.id, CotMoc.loai == "bai_dau_tien")
        .count()
    )
    assert so_moc_bai_dau == 1


def test_cot_moc_chuoi_3_ngay(db):
    hs = _user(db)
    for i in range(3):
        _session(db, hs.id, ngay_truoc=i)
    db.commit()
    kiem_tra_va_cap_nhat_cot_moc(db, hs.id)
    db.commit()
    ho_so = ho_so_chuoi_va_moc(db, hs.id)
    loai_ds = [m["loai"] for m in ho_so["cot_moc_da_dat"]]
    assert "chuoi_3_ngay" in loai_ds


def test_cot_moc_chuoi_chua_du(db):
    hs = _user(db)
    _session(db, hs.id, ngay_truoc=0)
    db.commit()
    kiem_tra_va_cap_nhat_cot_moc(db, hs.id)
    db.commit()
    ho_so = ho_so_chuoi_va_moc(db, hs.id)
    loai_ds = [m["loai"] for m in ho_so["cot_moc_da_dat"]]
    assert "chuoi_3_ngay" not in loai_ds


def test_api_chuoi_ngay(client, db):
    hs = User(
        vai_tro=VaiTro.hs, ho_ten="HS Test", dang_nhap="hs_test",
        mat_khau_hash=hash_password("password"),
    )
    db.add(hs)
    db.commit()
    _session(db, hs.id, ngay_truoc=0)
    db.commit()

    token = client.post("/api/auth/login", json={"dang_nhap": "hs_test", "mat_khau": "password"}).json()["access_token"]
    r = client.get("/api/hs/chuoi-ngay", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "chuoi_ngay" in data
    assert "tong_bai_hoan_thanh" in data
    assert "cot_moc_da_dat" in data


def test_dinh_nghia_cot_moc_hop_le():
    for m in DINH_NGHIA_COT_MOC:
        assert "loai" in m
        assert "tieu_de" in m
        assert "nguong_bai" in m or "nguong_chuoi" in m
