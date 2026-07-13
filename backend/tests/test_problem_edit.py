"""Test API GV sửa/xóa câu hỏi + duyệt."""

from app.auth.security import hash_password
from app.models.problem import TrangThaiDuyet
from tests.test_api_flow import _h, _token, seed_all


def test_gv_xem_chi_tiet_co_solution_steps(client, db):
    _, gv, _, p = seed_all(db)
    tok = _token(client, "gv_test")
    r = client.get(f"/api/problems/{p.id}", headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["do_kho"] == "tb"
    assert data["meta"]["dap_an_cuoi"] == "5"
    assert len(data["solution_steps"]) == 1
    assert data["solution_steps"][0]["danh_sach_goi_y"] == ["gợi 1", "gợi 2"]


def test_gv_sua_de_bai_mucdo_buoc(client, db):
    _, gv, _, p = seed_all(db)
    tok = _token(client, "gv_test")
    body = {
        "de_bai": "Đề mới $x^2$.",
        "do_kho": "kho",
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "b1",
             "bieu_thuc_ket_qua": "2", "danh_sach_goi_y": ["g mới"]},
        ],
    }
    r = client.patch(f"/api/problems/{p.id}", json=body, headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["de_bai"] == "Đề mới $x^2$."
    assert data["do_kho"] == "kho"
    assert len(data["solution_steps"]) == 1
    assert data["solution_steps"][0]["danh_sach_goi_y"] == ["g mới"]


def test_gv_sua_loi_giai_chi_tiet(client, db):
    _, gv, _, p = seed_all(db)
    tok = _token(client, "gv_test")
    body = {"loi_giai_chi_tiet": "Bước 1: ... Bước 2: ...", "hien_loi_giai_chi_tiet": True}
    r = client.patch(f"/api/problems/{p.id}", json=body, headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["loi_giai_chi_tiet"] == "Bước 1: ... Bước 2: ..."
    assert data["hien_loi_giai_chi_tiet"] is True

    # GV xem lại — vẫn còn nguyên (không bị mất khi PATCH các trường khác không đụng tới)
    r = client.patch(f"/api/problems/{p.id}", json={"do_kho": "kho"}, headers=_h(tok))
    assert r.json()["loi_giai_chi_tiet"] == "Bước 1: ... Bước 2: ..."
    assert r.json()["hien_loi_giai_chi_tiet"] is True


def test_hs_khong_thay_loi_giai_chi_tiet_qua_danh_sach_bai(client, db):
    """loi_giai_chi_tiet KHÔNG được lộ qua _strip_answers (dùng lúc ĐANG học) — chỉ lộ qua
    xem-lai SAU KHI hoàn thành, và chỉ khi GV bật hien_loi_giai_chi_tiet (xem test_xem_lai.py)."""
    hs, gv, _, p = seed_all(db)
    tok_gv = _token(client, "gv_test")
    client.patch(f"/api/problems/{p.id}", json={
        "loi_giai_chi_tiet": "đáp án bí mật", "hien_loi_giai_chi_tiet": True,
    }, headers=_h(tok_gv))

    tok_hs = _token(client, "hs_test")
    r = client.get(f"/api/problems/{p.id}", headers=_h(tok_hs))
    assert r.status_code == 200
    assert "loi_giai_chi_tiet" not in r.json()
    assert "đáp án bí mật" not in r.text

    r = client.get("/api/problems", headers=_h(tok_hs))
    assert "đáp án bí mật" not in r.text


def test_hs_khong_duoc_sua(client, db):
    hs, _, _, p = seed_all(db)
    tok = _token(client, "hs_test")
    r = client.patch(f"/api/problems/{p.id}", json={"do_kho": "de"}, headers=_h(tok))
    assert r.status_code == 403


def test_gv_duyet_va_xoa(client, db):
    _, gv, _, p = seed_all(db)
    tok = _token(client, "gv_test")
    # đặt về chờ duyệt rồi duyệt
    client.patch(f"/api/problems/{p.id}", json={"trang_thai_duyet": "cho_duyet"}, headers=_h(tok))
    r = client.post(f"/api/questions-ai/{p.id}/duyet", json={"hanh_dong": "duyet"}, headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["trang_thai_duyet"] == TrangThaiDuyet.da_duyet.value
    # xóa
    r = client.delete(f"/api/problems/{p.id}", headers=_h(tok))
    assert r.status_code == 200, r.text
    assert client.get(f"/api/problems/{p.id}", headers=_h(tok)).status_code == 404


def test_gv_tao_cau_hoi_tn4pa(client, db):
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    body = {
        "loai_cau": "TN4PA", "do_kho": "de", "de_bai": "Chọn đáp án đúng $x^2$.",
        "chuyen_de": "Khảo sát hàm số",
        "meta": {
            "phuong_an": {"A": "$1$", "B": "$2$", "C": "$3$", "D": "$4$"},
            "dap_an_dung": "B", "bat_buoc_suy_luan": True,
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "b1",
             "bieu_thuc_ket_qua": "2*x", "danh_sach_goi_y": ["gợi ý 1"]},
        ],
        "loi_giai_chi_tiet": "Lời giải đầy đủ: ...",
        "hien_loi_giai_chi_tiet": True,
    }
    r = client.post("/api/problems", json=body, headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["loai_cau"] == "TN4PA"
    assert data["loai_dap_an_nhap"] == "chon_phuong_an"
    # GV tạo → da_duyet ngay
    assert data["trang_thai_duyet"] == TrangThaiDuyet.da_duyet.value
    assert data["meta"]["dap_an_dung"] == "B"
    assert data["loi_giai_chi_tiet"] == "Lời giải đầy đủ: ..."
    assert data["hien_loi_giai_chi_tiet"] is True
    # HS lớp do gv_test chủ nhiệm → thấy được bài đã duyệt của GV mình (không lộ đáp án)
    htok = _token(client, "hs_test")
    r_hs = client.get(f"/api/problems/{data['id']}", headers=_h(htok))
    assert r_hs.status_code == 200
    assert "dap_an_dung" not in r_hs.json().get("meta", {})


def test_gv_tao_cau_hoi_tnds_va_tln(client, db):
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    tnds = {
        "loai_cau": "TNDS", "do_kho": "tb", "de_bai": "Xét đúng/sai.",
        "chuyen_de": "Khảo sát hàm số",
        "meta": {"y": [
            {"ky_hieu": k, "noi_dung_y": f"ý {k}", "dap_an": "Dung"}
            for k in ["a", "b", "c", "d"]
        ]},
    }
    r = client.post("/api/problems", json=tnds, headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["loai_dap_an_nhap"] == "dung_sai_4y"

    tln = {"loai_cau": "TLN", "do_kho": "kho", "de_bai": "Tìm $a$.",
           "chuyen_de": "Khảo sát hàm số", "meta": {"dap_an_cuoi": "3"}}
    r2 = client.post("/api/problems", json=tln, headers=_h(tok))
    assert r2.status_code == 200, r2.text
    assert r2.json()["loai_dap_an_nhap"] == "gia_tri"


def test_hs_khong_tao_duoc_cau_hoi(client, db):
    seed_all(db)
    tok = _token(client, "hs_test")
    r = client.post("/api/problems",
                    json={"loai_cau": "TLN", "de_bai": "x", "meta": {"dap_an_cuoi": "1"}},
                    headers=_h(tok))
    assert r.status_code == 403


def test_xoa_bai_co_phien_bi_an(client, db):
    """Câu hỏi đã có phiên học → soft-delete (bi_an=True), không xóa cứng."""
    hs, gv, _, p = seed_all(db)
    htok = _token(client, "hs_test")
    client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(htok))
    gtok = _token(client, "gv_test")
    r = client.delete(f"/api/problems/{p.id}", headers=_h(gtok))
    assert r.status_code == 200
    assert r.json()["an"] is True
    # Câu hỏi vẫn còn trong DB nhưng bi_an = True
    from app.models.problem import Problem
    p_db = db.get(Problem, p.id)
    assert p_db is not None
    assert p_db.bi_an is True
    # HS không thấy câu hỏi đã ẩn
    hs_r = client.get("/api/problems", headers=_h(htok))
    ids = [x["id"] for x in hs_r.json()]
    assert p.id not in ids


def test_khoi_phuc_bai(client, db):
    """Sau khi ẩn, GV khôi phục → câu hỏi hiển thị lại."""
    hs, gv, _, p = seed_all(db)
    htok = _token(client, "hs_test")
    client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(htok))
    gtok = _token(client, "gv_test")
    client.delete(f"/api/problems/{p.id}", headers=_h(gtok))
    r = client.patch(f"/api/problems/{p.id}/khoi-phuc", headers=_h(gtok))
    assert r.status_code == 200
    from app.models.problem import Problem
    assert db.get(Problem, p.id).bi_an is False


def test_anh_huong_xoa_vinh_vien(client, db):
    """API /anh-huong trả số liệu chính xác trước khi xóa vĩnh viễn."""
    hs, gv, _, p = seed_all(db)
    htok = _token(client, "hs_test")
    gtok = _token(client, "gv_test")
    # Tạo phiên + gợi ý (để có turn)
    s = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(htok)).json()
    client.post(f"/api/sessions/{s['session_id']}/message",
                json={"noi_dung": "GỢI Ý"}, headers=_h(htok))
    # Ẩn câu hỏi
    client.delete(f"/api/problems/{p.id}", headers=_h(gtok))
    # Xem ảnh hưởng
    r = client.get(f"/api/problems/{p.id}/anh-huong", headers=_h(gtok))
    assert r.status_code == 200
    ah = r.json()
    assert ah["so_phien"] == 1
    assert ah["so_hoc_sinh"] == 1
    assert ah["so_luot"] >= 1


def test_xoa_vinh_vien(client, db):
    """Xóa vĩnh viễn câu đã ẩn → cascade xóa session/turn/flag, câu hỏi biến mất khỏi DB."""
    from app.models.problem import Problem
    from app.models.session import Session as SessionModel
    hs, gv, _, p = seed_all(db)
    htok = _token(client, "hs_test")
    gtok = _token(client, "gv_test")
    s = client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(htok)).json()
    sid = s["session_id"]
    # Ẩn rồi xóa vĩnh viễn
    client.delete(f"/api/problems/{p.id}", headers=_h(gtok))
    r = client.delete(f"/api/problems/{p.id}/vinh-vien", headers=_h(gtok))
    assert r.status_code == 200
    assert r.json()["so_phien_da_xoa"] == 1
    # Câu hỏi và phiên học đều biến mất
    assert db.get(Problem, p.id) is None
    assert db.get(SessionModel, sid) is None


def test_gv_khac_khong_sua_duoc_bai(client, db):
    """GV khác (không phải người tạo, không phải Quản lý) không sửa được bài."""
    from app.models.user import User, VaiTro
    _, gv, _, p = seed_all(db)
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_test",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()
    tok2 = _token(client, "gv2_test")
    r = client.patch(f"/api/problems/{p.id}", json={"de_bai": "Sửa trộm"}, headers=_h(tok2))
    assert r.status_code == 403


def test_quan_ly_sua_duoc_va_gui_thong_bao(client, db):
    """Tài khoản Quản lý sửa được bài của GV khác và gửi thông báo cho chủ."""
    from app.models.thong_bao import ThongBao
    from app.models.user import User, VaiTro
    _, gv, _, p = seed_all(db)
    ql = User(vai_tro=VaiTro.gv, ho_ten="Quản lý", dang_nhap="ql_test",
              mat_khau_hash=hash_password("pass"), la_quan_ly=True)
    db.add(ql)
    db.commit()
    tok = _token(client, "ql_test")
    r = client.patch(f"/api/problems/{p.id}", json={"de_bai": "Đề mới"}, headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["de_bai"] == "Đề mới"
    # Chủ sở hữu (gv) nhận được 1 thông báo loại quan_ly
    tb = db.query(ThongBao).filter(ThongBao.nguoi_nhan_id == gv.id).all()
    assert any(t.loai.value == "quan_ly" for t in tb)


def test_tao_tln_dap_an_cuoi_sai(client, db):
    """Tạo TLN với đáp án cuối không hợp lệ → 400."""
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    # Quá 4 ký tự
    r = client.post("/api/problems", json={
        "loai_cau": "TLN", "do_kho": "tb", "de_bai": "Tìm x.",
        "chuyen_de": "Khảo sát hàm số", "meta": {"dap_an_cuoi": "12345"},
    }, headers=_h(tok))
    assert r.status_code == 400
    assert "4 ký tự" in r.json()["detail"]

    # Không phải số
    r2 = client.post("/api/problems", json={
        "loai_cau": "TLN", "do_kho": "tb", "de_bai": "Tìm x.",
        "chuyen_de": "Khảo sát hàm số", "meta": {"dap_an_cuoi": "abc"},
    }, headers=_h(tok))
    assert r2.status_code == 400


def test_tao_tln_dap_an_cuoi_hop_le(client, db):
    """Tạo TLN với đáp án hợp lệ: số nguyên, thập phân dấu phẩy, số âm."""
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    for da in ["3", "-2", "1,5", "-1,5", "0"]:
        r = client.post("/api/problems", json={
            "loai_cau": "TLN", "do_kho": "de", "de_bai": f"Tìm x ({da}).",
            "chuyen_de": "Khảo sát hàm số", "meta": {"dap_an_cuoi": da},
        }, headers=_h(tok))
        assert r.status_code == 200, f"Đáp án '{da}' phải hợp lệ, nhưng nhận {r.status_code}: {r.text}"


def test_import_tln_dap_an_cuoi_sai_bi_bao_loi(client, db):
    """Import TLN với đáp án cuối sai → dòng đó vào lỗi, không tạo."""
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {"loai_cau": "TLN", "chuyen_de": "Test", "de_bai": "x", "meta": {"dap_an_cuoi": "12345"}},
        {"loai_cau": "TLN", "chuyen_de": "Test", "de_bai": "y", "meta": {"dap_an_cuoi": "3"}},
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    res = r.json()
    assert res["da_tao"] == 1
    assert len(res["loi"]) == 1
    assert "4 ký tự" in res["loi"][0]["ly_do"]


def test_anh_huong_gv_khac_bi_chan(client, db):
    """IDOR: GV khác KHÔNG được xem ảnh hưởng (số phiên/HS/cờ) bài của GV khác nếu biết id.
    Trước khi vá, endpoint /anh-huong không kiểm chủ sở hữu như patch/xóa kế bên."""
    from app.models.user import User, VaiTro
    _, gv, _, p = seed_all(db)
    gv2 = User(vai_tro=VaiTro.gv, ho_ten="GV2", dang_nhap="gv2_ah",
               mat_khau_hash=hash_password("pass"))
    db.add(gv2)
    db.commit()
    r = client.get(f"/api/problems/{p.id}/anh-huong", headers=_h(_token(client, "gv2_ah")))
    assert r.status_code == 403


def test_anh_huong_quan_ly_xem_duoc_bai_gv_khac(client, db):
    """Quản lý/Admin toàn quyền → vẫn xem được ảnh hưởng bài của GV khác."""
    from app.models.user import User, VaiTro
    _, gv, _, p = seed_all(db)
    ql = User(vai_tro=VaiTro.gv, ho_ten="Quản lý", dang_nhap="ql_ah",
              mat_khau_hash=hash_password("pass"), la_quan_ly=True)
    db.add(ql)
    db.commit()
    # /anh-huong yêu cầu bài đã ẩn trước; DELETE chỉ soft-delete khi bài đã có phiên học
    # → HS tạo phiên, GV chủ ẩn bài, rồi Quản lý xem ảnh hưởng.
    client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(_token(client, "hs_test")))
    client.delete(f"/api/problems/{p.id}", headers=_h(_token(client, "gv_test")))
    r = client.get(f"/api/problems/{p.id}/anh-huong", headers=_h(_token(client, "ql_ah")))
    assert r.status_code == 200


def test_xoa_vinh_vien_yeu_cau_bi_an_truoc(client, db):
    """Không thể xóa vĩnh viễn câu hỏi chưa qua bước ẩn."""
    _, gv, _, p = seed_all(db)
    gtok = _token(client, "gv_test")
    r = client.delete(f"/api/problems/{p.id}/vinh-vien", headers=_h(gtok))
    assert r.status_code == 400
    assert "ẩn" in r.json()["detail"]
