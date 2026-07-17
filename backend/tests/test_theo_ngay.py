"""Tests các chuỗi thống kê THEO NGÀY (30 ngày) cho biểu đồ vùng:
- /progress/me/nhip-ngay, /progress/students/{id}/nhip-ngay, /progress/lop/nhip-ngay
- /progress/lop/kho-khan-ngay
- /admin/llm-theo-ngay, /admin/phien-theo-ngay
"""

from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.flag import Flag, LoaiCo, TrangThaiCo
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import User, VaiTro
from app.models.yeu_cau_tro_giup import YeuCauTroGiup

HOM_NAY = lambda: datetime.now(timezone.utc).date().isoformat()  # noqa: E731


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _seed(db):
    lop = Lop(ten="12TN")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV TN", dang_nhap="gv_tn",
              mat_khau_hash=hash_password("password"))
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin_tn",
                 mat_khau_hash=hash_password("password"))
    db.add_all([gv, admin])
    db.flush()
    lop.gv_id = gv.id
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS TN", dang_nhap="hs_tn",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    db.flush()
    p = Problem(chuyen_de="T", loai_cau="TLN", do_kho="tb", de_bai="?",
                loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "1"})
    db.add(p)
    db.commit()
    return gv, admin, hs, p


def _phien_xong(db, hs_id, p_id, giay=120):
    s = SessionModel(hoc_sinh_id=hs_id, problem_id=p_id,
                     trang_thai=TrangThaiSession.hoan_thanh, diem=1.0, thoi_gian_giay=giay)
    db.add(s)
    db.commit()
    return s


def test_nhip_ngay_me_va_hoc_sinh_va_lop(db, client):
    gv, admin, hs, p = _seed(db)
    _phien_xong(db, hs.id, p.id, giay=120)
    _phien_xong(db, hs.id, p.id, giay=60)

    # HS tự xem: 30 phần tử, hôm nay 2 bài / 3 phút
    r = client.get("/api/progress/me/nhip-ngay", headers=_h(client, "hs_tn")).json()
    assert len(r) == 30
    assert r[-1]["ngay"] == HOM_NAY()
    assert r[-1]["so_bai"] == 2 and r[-1]["so_phut"] == 3
    assert r[0]["so_bai"] == 0  # ngày trống vẫn có mặt với 0 (chuỗi liên tục)

    # GV xem 1 HS lớp mình + xem gộp lớp — cùng số liệu
    r2 = client.get(f"/api/progress/students/{hs.id}/nhip-ngay", headers=_h(client, "gv_tn")).json()
    assert r2[-1]["so_bai"] == 2
    r3 = client.get("/api/progress/lop/nhip-ngay", headers=_h(client, "gv_tn")).json()
    assert len(r3) == 30 and r3[-1]["so_bai"] == 2

    # Phân quyền: HS không gọi được route lop; GV không gọi được route me
    assert client.get("/api/progress/lop/nhip-ngay", headers=_h(client, "hs_tn")).status_code == 403
    assert client.get("/api/progress/me/nhip-ngay", headers=_h(client, "gv_tn")).status_code == 403


def test_kho_khan_ngay_lop(db, client):
    gv, admin, hs, p = _seed(db)
    s = _phien_xong(db, hs.id, p.id)
    db.add(Flag(session_id=s.id, loai_co=LoaiCo.khong_hieu_nhieu,
                trang_thai=TrangThaiCo.cho_xu_ly, ghi_chu="t"))
    db.add(YeuCauTroGiup(hoc_sinh_id=hs.id, session_id=s.id, problem_id=p.id))
    db.add(YeuCauTroGiup(hoc_sinh_id=hs.id, session_id=s.id, problem_id=p.id))
    db.commit()

    r = client.get("/api/progress/lop/kho-khan-ngay", headers=_h(client, "gv_tn")).json()
    assert len(r) == 30
    assert r[-1] == {"ngay": HOM_NAY(), "so_co": 1, "so_nho": 2, "tong": 3}


def test_admin_llm_va_phien_theo_ngay(db, client):
    gv, admin, hs, p = _seed(db)
    _phien_xong(db, hs.id, p.id)

    from app.services.llm_quota_service import LOAI_HOI_THOAI, LOAI_SINH_CAU_HOI, ghi_luot
    ghi_luot(db, hs.id, LOAI_HOI_THOAI, 3)
    ghi_luot(db, gv.id, LOAI_SINH_CAU_HOI, 1)

    r = client.get("/api/admin/llm-theo-ngay", headers=_h(client, "admin_tn")).json()
    assert len(r) == 30
    assert r[-1]["ngay"] == HOM_NAY()
    assert r[-1]["hoi_thoai"] == 3 and r[-1]["sinh_cau_hoi"] == 1 and r[-1]["tong"] == 4

    r2 = client.get("/api/admin/phien-theo-ngay", headers=_h(client, "admin_tn")).json()
    assert len(r2) == 30
    assert r2[-1]["so_phien"] == 1

    # GV không gọi được route admin
    assert client.get("/api/admin/llm-theo-ngay", headers=_h(client, "gv_tn")).status_code == 403
