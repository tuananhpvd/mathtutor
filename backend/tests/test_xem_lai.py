"""Tests B3 — xem lại bài sau khi hoàn thành (lời giải chuẩn + hành trình)."""

from app.auth.security import hash_password
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
