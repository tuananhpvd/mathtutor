"""Test tích hợp API luồng TLN (Phase 2)."""

import json

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def seed_all(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()

    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Test", dang_nhap="hs_test",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Test", dang_nhap="gv_test",
              mat_khau_hash=hash_password("pass"))
    admin = User(vai_tro=VaiTro.admin, ho_ten="Admin", dang_nhap="admin_test",
                 mat_khau_hash=hash_password("pass"))
    db.add_all([hs, gv, admin])
    db.flush()

    # Bài TLN đã duyệt
    p = Problem(
        chuyen_de="Test", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet,
        meta={"dap_an_cuoi": "5"},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(
        problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
        mo_ta="test", bieu_thuc_ket_qua="5",
        danh_sach_goi_y=["gợi 1", "gợi 2"],
    ))
    db.commit()
    return hs, gv, admin, p


def _token(client, dang_nhap, mat_khau="pass"):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": mat_khau})
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_luong_tln(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")

    # Tạo phiên
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    assert r.json()["loai_cau"] == "TLN"
    assert r.json()["van_ban"]  # lời mở đầu không rỗng

    # Gửi tin sai
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"},
                    headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["y_dinh"] == "hoi_nguoc"
    assert r.json()["da_xong"] is False

    # Gửi tin đúng
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "x=5", "dap_an_nhap": "5"},
                    headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["da_xong"] is True
    assert r.json()["y_dinh"] == "ket_thuc"


def _seed_tn4pa(db, bat_buoc: bool):
    p = Problem(
        chuyen_de="Test", loai_cau="TN4PA", do_kho="de",
        de_bai="Hàm số đồng biến trên khoảng nào?", loai_dap_an_nhap="chon_phuong_an",
        trang_thai_duyet=TrangThaiDuyet.da_duyet,
        meta={"phuong_an": {"A": "1", "B": "2", "C": "3", "D": "4"},
              "dap_an_dung": "B", "bat_buoc_suy_luan": bat_buoc},
    )
    db.add(p)
    db.flush()
    db.add(SolutionStep(
        problem_id=p.id, thu_tu=1, pham_vi="ca_bai",
        mo_ta="Tính y' và xét dấu", bieu_thuc_ket_qua="4*x - 4",
        danh_sach_goi_y=["gợi 1", "gợi 2"],
    ))
    db.commit()
    return p


def test_tn4pa_bat_buoc_suy_luan_hai_pha(client, db):
    seed_all(db)
    p = _seed_tn4pa(db, bat_buoc=True)
    tok = _token(client, "hs_test")

    # Tạo phiên: chưa mở khóa chọn đáp án, có mô tả bước
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    assert r.json()["cho_chon_dap_an"] is False
    assert r.json()["buoc_mo_ta"] == "Tính y' và xét dấu"

    # Bấm chọn đáp án ngay → bị chặn, vẫn chưa mở khóa
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["cho_chon_dap_an"] is False
    assert r.json()["da_xong"] is False

    # Nhập biểu thức bước đúng → mở khóa chọn đáp án
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "y'=4x-4", "dap_an_nhap": "4*x-4"}, headers=_h(tok))
    assert r.json()["y_dinh"] == "xac_nhan_dung"
    assert r.json()["cho_chon_dap_an"] is True

    # Chọn đáp án đúng → hoàn thành
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["da_xong"] is True
    assert r.json()["y_dinh"] == "ket_thuc"


def test_tn4pa_chon_ngay_hai_pha(client, db):
    seed_all(db)
    p = _seed_tn4pa(db, bat_buoc=False)
    tok = _token(client, "hs_test")

    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    sid = r.json()["session_id"]
    assert r.json()["cho_chon_dap_an"] is True  # mở ngay

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "", "dap_an_nhap": "B"}, headers=_h(tok))
    assert r.json()["da_xong"] is True


def test_get_problems_hs_khong_co_dap_an(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")

    r = client.get(f"/api/problems/{p.id}", headers=_h(tok))
    assert r.status_code == 200
    data = r.json()
    # Không được chứa trường đáp án
    assert "dap_an_cuoi" not in json.dumps(data)
    assert "dap_an_dung" not in json.dumps(data)


def test_admin_endpoint_chặn_hs(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    r = client.get("/api/admin/ping", headers=_h(tok))
    assert r.status_code == 403


def test_admin_endpoint_chặn_gv(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "gv_test")
    r = client.get("/api/admin/ping", headers=_h(tok))
    assert r.status_code == 403
