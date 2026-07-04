"""Tests C2 — số liệu chứng minh hiệu quả phương pháp (tất định, không LLM)."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.turn import Turn, VaiTroTurn
from app.models.user import User, VaiTro
from app.services.hieu_qua_service import (
    _phan_bo,
    _xu_huong_tu_muc,
    csv_hieu_qua_lop,
    hieu_qua_hs,
    hieu_qua_lop,
)


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_hq",
              mat_khau_hash=hash_password("pass"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_hq",
               mat_khau_hash=hash_password("pass"))
    db.add_all([gv, gv2])
    db.flush()
    lop = Lop(ten="12HQ", gv_id=gv.id)
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS HQ", dang_nhap="hs_hq",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add(hs)
    db.flush()
    p = Problem(chuyen_de="T", loai_cau="TLN", do_kho="tb", de_bai="?",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "1"})
    db.add(p)
    db.commit()
    return gv, gv2, hs, p


def _phien(db, hs_id, p_id, muc_goi_y, trang_thai=TrangThaiSession.hoan_thanh, diem=10.0):
    """Tạo 1 phiên + 2 turn, turn gia sư mang cap_goi_y = muc_goi_y."""
    s = SessionModel(hoc_sinh_id=hs_id, problem_id=p_id, trang_thai=trang_thai, diem=diem)
    db.add(s)
    db.flush()
    db.add_all([
        Turn(session_id=s.id, vai_tro=VaiTroTurn.hoc_sinh, noi_dung="x", cap_goi_y=0),
        Turn(session_id=s.id, vai_tro=VaiTroTurn.gia_su, noi_dung="y", cap_goi_y=muc_goi_y),
    ])
    db.commit()
    return s


# ---------- Hàm thuần ----------

def test_phan_bo_goi_y():
    pb = _phan_bo([0, 0, 1, 2, 3, 4])
    assert pb["muc_0"] == 2 and pb["muc_1"] == 1
    assert pb["muc_2"] == 1 and pb["muc_3_plus"] == 2
    assert pb["tong"] == 6
    assert pb["ty_le_tu_lam"] == 33   # 2/6
    assert pb["ty_le_muc_toi_da_1"] == 50  # 3/6
    # rỗng → không chia 0
    assert _phan_bo([])["ty_le_tu_lam"] is None


def test_xu_huong_giam_tang_thieu_du_lieu():
    # 5 bài đầu toàn mức 2, 5 bài cuối toàn mức 0 → giảm (tiến bộ)
    xh = _xu_huong_tu_muc([2, 2, 2, 2, 2, 0, 0, 0, 0, 0])
    assert xh["du_du_lieu"] and xh["xu_huong"] == "giam"
    assert xh["dau"] == 2.0 and xh["gan_nhat"] == 0.0
    # ngược lại → tăng
    assert _xu_huong_tu_muc([0] * 5 + [2] * 5)["xu_huong"] == "tang"
    # chênh trong ±0.2 → ổn định
    assert _xu_huong_tu_muc([1, 1, 1, 1, 1] * 2)["xu_huong"] == "on_dinh"
    # < 10 bài → chưa đủ dữ liệu
    assert _xu_huong_tu_muc([1, 2, 3])["du_du_lieu"] is False


# ---------- Service với DB ----------

def test_hieu_qua_hs_tinh_dung(db):
    gv, gv2, hs, p = _seed(db)
    _phien(db, hs.id, p.id, muc_goi_y=0)
    _phien(db, hs.id, p.id, muc_goi_y=2)
    _phien(db, hs.id, p.id, muc_goi_y=1)
    # phiên đang làm + phiên ẩn KHÔNG được tính
    _phien(db, hs.id, p.id, muc_goi_y=3, trang_thai=TrangThaiSession.dang_lam)
    s_an = _phien(db, hs.id, p.id, muc_goi_y=3)
    s_an.bi_an = True
    db.commit()

    ket = hieu_qua_hs(db, hs.id)
    pb = ket["phan_bo_goi_y"]
    assert pb["tong"] == 3
    assert pb["muc_0"] == 1 and pb["muc_1"] == 1 and pb["muc_2"] == 1
    assert ket["xu_huong_goi_y"]["du_du_lieu"] is False  # mới 3 bài
    assert len(ket["theo_tuan"]) == 8
    assert ket["theo_tuan"][-1]["so_bai"] == 3  # tuần hiện tại


def test_hieu_qua_lop_va_csv(db):
    gv, gv2, hs, p = _seed(db)
    for muc in [0, 0, 1]:
        _phien(db, hs.id, p.id, muc_goi_y=muc)

    ket = hieu_qua_lop(db, gv.id)
    assert ket["so_hoc_sinh"] == 1
    assert ket["phan_bo_goi_y"]["tong"] == 3
    assert ket["hoc_sinhs"][0]["ho_ten"] == "HS HQ"
    assert ket["hoc_sinhs"][0]["ty_le_tu_lam"] == 67

    # GV khác không có lớp → rỗng, không lộ HS của GV1
    ket2 = hieu_qua_lop(db, gv2.id)
    assert ket2["so_hoc_sinh"] == 0 and ket2["hoc_sinhs"] == []

    csv = csv_hieu_qua_lop(db, gv.id)
    assert csv.splitlines()[0].startswith("Họ tên,Lớp,Số bài")
    assert '"HS HQ"' in csv


def test_api_hieu_qua_quyen(db, client):
    gv, gv2, hs, p = _seed(db)
    _phien(db, hs.id, p.id, muc_goi_y=0)

    # GV chủ lớp xem được cấp lớp + từng HS
    h_gv = _h(_login(client, "gv_hq"))
    r = client.get("/api/progress/hieu-qua/lop", headers=h_gv)
    assert r.status_code == 200 and r.json()["so_hoc_sinh"] == 1
    r = client.get(f"/api/progress/students/{hs.id}/hieu-qua", headers=h_gv)
    assert r.status_code == 200

    # GV khác bị chặn xem từng HS
    r = client.get(f"/api/progress/students/{hs.id}/hieu-qua", headers=_h(_login(client, "gv2_hq")))
    assert r.status_code == 403

    # HS không gọi được endpoint GV
    r = client.get("/api/progress/hieu-qua/lop", headers=_h(_login(client, "hs_hq")))
    assert r.status_code == 403

    # CSV: đúng content-type, có BOM để Excel mở tiếng Việt
    r = client.get("/api/progress/hieu-qua/lop/csv", headers=h_gv)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert r.text.startswith("﻿")
