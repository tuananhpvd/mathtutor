"""Test API: HS chat tự do với gia sư (câu hỏi/bối rối, không kèm đáp án), het_goi_y,
so_goi_y_toi_da, tong_so_lan_sai/diem_qua_trinh và cờ 'đã xem hướng dẫn phòng học'."""

from app.auth.security import hash_password
from app.models.lop import Lop
from app.models.problem import Problem, TrangThaiDuyet
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro


def seed(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Chat", dang_nhap="hs_chat",
              mat_khau_hash=hash_password("pass"), lop_id=lop.id)
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Chat", dang_nhap="gv_chat",
              mat_khau_hash=hash_password("pass"))
    db.add_all([hs, gv])
    db.flush()
    lop.gv_id = gv.id

    p = Problem(
        chuyen_de="Test", loai_cau="TLN", do_kho="tb",
        de_bai="Tìm x.", loai_dap_an_nhap="gia_tri",
        trang_thai_duyet=TrangThaiDuyet.da_duyet,
        nguoi_tao_id=gv.id,
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
    return hs, gv, p


def _token(client, dang_nhap, mat_khau="pass"):
    r = client.post("/api/auth/login", json={"dang_nhap": dang_nhap, "mat_khau": mat_khau})
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_hs_hoi_tu_do_qua_api_khong_tinh_la_dinh_huong(client, db):
    hs, gv, p = seed(db)
    tok = _token(client, "hs_chat")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok)).json()["session_id"]

    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "vì sao lại làm như vậy ạ?"},
                    headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["y_dinh"] == "giai_thich_ngan"
    assert r.json()["da_xong"] is False
    assert r.json()["cap_goi_y"] == 0  # không tốn lượt gợi ý


def test_so_goi_y_toi_da_co_trong_response(client, db):
    hs, gv, p = seed(db)
    tok = _token(client, "hs_chat")
    r = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok))
    assert r.json()["so_goi_y_toi_da"] == 2  # bước 1 có 2 gợi ý

    sid = r.json()["session_id"]
    r2 = client.post(f"/api/sessions/{sid}/message",
                     json={"noi_dung": "", "yeu_cau_goi_y": True}, headers=_h(tok))
    assert r2.json()["so_goi_y_toi_da"] == 2


def test_het_goi_y_qua_api(client, db):
    hs, gv, p = seed(db)
    tok = _token(client, "hs_chat")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok)).json()["session_id"]

    # Bước 1 có 2 gợi ý — xin lần 1 hợp lệ, lần 2 đã max, lần 3 phải báo hết
    r1 = client.post(f"/api/sessions/{sid}/message",
                     json={"noi_dung": "", "yeu_cau_goi_y": True}, headers=_h(tok))
    assert r1.json()["y_dinh"] == "goi_y"
    r2 = client.post(f"/api/sessions/{sid}/message",
                     json={"noi_dung": "", "yeu_cau_goi_y": True}, headers=_h(tok))
    r3 = client.post(f"/api/sessions/{sid}/message",
                     json={"noi_dung": "", "yeu_cau_goi_y": True}, headers=_h(tok))
    assert r3.json()["y_dinh"] == "het_goi_y"
    assert r3.json()["cap_goi_y"] == r2.json()["cap_goi_y"]  # không vượt max


def test_tong_so_lan_sai_va_diem_qua_trinh_sau_hoan_thanh(client, db):
    hs, gv, p = seed(db)
    tok_hs = _token(client, "hs_chat")
    tok_gv = _token(client, "gv_chat")
    sid = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(tok_hs)).json()["session_id"]

    # Sai 1 lần rồi đúng
    client.post(f"/api/sessions/{sid}/message",
               json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"}, headers=_h(tok_hs))
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "x=5", "dap_an_nhap": "5"}, headers=_h(tok_hs))
    assert r.json()["da_xong"] is True
    assert r.json()["tong_so_lan_sai"] == 1

    # Xem lại: HS không thấy diem_qua_trinh, GV thấy
    tk_hs = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(tok_hs)).json()["thong_ke"]
    assert tk_hs["tong_so_lan_sai"] == 1
    assert tk_hs["diem_qua_trinh"] is None

    tk_gv = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(tok_gv)).json()["thong_ke"]
    assert tk_gv["diem_qua_trinh"] is not None
    assert 0 <= tk_gv["diem_qua_trinh"] <= 1


def test_da_xem_huong_dan_phong_hoc(client, db):
    hs, gv, p = seed(db)
    tok = _token(client, "hs_chat")

    r0 = client.get("/api/hs/ho-so", headers=_h(tok))
    assert r0.json()["da_xem_huong_dan_phong_hoc"] is False

    r1 = client.post("/api/hs/da-xem-huong-dan-phong-hoc", headers=_h(tok))
    assert r1.status_code == 200

    r2 = client.get("/api/hs/ho-so", headers=_h(tok))
    assert r2.json()["da_xem_huong_dan_phong_hoc"] is True
