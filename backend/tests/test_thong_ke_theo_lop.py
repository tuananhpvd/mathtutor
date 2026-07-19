"""Thống kê GV tính theo ĐƠN VỊ LỚP (không gộp mọi lớp của GV).

Gộp nhiều lớp làm chìm khác biệt giữa các lớp và để lớp đông lấn át lớp nhỏ. Bộ test này
chốt: (a) các endpoint thống kê lọc đúng theo `lop_id`, (b) GV không xem được lớp người khác,
(c) 3 số đếm ở Tổng quan CỐ Ý vẫn gộp theo yêu cầu nghiệp vụ, (d) thẻ "tốn nhiều thời gian"
là TRUNG BÌNH MỖI LƯỢT kèm số lượt (không phải tổng), (e) digest nhắc GV tách theo lớp.
"""

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.thong_bao import ThongBao
from app.models.user import User, VaiTro
from app.services.phan_tich_service import day_nhac_diem_yeu_tuan


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _dang(db):
    cd = ChuyenDe(ten="Khảo sát hàm số", thu_tu=1)
    db.add(cd)
    db.flush()
    d = Dang(chuyen_de_id=cd.id, ten="Tìm cực trị", thu_tu=1)
    db.add(d)
    db.flush()
    return d


def _bai(db, dang_id, nguoi_tao_id):
    p = Problem(
        chuyen_de="Khảo sát hàm số", dang_id=dang_id, loai_cau="TNDS", do_kho="tb",
        de_bai="Xét tính đúng/sai.", loai_dap_an_nhap="dung_sai_4y",
        trang_thai_duyet=TrangThaiDuyet.da_duyet, nguoi_tao_id=nguoi_tao_id,
        meta={"y": [{"ky_hieu": k, "noi_dung_y": k, "dap_an": "Dung"} for k in "abcd"]},
    )
    db.add(p)
    db.flush()
    return p


def _phien(db, hs_id, problem_id, diem=0.1, giay=120):
    db.add(SessionModel(
        hoc_sinh_id=hs_id, problem_id=problem_id,
        trang_thai=TrangThaiSession.hoan_thanh, diem=diem, thoi_gian_giay=giay,
    ))


def _seed_2_lop(db):
    """gv1 phụ trách 2 lớp (A: hsA, B: hsB); gv2 là GV khác (để thử vượt quyền)."""
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV 1", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV 2", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv, gv2])
    db.flush()
    lopA = Lop(ten="12A", gv_id=gv.id)
    lopB = Lop(ten="12B", gv_id=gv.id)
    db.add_all([lopA, lopB])
    db.flush()
    hsA = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hsa",
               mat_khau_hash=hash_password("password"), lop_id=lopA.id)
    hsB = User(vai_tro=VaiTro.hs, ho_ten="HS B", dang_nhap="hsb",
               mat_khau_hash=hash_password("password"), lop_id=lopB.id)
    db.add_all([hsA, hsB])
    db.flush()
    return gv, gv2, lopA, lopB, hsA, hsB


def test_tien_do_hoc_sinh_loc_dung_theo_lop(db, client):
    gv, _gv2, lopA, lopB, hsA, hsB = _seed_2_lop(db)
    db.commit()
    h = _h(client, "gv1")

    ds_a = client.get(f"/api/progress/students?lop_id={lopA.id}", headers=h).json()
    assert [r["ho_ten"] for r in ds_a] == ["HS A"]

    ds_b = client.get(f"/api/progress/students?lop_id={lopB.id}", headers=h).json()
    assert [r["ho_ten"] for r in ds_b] == ["HS B"]

    # Không truyền lop_id → vẫn gộp (dùng cho các chỗ cố ý gộp)
    ds_all = client.get("/api/progress/students", headers=h).json()
    assert {r["ho_ten"] for r in ds_all} == {"HS A", "HS B"}


def test_gv_khong_xem_duoc_thong_ke_lop_nguoi_khac(db, client):
    _gv, _gv2, lopA, _lopB, _hsA, _hsB = _seed_2_lop(db)
    db.commit()
    h2 = _h(client, "gv2")
    for url in (
        f"/api/progress/students?lop_id={lopA.id}",
        f"/api/progress/lop/tong-hop?lop_id={lopA.id}",
        f"/api/progress/lop/nhip-ngay?lop_id={lopA.id}",
        f"/api/progress/hieu-qua/lop?lop_id={lopA.id}",
        f"/api/gv/tong-quan?lop_id={lopA.id}",
    ):
        assert client.get(url, headers=h2).status_code == 403, url


def test_tong_hop_lop_tach_theo_lop_va_co_co_du_mau(db, client):
    gv, _gv2, lopA, lopB, hsA, _hsB = _seed_2_lop(db)
    d = _dang(db)
    for _ in range(2):  # HS lớp A yếu
        _phien(db, hsA.id, _bai(db, d.id, gv.id).id)
    db.commit()
    h = _h(client, "gv1")

    a = client.get(f"/api/progress/lop/tong-hop?lop_id={lopA.id}", headers=h).json()
    assert a["so_hoc_sinh"] == 1
    assert [x["ho_ten"] for x in a["hoc_sinh_can_chu_y"]] == ["HS A"]
    # 1 HS có dữ liệu < ngưỡng → FE phải hiện "chưa đủ dữ liệu", không vẽ xếp hạng
    assert a["du_mau"] is False and a["nguong_mau"] >= 2

    b = client.get(f"/api/progress/lop/tong-hop?lop_id={lopB.id}", headers=h).json()
    assert b["so_hoc_sinh"] == 1 and b["hoc_sinh_can_chu_y"] == []


def test_so_sanh_cac_lop_moi_lop_mot_dong(db, client):
    gv, _gv2, lopA, lopB, hsA, _hsB = _seed_2_lop(db)
    d = _dang(db)
    for _ in range(2):
        _phien(db, hsA.id, _bai(db, d.id, gv.id).id)
    db.commit()

    rows = client.get("/api/progress/lop/so-sanh", headers=_h(client, "gv1")).json()
    assert [r["lop_ten"] for r in rows] == ["12A", "12B"]
    theo_ten = {r["lop_ten"]: r for r in rows}
    assert theo_ten["12A"]["so_hoc_sinh_can_chu_y"] == 1
    assert theo_ten["12B"]["so_hoc_sinh_can_chu_y"] == 0
    assert all("du_mau" in r for r in rows)


def test_tong_quan_3_so_dem_van_gop_moi_lop(db, client):
    """Yêu cầu nghiệp vụ: sĩ số HS / HS bị khóa / cờ theo dõi CỐ Ý gộp mọi lớp, kể cả khi
    đang xem theo 1 lớp."""
    gv, _gv2, lopA, _lopB, _hsA, _hsB = _seed_2_lop(db)
    db.commit()
    h = _h(client, "gv1")

    gop = client.get("/api/gv/tong-quan", headers=h).json()
    theo_lop = client.get(f"/api/gv/tong-quan?lop_id={lopA.id}", headers=h).json()
    assert gop["tong_hoc_sinh"] == 2
    assert theo_lop["tong_hoc_sinh"] == 2      # KHÔNG tụt về 1 dù lọc theo lớp A
    assert theo_lop["hoc_sinh_khoa"] == gop["hoc_sinh_khoa"]
    assert theo_lop["tong_co"] == gop["tong_co"]


def test_the_thoi_gian_la_trung_binh_moi_luot_kem_so_luot(db, client):
    """Trước đây cộng dồn TỔNG thời gian → dạng được giao NHIỀU nhất luôn đứng đầu. Nay là
    trung bình mỗi lượt, và nhóm dưới ngưỡng số lượt không được xếp hạng."""
    gv, _gv2, lopA, _lopB, hsA, _hsB = _seed_2_lop(db)
    d = _dang(db)
    for _ in range(6):  # >= NGUONG_LUOT_TOI_THIEU (5) để được xếp hạng
        _phien(db, hsA.id, _bai(db, d.id, gv.id).id, diem=1.0, giay=100)
    db.commit()

    tq = client.get(f"/api/gv/tong-quan?lop_id={lopA.id}", headers=_h(client, "gv1")).json()
    assert tq["dang_mat_thoi_gian"], "phải có nhóm đủ mẫu để xếp hạng"
    r = tq["dang_mat_thoi_gian"][0]
    assert r["so_luot"] == 6
    assert r["thoi_gian_tb_giay"] == 100        # TRUNG BÌNH, không phải tổng 600
    assert "thoi_gian_giay" not in r            # trường tổng cũ đã bỏ


def test_the_thoi_gian_bo_qua_nhom_mau_nho(db, client):
    gv, _gv2, lopA, _lopB, hsA, _hsB = _seed_2_lop(db)
    d = _dang(db)
    for _ in range(2):  # dưới ngưỡng → không xếp hạng
        _phien(db, hsA.id, _bai(db, d.id, gv.id).id, diem=1.0, giay=900)
    db.commit()

    tq = client.get(f"/api/gv/tong-quan?lop_id={lopA.id}", headers=_h(client, "gv1")).json()
    assert tq["dang_mat_thoi_gian"] == []


def test_digest_nhac_gv_tach_theo_tung_lop(db):
    """Mỗi lớp một thông báo riêng (kèm tên lớp + lien_ket_id=lop_id) — gộp thì GV không biết
    em nào thuộc lớp nào."""
    gv, _gv2, lopA, lopB, hsA, hsB = _seed_2_lop(db)
    d = _dang(db)
    for hs in (hsA, hsB):
        for _ in range(2):
            _phien(db, hs.id, _bai(db, d.id, gv.id).id)
    db.commit()

    ket = day_nhac_diem_yeu_tuan(db)
    assert ket["da_gui"] == 2

    tbs = (db.query(ThongBao)
           .filter(ThongBao.nguoi_nhan_id == gv.id, ThongBao.lien_ket_loai == "tien_bo")
           .all())
    assert len(tbs) == 2
    assert {t.lien_ket_id for t in tbs} == {lopA.id, lopB.id}
    theo_lop = {t.lien_ket_id: t for t in tbs}
    assert "12A" in theo_lop[lopA.id].tieu_de and "HS A" in theo_lop[lopA.id].noi_dung
    assert "HS B" not in theo_lop[lopA.id].noi_dung   # không lẫn HS lớp khác

    # Dedup theo TỪNG lớp: chạy lại trong tuần không gửi thêm
    assert day_nhac_diem_yeu_tuan(db)["da_gui"] == 0
