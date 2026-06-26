"""Test API GV sửa/xóa câu hỏi + duyệt."""

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
    }
    r = client.post("/api/problems", json=body, headers=_h(tok))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["loai_cau"] == "TN4PA"
    assert data["loai_dap_an_nhap"] == "chon_phuong_an"
    assert data["trang_thai_duyet"] == TrangThaiDuyet.cho_duyet.value
    assert data["meta"]["dap_an_dung"] == "B"
    # HS không thấy bài chưa duyệt
    htok = _token(client, "hs_test")
    assert client.get(f"/api/problems/{data['id']}", headers=_h(htok)).status_code == 404


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


def test_xoa_bai_co_phien_bi_chan(client, db):
    hs, gv, _, p = seed_all(db)
    htok = _token(client, "hs_test")
    client.post("/api/sessions", json={"problem_id": p.id}, headers=_h(htok))
    gtok = _token(client, "gv_test")
    r = client.delete(f"/api/problems/{p.id}", headers=_h(gtok))
    assert r.status_code == 400
    assert "phiên" in r.json()["detail"]
