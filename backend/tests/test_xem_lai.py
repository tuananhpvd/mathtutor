"""Tests B3 — xem lại bài sau khi hoàn thành (lời giải chuẩn + hành trình)."""

from app.auth.security import hash_password
from app.models.session import Session as SessionModel
from app.models.session import TrangThaiSession
from app.models.solution_step import SolutionStep
from app.models.user import User, VaiTro

from .test_api_flow import _h, _token, seed_all


def _hoan_thanh_phien(client, tok, problem_id):
    """Tạo phiên TLN và hoàn thành: 1 lần sai + 1 lần đúng (đáp án chuẩn '5')."""
    sid = client.post("/api/sessions", json={"problem_id": problem_id},
                      headers=_h(tok)).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message",
                json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"}, headers=_h(tok))
    r = client.post(f"/api/sessions/{sid}/message",
                    json={"noi_dung": "x=5", "dap_an_nhap": "5"}, headers=_h(tok))
    assert r.json()["da_xong"] is True
    return sid


def test_xem_lai_sau_hoan_thanh_du_du_lieu(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    sid = _hoan_thanh_phien(client, tok, p.id)

    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    # Đáp án chuẩn TLN được trả sau hoàn thành
    assert data["dap_an"]["dap_an_cuoi"] == "5"
    # Lời giải chuẩn từng bước
    assert data["loi_giai"][0]["mo_ta"] == "test"
    assert data["loi_giai"][0]["bieu_thuc_ket_qua"] == "5"
    # Hành trình có cả lượt HS và gia sư, đúng thứ tự thời gian
    vai_tros = {t["vai_tro"] for t in data["hanh_trinh"]}
    assert "hoc_sinh" in vai_tros and "gia_su" in vai_tros
    assert data["hanh_trinh"][0]["thoi_diem"] is not None
    # Thống kê phiên
    tk = data["thong_ke"]
    assert tk["so_luot_hs"] >= 2
    assert "diem" in tk and "cap_goi_y_max" in tk
    # Đề bài đi qua lớp lọc an toàn (không mang trường đáp án trong problem)
    assert "dap_an_cuoi" not in str(data["problem"])


def test_xem_lai_loi_giai_chi_tiet_theo_cau_hinh_gv(client, db):
    """loi_giai_chi_tiet chỉ hiện trong xem-lai khi GV bật hien_loi_giai_chi_tiet; mặc định
    (chưa cấu hình) hoặc GV tắt → None, HS không thấy."""
    hs, gv, admin, p = seed_all(db)
    tok_gv = _token(client, "gv_test")
    tok_hs = _token(client, "hs_test")

    # Mặc định (chưa cấu hình): không có lời giải chi tiết trong xem-lai
    sid1 = _hoan_thanh_phien(client, tok_hs, p.id)
    data1 = client.get(f"/api/sessions/{sid1}/xem-lai", headers=_h(tok_hs)).json()
    assert data1["loi_giai_chi_tiet"] is None

    # GV bật hiển thị
    r = client.patch(f"/api/problems/{p.id}", headers=_h(tok_gv), json={
        "loi_giai_chi_tiet": "Giải chi tiết: bước 1 ... bước 2 ...",
        "hien_loi_giai_chi_tiet": True,
    })
    assert r.status_code == 200, r.text

    data2 = client.get(f"/api/sessions/{sid1}/xem-lai", headers=_h(tok_hs)).json()
    assert data2["loi_giai_chi_tiet"] == "Giải chi tiết: bước 1 ... bước 2 ..."

    # GV tắt lại → HS không còn thấy nữa
    client.patch(f"/api/problems/{p.id}", headers=_h(tok_gv),
                json={"hien_loi_giai_chi_tiet": False})
    data3 = client.get(f"/api/sessions/{sid1}/xem-lai", headers=_h(tok_hs)).json()
    assert data3["loi_giai_chi_tiet"] is None


def test_xem_lai_bieu_thuc_ket_qua_tra_ve_latex(client, db):
    """bieu_thuc_ket_qua lưu cú pháp SymPy (vd "3*x**2 - 3") — trang Xem lại phải nhận
    được LaTeX thật (vd "3 x^{2} - 3") để Formula/KaTeX hiển thị đẹp, không phải chuỗi
    SymPy thô (từng hiện lỗi kiểu "3∗x∗∗2−3" khi KaTeX cố parse cú pháp SymPy).

    Chốt trạng thái hoàn thành thẳng qua DB (thay vì hội thoại) để tách biệt khỏi logic
    orchestrator — test này chỉ quan tâm bước chuyển đổi LaTeX ở response, không phải
    luồng hoàn thành phiên (đã có test riêng khóa hành vi đó)."""
    hs, gv, admin, p = seed_all(db)
    step = db.query(SolutionStep).filter(SolutionStep.problem_id == p.id).first()
    step.bieu_thuc_ket_qua = "3*x**2 - 3"
    tok = _token(client, "hs_test")
    sid = client.post("/api/sessions", json={"problem_id": p.id},
                      headers=_h(tok)).json()["session_id"]
    session = db.get(SessionModel, sid)
    session.trang_thai = TrangThaiSession.hoan_thanh
    db.commit()

    data = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(tok)).json()
    assert data["loi_giai"][0]["bieu_thuc_ket_qua"] == "3 x^{2} - 3"
    assert "**" not in data["loi_giai"][0]["bieu_thuc_ket_qua"]


def test_xem_lai_phien_chua_xong_bi_chan_403(client, db):
    """KHÓA HÀNH VI: phiên đang làm → 403, đáp án KHÔNG lộ lúc đang học."""
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    sid = client.post("/api/sessions", json={"problem_id": p.id},
                      headers=_h(tok)).json()["session_id"]
    client.post(f"/api/sessions/{sid}/message",
                json={"noi_dung": "em nghĩ x=3", "dap_an_nhap": "3"}, headers=_h(tok))

    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(tok))
    assert r.status_code == 403
    assert "5" not in r.text  # đáp án chuẩn không xuất hiện trong phản hồi


def test_xem_lai_phien_cua_hs_khac_404(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    sid = _hoan_thanh_phien(client, tok, p.id)

    hs2 = User(vai_tro=VaiTro.hs, ho_ten="HS Khác", dang_nhap="hs_khac",
               mat_khau_hash=hash_password("pass"))
    db.add(hs2)
    db.commit()
    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(_token(client, "hs_khac")))
    assert r.status_code == 404


def test_xem_lai_gv_va_admin(client, db):
    hs, gv, admin, p = seed_all(db)
    tok = _token(client, "hs_test")
    sid = _hoan_thanh_phien(client, tok, p.id)

    # GV chủ nhiệm lớp HS → xem được
    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(_token(client, "gv_test")))
    assert r.status_code == 200

    # GV khác (không quản lý HS này) → 403
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV Khác", dang_nhap="gv_khac",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()
    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(_token(client, "gv_khac")))
    assert r.status_code == 403

    # Admin → xem được
    r = client.get(f"/api/sessions/{sid}/xem-lai", headers=_h(_token(client, "admin_test")))
    assert r.status_code == 200
