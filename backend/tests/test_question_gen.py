"""Tests Phase 5 — AI sinh câu hỏi + GV duyệt."""

from app.auth.security import hash_password
from app.core.matching.cas import kiem_tra_bieu_thuc
from app.llm.client import StubLLMClient
from app.llm.question_gen import sinh_nhap, validate_cau_hoi
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem
from app.models.user import User, VaiTro
from app.services.question_gen_service import sinh_va_luu


def _login(client, dang_nhap):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dang_nhap, "mat_khau": "password"}).json()["access_token"]


def _seed(db):
    lop = Lop(ten="12A1")
    db.add(lop)
    db.flush()
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    db.add(gv)
    db.flush()
    lop.gv_id = gv.id  # HS tự luyện bài của GV chủ nhiệm lớp
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add(hs)
    db.commit()


# ----- kiem_tra_bieu_thuc -----

def test_kiem_tra_bieu_thuc_hop_le():
    assert kiem_tra_bieu_thuc("3*x**2-3") is True
    assert kiem_tra_bieu_thuc("sqrt(2)") is True
    assert kiem_tra_bieu_thuc("pi/6") is True
    assert kiem_tra_bieu_thuc("") is True  # bước không có biểu thức


def test_kiem_tra_bieu_thuc_loi():
    assert kiem_tra_bieu_thuc("3*x +-* 2") is False
    assert kiem_tra_bieu_thuc("__import__('os')") is False


# ----- Stub sinh đúng mẫu + số gợi ý theo độ khó -----

def test_stub_sinh_tln_so_goi_y_theo_do_kho():
    llm = StubLLMClient()
    for do_kho, n in [("de", 2), ("tb", 3), ("kho", 4)]:
        r = llm.sinh_cau_hoi({"loai_cau": "TLN", "chuyen_de": "X", "do_kho": do_kho, "so_luong": 1})
        cau = r["cau_hoi"][0]
        assert cau["loai_cau"] == "TLN"
        for s in cau["solution_steps"]:
            assert len(s["danh_sach_goi_y"]) == n


def test_stub_sinh_tn4pa_dung_mau():
    llm = StubLLMClient()
    r = llm.sinh_cau_hoi({"loai_cau": "TN4PA", "chuyen_de": "X", "do_kho": "de", "so_luong": 2})
    assert len(r["cau_hoi"]) == 2
    cau = r["cau_hoi"][0]
    assert set(cau["meta"]["phuong_an"].keys()) == {"A", "B", "C", "D"}
    assert cau["meta"]["dap_an_dung"] in {"A", "B", "C", "D"}


def test_stub_sinh_tnds_4_y():
    llm = StubLLMClient()
    r = llm.sinh_cau_hoi({"loai_cau": "TNDS", "chuyen_de": "X", "do_kho": "kho", "so_luong": 1})
    cau = r["cau_hoi"][0]
    assert len(cau["meta"]["y"]) == 4


def test_stub_sinh_cau_hoi_luon_co_loi_giai_chi_tiet():
    """AI (kể cả Stub) phải tự sinh 'loi_giai_chi_tiet' cho mọi câu — GV chỉ cần sửa,
    không phải viết từ đầu."""
    llm = StubLLMClient()
    for loai in ("TN4PA", "TNDS", "TLN"):
        r = llm.sinh_cau_hoi({"loai_cau": loai, "chuyen_de": "X", "do_kho": "tb", "so_luong": 1})
        cau = r["cau_hoi"][0]
        assert cau.get("loi_giai_chi_tiet", "").strip(), f"{loai} thiếu loi_giai_chi_tiet"


def test_validate_cau_hoi_thieu_loi_giai_chi_tiet_bi_canh_bao():
    cau = _cau_tln("5")
    cau["loi_giai_chi_tiet"] = ""
    cb = validate_cau_hoi(cau)
    assert any("lời giải chi tiết" in c.lower() for c in cb)


# ----- validate_cau_hoi -----

def test_validate_cau_hoi_sach():
    llm = StubLLMClient()
    nhap = sinh_nhap(llm, {"loai_cau": "TLN", "chuyen_de": "X", "do_kho": "tb", "so_luong": 1})
    assert nhap[0]["canh_bao"] == []


def test_validate_cau_hoi_bieu_thuc_loi():
    cau = {
        "loai_cau": "TLN", "de_bai": "Test", "loai_dap_an_nhap": "gia_tri",
        "meta": {"dap_an_cuoi": "5"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "x",
             "bieu_thuc_ket_qua": "3 +* x", "danh_sach_goi_y": ["a"]},
        ],
    }
    cb = validate_cau_hoi(cau)
    assert any("SymPy không parse" in c for c in cb)


def _cau_tln(dap_an_cuoi):
    return {
        "loai_cau": "TLN", "de_bai": "Test", "loai_dap_an_nhap": "gia_tri",
        "meta": {"dap_an_cuoi": dap_an_cuoi},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "x",
             "bieu_thuc_ket_qua": "5", "danh_sach_goi_y": ["a"]},
        ],
        "loi_giai_chi_tiet": "Lời giải mẫu cho test.",
    }


def test_validate_tln_dap_an_hop_le_toi_da_4_ky_tu():
    for dung in ("125", "-125", "3.12", "-3.1", "5", "0.5"):
        cb = validate_cau_hoi(_cau_tln(dung))
        assert cb == [], f"{dung!r} phải hợp lệ nhưng có cảnh báo: {cb}"


def test_validate_tln_dap_an_qua_4_ky_tu_bao_loi():
    # "-3.124" dài 6 ký tự (gồm dấu - và .) — vượt quá 4 ký tự cho phép.
    cb = validate_cau_hoi(_cau_tln("-3.124"))
    assert any("dap_an_cuoi" in c and "4 ký tự" in c for c in cb)


def test_validate_tln_dap_an_khong_phai_so_thap_phan_bao_loi():
    for xau in ("sqrt(2)", "1/3", "pi/6", "abc"):
        cb = validate_cau_hoi(_cau_tln(xau))
        assert any("dap_an_cuoi" in c for c in cb), f"{xau!r} phải bị cảnh báo"


def _cau_tln_buoc(bieu_thuc_ket_qua):
    return {
        "loai_cau": "TLN", "de_bai": "Test", "loai_dap_an_nhap": "gia_tri",
        "meta": {"dap_an_cuoi": "5"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "x",
             "bieu_thuc_ket_qua": bieu_thuc_ket_qua, "danh_sach_goi_y": ["a"]},
        ],
    }


def test_validate_bieu_thuc_trung_gian_chua_tinh_bao_canh_bao():
    # Bug thật: AI để nguyên "binomial(15, 3)" thay vì tính ra 455.
    cb = validate_cau_hoi(_cau_tln_buoc("binomial(15, 3)"))
    assert any("trung gian chưa tính" in c and "455" in c for c in cb)


def test_validate_bieu_thuc_da_tinh_khong_bao_canh_bao():
    for bt in ("455", "3*x**2-3", "sqrt(2)", "20"):
        cb = validate_cau_hoi(_cau_tln_buoc(bt))
        assert not any("trung gian chưa tính" in c for c in cb), f"{bt!r} không nên bị cảnh báo"


def test_validate_bieu_thuc_ham_to_hop_con_bien_khong_bao_canh_bao():
    # Còn biến tự do (theo x) -> giữ dạng hàm là đúng, không phải "trung gian chưa tính".
    cb = validate_cau_hoi(_cau_tln_buoc("binomial(10, x)"))
    assert not any("trung gian chưa tính" in c for c in cb)


def test_validate_tn4pa_thieu_dap_an():
    cau = {
        "loai_cau": "TN4PA", "de_bai": "Test", "meta": {"phuong_an": {"A": "1"}},
        "solution_steps": [{"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "x",
                            "bieu_thuc_ket_qua": "1", "danh_sach_goi_y": ["a"]}],
    }
    cb = validate_cau_hoi(cau)
    assert any("phương án" in c for c in cb)
    assert any("dap_an_dung" in c for c in cb)


# ----- Gắn dạng cho câu sinh ra + truyền tên dạng cho LLM -----

class _FakeLLM(StubLLMClient):
    """Ghi lại yeu_cau để kiểm tra tên dạng được truyền vào prompt."""

    def __init__(self):
        self.yeu_cau_da_nhan = None

    def sinh_cau_hoi(self, yeu_cau):
        self.yeu_cau_da_nhan = yeu_cau
        return super().sinh_cau_hoi(yeu_cau)


def _seed_danh_muc(db):
    cd = ChuyenDe(ten="Khảo sát hàm số")
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Tìm cực trị")
    db.add(dang)
    db.commit()
    return dang


def test_sinh_gan_dang_va_dong_bo_chuyen_de(db):
    dang = _seed_danh_muc(db)
    llm = _FakeLLM()
    ket_qua = sinh_va_luu(
        db,
        {"chuyen_de": "(sai - sẽ bị ghi đè)", "dang_id": dang.id,
         "loai_cau": "TLN", "do_kho": "tb", "so_luong": 2},
        nguoi_tao_id=None,
        llm=llm,
    )
    # LLM nhận đúng tên dạng + chuyên đề chuẩn
    assert llm.yeu_cau_da_nhan["dang"] == "Tìm cực trị"
    assert llm.yeu_cau_da_nhan["chuyen_de"] == "Khảo sát hàm số"
    # Mọi câu lưu ra đều gắn dang_id và chuyên đề đúng
    for d in ket_qua:
        p = db.get(Problem, d["id"])
        assert p.dang_id == dang.id
        assert p.chuyen_de == "Khảo sát hàm số"


def test_sinh_va_luu_luu_ca_loi_giai_chi_tiet_ai_sinh(db):
    """AI (kể cả sinh hàng loạt) tự sinh loi_giai_chi_tiet — phải lưu tới DB để GV sửa,
    không phải để trống chờ GV viết từ đầu. hien_loi_giai_chi_tiet mặc định VẪN False
    (an toàn — GV phải chủ động bật mới cho HS xem)."""
    dang = _seed_danh_muc(db)
    llm = StubLLMClient()
    ket_qua = sinh_va_luu(
        db,
        {"chuyen_de": "X", "dang_id": dang.id, "loai_cau": "TLN", "do_kho": "tb", "so_luong": 1},
        nguoi_tao_id=None,
        llm=llm,
    )
    p = db.get(Problem, ket_qua[0]["id"])
    assert p.loi_giai_chi_tiet.strip() != ""
    assert p.hien_loi_giai_chi_tiet is False


# ----- Parse JSON bền + retry (chống lỗi 500) -----

def test_parse_json_latex_va_phay_thua():
    from app.llm.client import _parse_json_cau_hoi
    # backslash đơn của LaTeX + dấu phẩy thừa trước ]
    raw = '{"cau_hoi": [{"loai_cau": "TLN", "de_bai": "$\\dfrac{1}{2}$",}]}'
    d = _parse_json_cau_hoi(raw)
    assert d["cau_hoi"][0]["de_bai"] == "$\\dfrac{1}{2}$"


def test_parse_json_mang_tran_va_rao_code():
    from app.llm.client import _parse_json_cau_hoi
    d = _parse_json_cau_hoi('```json\n[{"loai_cau":"TLN","de_bai":"x"}]\n```')
    assert len(d["cau_hoi"]) == 1


def test_goi_va_parse_thu_lai_roi_thanh_cong(monkeypatch):
    from app.llm import client as cl
    monkeypatch.setattr(cl.time, "sleep", lambda *a, **k: None)  # khỏi chờ
    dem = {"n": 0}

    def call_fn(system, user):
        dem["n"] += 1
        if dem["n"] < 2:
            raise RuntimeError("503 quá tải")
        return '{"cau_hoi": [{"loai_cau": "TLN", "de_bai": "x"}]}'

    d = cl._goi_va_parse(call_fn, "sys", "usr")
    assert dem["n"] == 2 and len(d["cau_hoi"]) == 1


def test_goi_va_parse_het_luot_nem_loi(monkeypatch):
    from app.llm import client as cl
    monkeypatch.setattr(cl.time, "sleep", lambda *a, **k: None)
    import pytest
    with pytest.raises(RuntimeError):
        cl._goi_va_parse(lambda s, u: "không phải json", "sys", "usr")


# ----- Endpoint KHÔNG bao giờ trả 500 -----

class _LLMLoi(StubLLMClient):
    def sinh_cau_hoi(self, yeu_cau):
        raise RuntimeError("Mô phỏng API lỗi")


class _LLMCauRong(StubLLMClient):
    def sinh_cau_hoi(self, yeu_cau):
        return {"cau_hoi": [
            {"loai_cau": "TLN", "de_bai": "Câu tốt $x$", "meta": {"dap_an_cuoi": "1"},
             "solution_steps": [{"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "a",
                                 "bieu_thuc_ket_qua": "1", "danh_sach_goi_y": ["g"]}]},
            {"loai_cau": "TLN", "de_bai": "   "},  # rỗng → phải bị bỏ qua
        ]}


def test_generate_loi_llm_tra_502_khong_500(db, client, monkeypatch):
    _seed(db)
    import app.api.questions_ai as qa
    monkeypatch.setattr(qa, "get_llm_client", lambda cfg=None: _LLMLoi())
    h = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.post("/api/questions-ai/generate", headers=h,
                    json={"chuyen_de": "X", "loai_cau": "TLN", "do_kho": "tb", "so_luong": 1})
    assert r.status_code == 502  # KHÔNG phải 500


def test_generate_bo_qua_cau_rong(db, client, monkeypatch):
    _seed(db)
    import app.api.questions_ai as qa
    monkeypatch.setattr(qa, "get_llm_client", lambda cfg=None: _LLMCauRong())
    h = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.post("/api/questions-ai/generate", headers=h,
                    json={"chuyen_de": "X", "loai_cau": "TLN", "do_kho": "tb", "so_luong": 2})
    assert r.status_code == 200
    assert len(r.json()) == 1  # chỉ giữ câu hợp lệ


# ----- API -----

def test_api_generate_va_duyet(db, client):
    _seed(db)
    token = _login(client, "gv1")
    h = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/questions-ai/generate", headers=h,
                    json={"chuyen_de": "Khảo sát hàm số", "loai_cau": "TLN",
                          "do_kho": "tb", "so_luong": 2})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert all(d["trang_thai_duyet"] == "cho_duyet" for d in data)
    pid = data[0]["id"]

    # Duyệt 1 câu
    r2 = client.post(f"/api/questions-ai/{pid}/duyet", headers=h, json={"hanh_dong": "duyet"})
    assert r2.status_code == 200
    assert r2.json()["trang_thai_duyet"] == "da_duyet"


def test_api_generate_tra_meta_day_du(db, client):
    _seed(db)
    h = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.post("/api/questions-ai/generate", headers=h,
                    json={"chuyen_de": "X", "loai_cau": "TN4PA", "do_kho": "tb", "so_luong": 1})
    assert r.status_code == 200
    cau = r.json()[0]
    # Bản nháp phải kèm meta đầy đủ để giao diện hiện ABCD
    assert set(cau["meta"]["phuong_an"].keys()) == {"A", "B", "C", "D"}
    assert cau["meta"]["dap_an_dung"] in {"A", "B", "C", "D"}


def test_api_generate_phan_quyen_hs_bi_chan(db, client):
    _seed(db)
    token = _login(client, "hs1")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/questions-ai/generate", headers=h,
                    json={"chuyen_de": "X", "loai_cau": "TLN", "do_kho": "tb", "so_luong": 1})
    assert r.status_code == 403


def test_cau_chua_duyet_khong_hien_cho_hs(db, client):
    _seed(db)
    gv = _login(client, "gv1")
    client.post("/api/questions-ai/generate", headers={"Authorization": f"Bearer {gv}"},
                json={"chuyen_de": "X", "loai_cau": "TLN", "do_kho": "tb", "so_luong": 1})

    # HS xem danh sách bài → không có câu cho_duyet
    hs = _login(client, "hs1")
    r = client.get("/api/problems", headers={"Authorization": f"Bearer {hs}"})
    assert r.status_code == 200
    assert r.json() == []  # chưa duyệt → HS không thấy


def test_duyet_roi_hs_thay(db, client):
    _seed(db)
    gv = _login(client, "gv1")
    gh = {"Authorization": f"Bearer {gv}"}
    data = client.post("/api/questions-ai/generate", headers=gh,
                       json={"chuyen_de": "X", "loai_cau": "TLN",
                             "do_kho": "tb", "so_luong": 1}).json()
    pid = data[0]["id"]
    client.post(f"/api/questions-ai/{pid}/duyet", headers=gh, json={"hanh_dong": "duyet"})

    hs = _login(client, "hs1")
    r = client.get("/api/problems", headers={"Authorization": f"Bearer {hs}"})
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == pid
