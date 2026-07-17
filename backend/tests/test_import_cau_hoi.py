"""Tests import hàng loạt câu hỏi từ file mẫu (GV)."""

from app.models.problem import TrangThaiDuyet
from tests.test_api_flow import _h, _token, seed_all


def test_import_tn4pa(client, db):
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {
            "loai_cau": "TN4PA",
            "chuyen_de": "Khảo sát hàm số",
            "dang_ten": "",
            "do_kho": "de",
            "de_bai": "Hàm số $y=x^2$ đồng biến trên?",
            "meta": {
                "phuong_an": {"A": "$(-\\infty;0)$", "B": "$(0;+\\infty)$", "C": "$\\mathbb{R}$", "D": "$(1;2)$"},
                "dap_an_dung": "B",
                "bat_buoc_suy_luan": False,
            },
        },
        {
            "loai_cau": "TN4PA",
            "chuyen_de": "Tích phân",
            "dang_ten": "",
            "do_kho": "tb",
            "de_bai": "Tính $\\int_0^1 1\\,dx$.",
            "meta": {
                "phuong_an": {"A": "$1$", "B": "$0$", "C": "$2$", "D": "$-1$"},
                "dap_an_dung": "A",
                "bat_buoc_suy_luan": False,
            },
        },
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["da_tao"] == 2
    assert len(res["ids"]) == 2
    assert res["loi"] == []


def test_import_tnds(client, db):
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {
            "loai_cau": "TNDS",
            "chuyen_de": "Khảo sát hàm số",
            "dang_ten": "",
            "do_kho": "kho",
            "de_bai": "Xét tính đúng sai.",
            "meta": {
                "y": [
                    {"ky_hieu": "a", "noi_dung_y": "Ý a", "dap_an": "Dung"},
                    {"ky_hieu": "b", "noi_dung_y": "Ý b", "dap_an": "Sai"},
                    {"ky_hieu": "c", "noi_dung_y": "Ý c", "dap_an": "Dung"},
                    {"ky_hieu": "d", "noi_dung_y": "Ý d", "dap_an": "Sai"},
                ],
            },
        },
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["da_tao"] == 1


def test_import_tln(client, db):
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {
            "loai_cau": "TLN",
            "chuyen_de": "Tích phân",
            "dang_ten": "",
            "do_kho": "tb",
            "de_bai": "Tính $\\int_0^2 x\\,dx$.",
            "meta": {"dap_an_cuoi": "2"},
        },
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["da_tao"] == 1


def test_trang_thai_import_la_cho_duyet(client, db):
    """Câu hỏi import phải là cho_duyet, thuộc người tạo (không da_duyet như tạo thủ công)."""
    from app.models.problem import Problem
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [{
        "loai_cau": "TLN",
        "chuyen_de": "Test",
        "do_kho": "de",
        "de_bai": "Câu test.",
        "meta": {"dap_an_cuoi": "1"},
    }]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    pid = r.json()["ids"][0]
    p = db.get(Problem, pid)
    assert p.trang_thai_duyet == TrangThaiDuyet.cho_duyet
    assert p.nguoi_tao_id == gv.id


def test_hs_khong_import_duoc(client, db):
    seed_all(db)
    tok = _token(client, "hs_test")
    r = client.post("/api/problems/import-batch",
                    json={"items": [{"loai_cau": "TLN", "chuyen_de": "x",
                                     "de_bai": "x", "meta": {"dap_an_cuoi": "1"}}]},
                    headers=_h(tok))
    assert r.status_code == 403


def test_import_mixed_loi_va_hop_le(client, db):
    """Dòng lỗi (loai_cau sai) bị bỏ qua; dòng hợp lệ vẫn được tạo."""
    _, gv, _, _ = seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {"loai_cau": "KHONG_HOP_LE", "chuyen_de": "x", "de_bai": "x", "meta": {}},
        {"loai_cau": "TLN", "chuyen_de": "Tích phân", "de_bai": "Tính x.", "meta": {"dap_an_cuoi": "5"}},
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["da_tao"] == 1
    assert len(res["loi"]) == 1


def test_import_batch_qua_1000_dong_bi_chan(client, db):
    """max_length=1000 trên ImportBatchRequest.items — chặn batch khổng lồ tốn RAM/CPU
    không giới hạn, TRƯỚC KHI chạm tới service (lỗi validate 422, không phải lỗi nghiệp vụ)."""
    seed_all(db)
    tok = _token(client, "gv_test")
    items = [
        {"loai_cau": "TLN", "chuyen_de": "x", "de_bai": "x", "meta": {"dap_an_cuoi": "1"}}
        for _ in range(1001)
    ]
    r = client.post("/api/problems/import-batch", json={"items": items}, headers=_h(tok))
    assert r.status_code == 422
