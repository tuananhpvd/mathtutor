"""HS tự đăng ký bằng MÃ LỚP — Pha B (endpoint công khai đầu tiên của hệ thống).

Trọng tâm là các ràng buộc AN TOÀN, vì đây là luồng không cần đăng nhập:
vai trò cứng `hs`, lớp lấy từ mã, chặn lớp chưa có GV, chặn trùng tên đăng nhập,
mã hết hạn/thu hồi, và throttle chỉ đếm lần nhập SAI mã.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.auth.security import hash_password
from app.auth.throttle import SO_LAN_SAI_MA_TOI_DA, xoa_lich_su_sai_ma
from app.core.ma_lop import chuan_hoa
from app.models.lop import Lop
from app.models.thong_bao import ThongBao
from app.models.user import TrangThaiUser, User, VaiTro


@pytest.fixture(autouse=True)
def _reset_throttle():
    """Throttle là bộ nhớ tiến trình → dọn giữa các test để không dính nhau."""
    xoa_lich_su_sai_ma("testclient")
    yield
    xoa_lich_su_sai_ma("testclient")


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _seed(db):
    """gv1 có lớp 12A1; ngoài ra 1 lớp MỒ CÔI (chưa có GV) để kiểm chặn."""
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Một", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV Hai", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv, gv2])
    db.flush()
    lop = Lop(ten="12A1", gv_id=gv.id)
    lop_mo_coi = Lop(ten="Lớp mồ côi", gv_id=None)
    db.add_all([lop, lop_mo_coi])
    db.flush()
    db.commit()
    return gv, gv2, lop, lop_mo_coi


def _tao_ma(client, lop_id, dn="gv1"):
    r = client.post(f"/api/gv/lop/{lop_id}/ma", headers=_h(client, dn))
    assert r.status_code == 200, r.text
    return r.json()["ma_lop"]


# ---------- GV quản lý mã ----------

def test_gv_tao_va_thu_hoi_ma(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    assert "-" in ma  # dạng hiển thị có gạch cho dễ đọc

    ds = client.get("/api/gv/lop", headers=_h(client, "gv1")).json()
    assert next(x for x in ds if x["id"] == lop.id)["ma_lop"] == ma

    r = client.delete(f"/api/gv/lop/{lop.id}/ma", headers=_h(client, "gv1"))
    assert r.status_code == 200
    ds = client.get("/api/gv/lop", headers=_h(client, "gv1")).json()
    assert next(x for x in ds if x["id"] == lop.id)["ma_lop"] is None


def test_doi_ma_lam_ma_cu_het_hieu_luc(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    ma_cu = _tao_ma(client, lop.id)
    ma_moi = _tao_ma(client, lop.id)
    assert ma_cu != ma_moi
    assert client.get(f"/api/auth/lop-tu-ma?ma={ma_cu}").status_code == 400
    assert client.get(f"/api/auth/lop-tu-ma?ma={ma_moi}").status_code == 200


def test_gv_khac_khong_tao_duoc_ma_lop_nguoi_khac(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    assert client.post(f"/api/gv/lop/{lop.id}/ma", headers=_h(client, "gv2")).status_code == 403
    assert client.delete(f"/api/gv/lop/{lop.id}/ma", headers=_h(client, "gv2")).status_code == 403


# ---------- Xem trước lớp ----------

def test_xem_truoc_lop_tu_ma(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    d = client.get(f"/api/auth/lop-tu-ma?ma={ma}").json()
    assert d["lop_ten"] == "12A1"
    assert d["gv_ten"] == "GV Một"


def test_ma_go_kieu_nao_cung_khop(db, client):
    """HS gõ chữ thường / bỏ gạch / thêm khoảng trắng đều phải vào được."""
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    sach = chuan_hoa(ma)
    for bien_the in (sach, sach.lower(), ma, f"  {sach}  "):
        r = client.get("/api/auth/lop-tu-ma", params={"ma": bien_the})
        assert r.status_code == 200, (bien_the, r.text)


# ---------- Đăng ký ----------

def test_dang_ky_thanh_cong_vao_dung_lop_va_vao_hoc_ngay(db, client):
    gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)

    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "Trần Bình", "dang_nhap": "binhtran", "mat_khau": "matkhau123",
    })
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["vai_tro"] == "hs" and d["ho_ten"] == "Trần Bình"
    assert d["access_token"]  # vào học ngay, không phải đăng nhập lại

    hs = db.query(User).filter(User.dang_nhap == "binhtran").first()
    assert hs.vai_tro == VaiTro.hs
    assert hs.lop_id == lop.id
    assert hs.trang_thai == TrangThaiUser.hoat_dong

    # GV được báo để biết ai vừa vào lớp mình
    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).all()
    assert any("Trần Bình" in t.noi_dung and "12A1" in t.noi_dung for t in tb)

    # Token dùng được ngay
    me = client.get("/api/hs/ping", headers={"Authorization": f"Bearer {d['access_token']}"})
    assert me.status_code == 200


def test_khong_the_tu_dat_vai_tro_hay_lop(db, client):
    """Chặn leo thang đặc quyền: client gửi kèm vai_tro/lop_id phải bị BỎ QUA."""
    _gv, _gv2, lop, mo_coi = _seed(db)
    ma = _tao_ma(client, lop.id)

    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "Kẻ Gian", "dang_nhap": "kegian", "mat_khau": "matkhau123",
        "vai_tro": "admin", "lop_id": mo_coi.id, "la_quan_ly": True,
    })
    assert r.status_code == 201
    hs = db.query(User).filter(User.dang_nhap == "kegian").first()
    assert hs.vai_tro == VaiTro.hs      # KHÔNG thành admin
    assert hs.lop_id == lop.id          # theo MÃ, không theo input
    assert not hs.la_quan_ly


def test_chan_lop_chua_co_giao_vien(db, client):
    """Giữ chuỗi trách nhiệm: lớp không GV thì không ai đỡ khi HS bí → không nhận đăng ký."""
    _gv, _gv2, _lop, mo_coi = _seed(db)
    from app.services import dang_ky_service
    dang_ky_service.tao_ma_lop(db, mo_coi)          # cấp mã thẳng, bỏ qua tầng API
    ma = mo_coi.ma_lop

    r = client.get(f"/api/auth/lop-tu-ma?ma={ma}")
    assert r.status_code == 400
    assert "chưa có giáo viên" in r.json()["detail"]

    r2 = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "A", "dang_nhap": "aaa1", "mat_khau": "matkhau123"})
    assert r2.status_code == 400


def test_ma_sai_va_ma_het_han_bi_tu_choi(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    _tao_ma(client, lop.id)

    assert client.get("/api/auth/lop-tu-ma?ma=ZZZZ-ZZZZ").status_code == 400

    lop.ma_het_han = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    r = client.get(f"/api/auth/lop-tu-ma?ma={lop.ma_lop}")
    assert r.status_code == 400
    # Cùng một thông điệp với mã không tồn tại → không lộ mã nào từng có thật
    assert "hết hiệu lực" in r.json()["detail"]


def test_trung_ten_dang_nhap_bi_chan(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    body = {"ma": ma, "ho_ten": "A", "dang_nhap": "trungten", "mat_khau": "matkhau123"}
    assert client.post("/api/auth/dang-ky", json=body).status_code == 201
    r = client.post("/api/auth/dang-ky", json=body)
    assert r.status_code == 400
    assert "đã có người dùng" in r.json()["detail"]


def test_mat_khau_ngan_bi_tu_choi(db, client):
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "A", "dang_nhap": "matkhauyeu", "mat_khau": "123"})
    assert r.status_code == 422  # pydantic min_length=6


def test_tai_khoan_moi_duoc_ghi_tao_luc(db, client):
    """`tao_luc` là cơ sở cho trần chống spam theo ngày — không có thì trần vô hiệu."""
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)
    client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "A", "dang_nhap": "cotaoluc", "mat_khau": "matkhau123"})
    hs = db.query(User).filter(User.dang_nhap == "cotaoluc").first()
    assert hs.tao_luc is not None


def test_tran_dang_ky_theo_ngay(db, client, monkeypatch):
    from app.services import dang_ky_service

    monkeypatch.setattr(dang_ky_service, "TRAN_DANG_KY_NGAY", 2)
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)

    for i in range(2):
        r = client.post("/api/auth/dang-ky", json={
            "ma": ma, "ho_ten": f"HS {i}", "dang_nhap": f"ngay{i}", "mat_khau": "matkhau123"})
        assert r.status_code == 201
    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "Thừa", "dang_nhap": "ngaythua", "mat_khau": "matkhau123"})
    assert r.status_code == 400
    assert "hôm nay" in r.json()["detail"]


def test_tai_khoan_cu_tao_luc_NULL_khong_tinh_vao_tran_ngay(db, client, monkeypatch):
    """HS cũ (tạo trước khi có cột `tao_luc`) không được chiếm chỗ của trần 24h."""
    from app.services import dang_ky_service

    monkeypatch.setattr(dang_ky_service, "TRAN_DANG_KY_NGAY", 1)
    _gv, _gv2, lop, _mc = _seed(db)
    cu = User(vai_tro=VaiTro.hs, ho_ten="HS Cũ", dang_nhap="hscu",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(cu)
    db.commit()
    # LƯU Ý: truyền `tao_luc=None` lúc khởi tạo KHÔNG tạo ra NULL — SQLAlchemy vẫn áp
    # `default=` khi giá trị là None. Phải UPDATE sau khi insert mới mô phỏng được tài khoản
    # cũ có trước cột này.
    db.query(User).filter(User.id == cu.id).update({"tao_luc": None})
    db.commit()

    ma = _tao_ma(client, lop.id)
    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "Mới", "dang_nhap": "hsmoi", "mat_khau": "matkhau123"})
    assert r.status_code == 201, r.text  # HS cũ NULL không làm đầy trần


def test_tran_tong_si_so(db, client, monkeypatch):
    """Chặn kiểu nhỏ giọt kéo dài nhiều ngày mà trần/ngày không bắt được."""
    from app.services import dang_ky_service

    monkeypatch.setattr(dang_ky_service, "TRAN_HS_MOI_LOP", 1)
    _gv, _gv2, lop, _mc = _seed(db)
    cu = User(vai_tro=VaiTro.hs, ho_ten="HS Cũ", dang_nhap="hscu2",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(cu)
    db.commit()

    ma = _tao_ma(client, lop.id)
    r = client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "Mới", "dang_nhap": "hsmoi2", "mat_khau": "matkhau123"})
    assert r.status_code == 400
    assert "đủ sĩ số" in r.json()["detail"]


# ---------- Throttle ----------

def test_throttle_chi_dem_lan_nhap_SAI_ma(db, client):
    """Cả lớp đăng ký cùng lúc qua CÙNG một IP (NAT trường) không được bị khóa oan —
    chỉ lần nhập SAI mới tính."""
    _gv, _gv2, lop, _mc = _seed(db)
    ma = _tao_ma(client, lop.id)

    # Nhập ĐÚNG nhiều lần: không bao giờ bị chặn
    for _ in range(SO_LAN_SAI_MA_TOI_DA + 5):
        assert client.get(f"/api/auth/lop-tu-ma?ma={ma}").status_code == 200

    # Nhập SAI quá ngưỡng → 429
    for _ in range(SO_LAN_SAI_MA_TOI_DA):
        client.get("/api/auth/lop-tu-ma?ma=ZZZZ-ZZZZ")
    r = client.get("/api/auth/lop-tu-ma?ma=ZZZZ-ZZZZ")
    assert r.status_code == 429

    # Và chặn luôn cả đăng ký (cùng bộ đếm) dù mã đúng
    assert client.post("/api/auth/dang-ky", json={
        "ma": ma, "ho_ten": "A", "dang_nhap": "bichan", "mat_khau": "matkhau123",
    }).status_code == 429
