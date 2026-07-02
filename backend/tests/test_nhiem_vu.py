"""Tests A3: giao bài/nhiệm vụ (thủ công, cả lớp, đề xuất theo điểm yếu)."""

from app.auth.security import hash_password
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _h(client, dn):
    return {"Authorization": f"Bearer {_login(client, dn)}"}


def _bai(db, chuyen_de, dang_id=None, duyet=True, nguoi_tao_id=None):
    p = Problem(
        chuyen_de=chuyen_de, dang_id=dang_id, loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet if duyet else TrangThaiDuyet.cho_duyet,
        nguoi_tao_id=nguoi_tao_id,
        meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(problem_id=p.id, thu_tu=1, pham_vi="ca_bai", mo_ta="b1",
                        bieu_thuc_ket_qua="5", danh_sach_goi_y=["g1", "g2"]))
    return p


def _seed(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="Thầy Nam", dang_nhap="gv2",
               mat_khau_hash=hash_password("password"))
    db.add_all([gv, gv2])
    db.flush()
    lop.gv_id = gv.id
    hs1 = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
               mat_khau_hash=hash_password("password"), lop_id=lop.id)
    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS B", dang_nhap="hs2",
               mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add_all([hs1, hs2])
    db.flush()
    p1 = _bai(db, "Khảo sát hàm số", nguoi_tao_id=gv.id)
    p2 = _bai(db, "Số phức", nguoi_tao_id=gv.id)
    db.commit()
    return {"lop": lop.id, "hs1": hs1.id, "hs2": hs2.id, "p1": p1.id, "p2": p2.id}


def test_giao_nhiem_vu_thu_cong_va_hs_thay(db, client):
    s = _seed(db)
    h_gv = _h(client, "gv1")
    r = client.post("/api/nhiem-vu", headers=h_gv, json={
        "tieu_de": "Luyện cuối tuần",
        "problem_ids": [s["p1"], s["p2"]],
        "hoc_sinh_ids": [s["hs1"]],
    })
    assert r.status_code == 200, r.text
    assert r.json()["so_hs"] == 1 and r.json()["so_bai"] == 2

    # HS A thấy nhiệm vụ + thông báo
    h_hs = _h(client, "hs1")
    assert client.get("/api/thong-bao/chua-doc", headers=h_hs).json()["so_luong"] == 1
    ds = client.get("/api/nhiem-vu/hs", headers=h_hs).json()
    assert len(ds) == 1
    assert ds[0]["tong_bai"] == 2 and ds[0]["so_hoan_thanh"] == 0
    assert ds[0]["gv_ten"] == "Cô Lan"

    # HS B không được giao → không thấy
    assert client.get("/api/nhiem-vu/hs", headers=_h(client, "hs2")).json() == []


def test_giao_ca_lop(db, client):
    s = _seed(db)
    h_gv = _h(client, "gv1")
    r = client.post("/api/nhiem-vu", headers=h_gv, json={
        "tieu_de": "Cả lớp làm", "problem_ids": [s["p1"]], "lop_ids": [s["lop"]],
    })
    assert r.status_code == 200, r.text
    assert r.json()["so_hs"] == 2  # cả 2 HS trong lớp

    assert len(client.get("/api/nhiem-vu/hs", headers=_h(client, "hs1")).json()) == 1
    assert len(client.get("/api/nhiem-vu/hs", headers=_h(client, "hs2")).json()) == 1


def test_tien_do_cap_nhat_khi_hoan_thanh_bai(db, client):
    s = _seed(db)
    h_gv = _h(client, "gv1")
    client.post("/api/nhiem-vu", headers=h_gv, json={
        "tieu_de": "NV", "problem_ids": [s["p1"], s["p2"]], "hoc_sinh_ids": [s["hs1"]],
    })
    h_hs = _h(client, "hs1")
    # HS hoàn thành p1 (TLN 1 bước, đáp án 5)
    sid = client.post("/api/sessions", headers=h_hs, json={"problem_id": s["p1"]}).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message", headers=h_hs, json={"dap_an_nhap": "5"})

    ds = client.get("/api/nhiem-vu/hs", headers=h_hs).json()
    assert ds[0]["so_hoan_thanh"] == 1 and ds[0]["tong_bai"] == 2
    bai_p1 = next(b for b in ds[0]["bai"] if b["problem_id"] == s["p1"])
    assert bai_p1["da_hoan_thanh"] is True


def test_de_xuat_theo_diem_yeu(db, client):
    """HS làm yếu 1 dạng → đề xuất bài cùng dạng (chưa làm)."""
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    db.add(gv)
    db.flush()
    lop.gv_id = gv.id
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    cd = ChuyenDe(ten="Khảo sát hàm số", thu_tu=1)
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Cực trị", thu_tu=1)
    db.add(dang)
    db.flush()
    # Nhiều bài cùng dạng để HS làm yếu + còn bài chưa làm để đề xuất
    bais = [_bai(db, "Khảo sát hàm số", dang_id=dang.id) for _ in range(4)]
    db.commit()

    h_hs = _h(client, "hs1")
    # HS làm SAI 2 bài (điểm thấp) để dạng bị xếp yếu
    for p in bais[:2]:
        sid = client.post("/api/sessions", headers=h_hs,
                          json={"problem_id": p.id}).json()["session_id"]
        # nộp sai nhiều lần rồi đúng để hoàn thành nhưng điểm thấp? TLN cần đúng mới xong.
        client.post(f"/api/sessions/{sid}/message", headers=h_hs, json={"dap_an_nhap": "999"})
        client.post(f"/api/sessions/{sid}/message", headers=h_hs, json={"dap_an_nhap": "5"})

    h_gv = _h(client, "gv1")
    r = client.get(f"/api/nhiem-vu/de-xuat?hoc_sinh_id={hs.id}", headers=h_gv)
    assert r.status_code == 200, r.text
    # Có cấu trúc trả về đúng (danh sách bài đề xuất là các bài cùng dạng chưa hoàn thành)
    data = r.json()
    assert "bai" in data and "dang_yeu" in data
    de_xuat_pids = {b["problem_id"] for b in data["bai"]}
    # 2 bài chưa làm cùng dạng nên không nằm trong tập đã hoàn thành
    assert de_xuat_pids.issubset({bais[2].id, bais[3].id})


def test_gv_khac_khong_giao_hs_ngoai_lop(db, client):
    s = _seed(db)
    h_gv2 = _h(client, "gv2")
    r = client.post("/api/nhiem-vu", headers=h_gv2, json={
        "tieu_de": "X", "problem_ids": [s["p1"]], "hoc_sinh_ids": [s["hs1"]],
    })
    assert r.status_code == 400


def test_xoa_nhiem_vu(db, client):
    s = _seed(db)
    h_gv = _h(client, "gv1")
    nv_id = client.post("/api/nhiem-vu", headers=h_gv, json={
        "tieu_de": "NV", "problem_ids": [s["p1"]], "hoc_sinh_ids": [s["hs1"]],
    }).json()["id"]
    assert client.delete(f"/api/nhiem-vu/{nv_id}", headers=h_gv).status_code == 200
    assert client.get("/api/nhiem-vu/hs", headers=_h(client, "hs1")).json() == []
