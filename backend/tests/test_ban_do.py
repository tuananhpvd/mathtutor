"""Tests C3 — bản đồ năng lực (heatmap chuyên đề × độ khó)."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.user import User, VaiTro
from app.services.phan_tich_service import ban_do_nang_luc


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "pass"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_bd",
              mat_khau_hash=hash_password("pass"))
    db.add(gv)
    db.flush()
    lop = Lop(ten="12BD", gv_id=gv.id)
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS BD", dang_nhap="hs_bd",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS BD2", dang_nhap="hs2_bd",
               mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    db.add_all([hs, hs2])
    db.flush()

    def bai(cd, dk):
        p = Problem(chuyen_de=cd, loai_cau="TLN", do_kho=dk, de_bai="?",
                    loai_dap_an_nhap="gia_tri", trang_thai_duyet=TrangThaiDuyet.da_duyet,
                    nguoi_tao_id=gv.id, meta={"dap_an_cuoi": "1"})
        db.add(p)
        db.flush()
        return p

    p_dh_de = bai("Đạo hàm", "de")
    p_dh_kho = bai("Đạo hàm", "kho")
    p_ts_tb = bai("Tích phân", "tb")
    db.commit()
    return gv, hs, hs2, p_dh_de, p_dh_kho, p_ts_tb


def _phien(db, hs_id, p_id, diem=10.0, xong=True):
    s = SessionModel(
        hoc_sinh_id=hs_id, problem_id=p_id, diem=diem if xong else None,
        trang_thai=TrangThaiSession.hoan_thanh if xong else TrangThaiSession.dang_lam,
        cap_goi_y_hien_tai=0,
    )
    db.add(s)
    db.commit()
    return s


def test_ban_do_ca_nhan(db):
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    _phien(db, hs.id, p_de.id, diem=1.0)       # Đạo hàm/dễ: hoàn thành điểm tối đa
    _phien(db, hs.id, p_kho.id, xong=False)    # Đạo hàm/khó: đang làm → ô có phiên, mastery None

    ket = ban_do_nang_luc(db, [hs.id])
    assert ket["cot"] == ["de", "tb", "kho"]
    assert len(ket["hang"]) == 1  # chỉ chuyên đề Đạo hàm (Tích phân chưa có phiên)
    hang = ket["hang"][0]
    assert hang["chuyen_de"] == "Đạo hàm"
    assert hang["o"]["de"]["diem_thanh_thao"] == 100  # điểm 1.0, hoàn thành 100%, 0 gợi ý
    assert hang["o"]["de"]["nhan"] == "manh"
    # ô khó: có phiên nhưng chưa hoàn thành → "chưa đủ dữ liệu", KHÔNG phải yếu
    assert hang["o"]["kho"]["diem_thanh_thao"] is None
    assert hang["o"]["kho"]["nhan"] == "chua_du_lieu"
    # ô tb: không có phiên nào → null
    assert hang["o"]["tb"] is None


def test_ban_do_lop_don_chung_phien(db):
    """Bản đồ lớp DỒN CHUNG phiên mọi HS vào từng ô (không trung bình của trung bình)."""
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    _phien(db, hs.id, p_tb.id, diem=1.0)
    _phien(db, hs2.id, p_tb.id, diem=0.0)

    ket = ban_do_nang_luc(db, [hs.id, hs2.id])
    o = next(h for h in ket["hang"] if h["chuyen_de"] == "Tích phân")["o"]["tb"]
    assert o["so_hoan_thanh"] == 2
    # chất lượng TB (không có diem_qua_trinh → fallback diem) = 0.5, tỉ lệ hoàn thành 1.0,
    # không cạn gợi ý lần nào → 0.75*0.5 + 0.25*1.0 = 0.625 → 62 (round-half-to-even)
    assert o["diem_thanh_thao"] == 62


def test_api_ban_do_quyen(db, client):
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    _phien(db, hs.id, p_de.id)

    # HS xem bản đồ của mình
    r = client.get("/api/progress/me/ban-do", headers=_h(_login(client, "hs_bd")))
    assert r.status_code == 200 and len(r.json()["hang"]) == 1

    # GV xem bản đồ lớp + từng HS
    h_gv = _h(_login(client, "gv_bd"))
    assert client.get("/api/progress/ban-do/lop", headers=h_gv).status_code == 200
    assert client.get(f"/api/progress/students/{hs.id}/ban-do", headers=h_gv).status_code == 200

    # GV khác không quản lý HS → 403
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_bd",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()
    r = client.get(f"/api/progress/students/{hs.id}/ban-do",
                   headers=_h(_login(client, "gv2_bd")))
    assert r.status_code == 403


def test_ban_do_lop_loc_theo_lop_id(db, client):
    """GV nhiều lớp: lop_id lọc đúng lớp đó, không trộn với lớp khác của cùng GV."""
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    lop2 = Lop(ten="12BD2", gv_id=gv.id)
    db.add(lop2)
    db.flush()
    hs3 = User(vai_tro=VaiTro.hs, ho_ten="HS BD3", dang_nhap="hs3_bd",
               mat_khau_hash=hash_password("pass"), lop_id=lop2.id)
    db.add(hs3)
    db.commit()
    _phien(db, hs.id, p_de.id)   # lớp 1 (12BD)
    _phien(db, hs3.id, p_tb.id)  # lớp 2 (12BD2)

    h_gv = _h(_login(client, "gv_bd"))
    lop1 = db.query(Lop).filter_by(ten="12BD").first()

    r = client.get(f"/api/progress/ban-do/lop?lop_id={lop1.id}", headers=h_gv)
    assert r.status_code == 200
    ten_cd = {h["chuyen_de"] for h in r.json()["hang"]}
    assert ten_cd == {"Đạo hàm"}  # chỉ dữ liệu lớp 1, không lẫn "Tích phân" của lớp 2

    r2 = client.get(f"/api/progress/ban-do/lop?lop_id={lop2.id}", headers=h_gv)
    assert r2.status_code == 200
    ten_cd2 = {h["chuyen_de"] for h in r2.json()["hang"]}
    assert ten_cd2 == {"Tích phân"}

    # Không truyền lop_id → hành vi cũ, gộp cả 2 lớp
    r3 = client.get("/api/progress/ban-do/lop", headers=h_gv)
    assert {h["chuyen_de"] for h in r3.json()["hang"]} == {"Đạo hàm", "Tích phân"}


def test_ban_do_lop_id_khong_thuoc_gv_bi_chan(db, client):
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv3_bd",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()
    lop1 = db.query(Lop).filter_by(ten="12BD").first()
    r = client.get(f"/api/progress/ban-do/lop?lop_id={lop1.id}",
                   headers=_h(_login(client, "gv3_bd")))
    assert r.status_code == 403


def test_ban_do_lop_id_khong_ton_tai(db, client):
    gv, hs, hs2, p_de, p_kho, p_tb = _seed(db)
    r = client.get("/api/progress/ban-do/lop?lop_id=999999",
                   headers=_h(_login(client, "gv_bd")))
    assert r.status_code == 404
