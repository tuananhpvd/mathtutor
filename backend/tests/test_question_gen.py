"""Tests Phase 5 — AI sinh câu hỏi + GV duyệt."""

from app.auth.security import hash_password
from app.core.matching.cas import kiem_tra_bieu_thuc
from app.llm.client import StubLLMClient
from app.llm.question_gen import sinh_nhap, validate_cau_hoi
from app.models.danh_muc import ChuyenDe, Dang
from app.models.lop import Lop
from app.models.problem import Problem
from app.models.user import User, VaiTro
from app.services.question_gen_service import luu_cau_nhap, sinh_va_luu


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


# ----- Chặn lưu khi bieu_thuc_ket_qua không parse được (v142) -----

class _FakeLLMBieuThucHong(StubLLMClient):
    """Luôn trả 1 câu TLN có bieu_thuc_ket_qua còn sót $...$ — mô phỏng đúng sự cố thực tế
    (AI quên bỏ $ dù prompt cấm) khiến CAS không bao giờ chấm đúng được cho bước đó."""

    def sinh_cau_hoi(self, yeu_cau):
        return {"cau_hoi": [{
            "chuyen_de": yeu_cau.get("chuyen_de", "X"), "loai_cau": "TLN", "do_kho": "tb",
            "de_bai": "Tính đạo hàm.",
            "loai_dap_an_nhap": "gia_tri", "che_do_so_khop": "tuong_duong",
            "meta": {"dap_an_cuoi": "2"},
            "solution_steps": [
                {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "b1",
                 "bieu_thuc_ket_qua": "$3x^2-3$", "danh_sach_goi_y": ["gợi ý"]},
            ],
            "loi_giai_chi_tiet": "giai",
        }]}


def test_sinh_va_luu_bo_qua_cau_co_bieu_thuc_ket_qua_hong(db):
    """AI sinh câu có bieu_thuc_ket_qua hỏng ($ thừa) → KHÔNG được lưu vào DB (bị bỏ qua
    như câu rỗng/hỏng khác), thay vì lưu rồi chỉ cảnh báo (lỗi âm thầm, lộ ra khi HS làm)."""
    dang = _seed_danh_muc(db)
    so_luong_truoc = db.query(Problem).count()
    ket_qua = sinh_va_luu(
        db,
        {"chuyen_de": "X", "dang_id": dang.id, "loai_cau": "TLN", "do_kho": "tb", "so_luong": 1},
        nguoi_tao_id=None,
        llm=_FakeLLMBieuThucHong(),
    )
    assert ket_qua == []
    assert db.query(Problem).count() == so_luong_truoc


def test_luu_cau_nhap_tu_choi_bieu_thuc_ket_qua_hong(db):
    """luu_cau_nhap (luồng "AI tạo bước và gợi ý", GV bấm Lưu) cũng phải chặn — không chỉ
    luồng sinh hàng loạt."""
    import pytest

    cau = {
        "chuyen_de": "X", "loai_cau": "TLN", "do_kho": "tb", "de_bai": "Tính đạo hàm.",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "b1",
             "bieu_thuc_ket_qua": "$3x^2-3$", "danh_sach_goi_y": ["gợi ý"]},
        ],
        "loi_giai_chi_tiet": "giai",
    }
    with pytest.raises(ValueError, match="không parse được"):
        luu_cau_nhap(db, cau, nguoi_tao_id=None)


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


def test_parse_json_latex_chu_b_f_n_r_t():
    """Hồi quy: \\frac \\right \\to \\neq \\begin đều bắt đầu bằng b/f/n/r/t — trước đây
    bị coi nhầm là escape JSON hợp lệ (\\f \\r \\n \\t \\b) nên không được vá, khiến JSON
    hỏng thầm lặng hoặc lỗi hẳn khi đứng cạnh "\\\\" LaTeX (vd trong \\begin{cases}...)."""
    from app.llm.client import _parse_json_cau_hoi
    raw = (
        '{"cau_hoi": [{"loai_cau": "TLN", '
        '"de_bai": "Tinh $\\frac{1}{x}$ khi $x \\to 0$, biet $x \\neq 0$", '
        '"y_a": "$\\begin{cases} x=1 \\\\ y=2 \\end{cases}$"}]}'
    )
    d = _parse_json_cau_hoi(raw)
    de_bai = d["cau_hoi"][0]["de_bai"]
    assert "\\frac" in de_bai
    assert "\\to" in de_bai
    assert "\\neq" in de_bai
    assert "\\begin{cases}" in d["cau_hoi"][0]["y_a"]


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


def test_goi_va_parse_phan_hoi_loi_cho_lan_thu_lai(monkeypatch, caplog):
    """Lớp phòng thủ #2/#3 (nối tiếp v84): khi JSON hỏng, lần thử lại kế tiếp phải được
    nối thêm ghi chú lỗi cụ thể (để AI tự sửa thay vì lặp lại y hệt sai lầm cũ), và JSON thô
    phải được log lại để chẩn đoán nhanh nếu tương lai có kiểu lỗi mới chưa từng gặp."""
    import logging

    from app.llm import client as cl
    monkeypatch.setattr(cl.time, "sleep", lambda *a, **k: None)
    lan_nhan_duoc = []

    def call_fn(system, user):
        lan_nhan_duoc.append(user)
        if len(lan_nhan_duoc) < 2:
            return "khong phai json hop le"
        return '{"cau_hoi": [{"loai_cau": "TLN", "de_bai": "x"}]}'

    with caplog.at_level(logging.WARNING):
        d = cl._goi_va_parse(call_fn, "sys", "usr goc")
    assert len(d["cau_hoi"]) == 1
    assert lan_nhan_duoc[0] == "usr goc"  # lần đầu: nguyên văn, chưa có phản hồi lỗi
    assert "usr goc" in lan_nhan_duoc[1]
    assert "LƯU Ý" in lan_nhan_duoc[1]  # lần 2: có ghi chú lỗi lần trước để AI tự sửa
    assert any("JSON thô" in r.message for r in caplog.records)


def test_goi_va_parse_khong_phan_hoi_khi_loi_mang(monkeypatch):
    """Lỗi mạng/API (KHÔNG có phản hồi JSON để đọc) thì KHÔNG nối ghi chú lỗi vào lần thử
    lại — phân biệt rõ với lỗi parse JSON (nối ghi chú không có ý nghĩa gì cho lỗi mạng)."""
    from app.llm import client as cl
    monkeypatch.setattr(cl.time, "sleep", lambda *a, **k: None)
    lan_nhan_duoc = []

    def call_fn(system, user):
        lan_nhan_duoc.append(user)
        if len(lan_nhan_duoc) < 2:
            raise RuntimeError("503 quá tải")
        return '{"cau_hoi": [{"loai_cau": "TLN", "de_bai": "x"}]}'

    d = cl._goi_va_parse(call_fn, "sys", "usr goc")
    assert len(d["cau_hoi"]) == 1
    assert lan_nhan_duoc == ["usr goc", "usr goc"]  # lỗi mạng: user KHÔNG bị đổi


# ----- Schema JSON cho Structured Output (Gemini responseSchema, lớp phòng thủ #1) -----

def test_schema_sinh_cau_hoi_tn4pa_dung_cau_truc():
    from app.llm.prompts import schema_sinh_cau_hoi
    s = schema_sinh_cau_hoi("TN4PA")
    item = s["properties"]["cau_hoi"]["items"]
    assert item["properties"]["loai_cau"]["enum"] == ["TN4PA"]
    meta = item["properties"]["meta"]
    assert set(meta["properties"]["phuong_an"]["required"]) == {"A", "B", "C", "D"}
    assert meta["properties"]["dap_an_dung"]["enum"] == ["A", "B", "C", "D"]


def test_schema_sinh_cau_hoi_tnds_dung_cau_truc():
    from app.llm.prompts import schema_sinh_cau_hoi
    s = schema_sinh_cau_hoi("TNDS")
    meta = s["properties"]["cau_hoi"]["items"]["properties"]["meta"]
    y_item = meta["properties"]["y"]["items"]
    assert y_item["properties"]["dap_an"]["enum"] == ["Dung", "Sai"]
    assert y_item["properties"]["ky_hieu"]["enum"] == ["a", "b", "c", "d"]


def test_schema_sinh_cau_hoi_tln_dung_cau_truc():
    from app.llm.prompts import schema_sinh_cau_hoi
    s = schema_sinh_cau_hoi("TLN")
    meta = s["properties"]["cau_hoi"]["items"]["properties"]["meta"]
    assert meta["required"] == ["dap_an_cuoi"]


def test_schema_doc_de_tu_anh_theo_loai_ky_vong():
    from app.llm.prompts import schema_doc_de_tu_anh
    s = schema_doc_de_tu_anh("TN4PA")
    assert "phuong_an" in s["properties"]["meta_nhap"]["properties"]
    s2 = schema_doc_de_tu_anh("TNDS")
    assert "y" in s2["properties"]["meta_nhap"]["properties"]


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


# ----- canh_bao_khuon_mau_tnds (v137 — chống nhiễm mẫu few-shot) -----

def _y(a, b, c, d):
    return [
        {"ky_hieu": "a", "noi_dung_y": "x", "dap_an": a},
        {"ky_hieu": "b", "noi_dung_y": "x", "dap_an": b},
        {"ky_hieu": "c", "noi_dung_y": "x", "dap_an": c},
        {"ky_hieu": "d", "noi_dung_y": "x", "dap_an": d},
    ]


def test_canh_bao_khuon_mau_tnds_xen_ke_dung_sai():
    from app.llm.question_gen import canh_bao_khuon_mau_tnds
    cb = canh_bao_khuon_mau_tnds(_y("Dung", "Sai", "Dung", "Sai"))
    assert cb and "khuôn" in cb[0]


def test_canh_bao_khuon_mau_tnds_xen_ke_sai_dung():
    from app.llm.question_gen import canh_bao_khuon_mau_tnds
    cb = canh_bao_khuon_mau_tnds(_y("Sai", "Dung", "Sai", "Dung"))
    assert cb


def test_khong_canh_bao_khi_dap_an_khong_theo_khuon():
    from app.llm.question_gen import canh_bao_khuon_mau_tnds
    assert canh_bao_khuon_mau_tnds(_y("Dung", "Dung", "Dung", "Sai")) == []
    assert canh_bao_khuon_mau_tnds(_y("Sai", "Sai", "Sai", "Sai")) == []
    assert canh_bao_khuon_mau_tnds(_y("Dung", "Dung", "Sai", "Sai")) == []


def test_validate_cau_hoi_tnds_kem_canh_bao_khuon_mau():
    cau = {
        "loai_cau": "TNDS", "de_bai": "Test", "loai_dap_an_nhap": "dung_sai_4y",
        "meta": {"y": _y("Dung", "Sai", "Dung", "Sai")},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": k, "mo_ta": "m", "bieu_thuc_ket_qua": "1",
             "danh_sach_goi_y": ["g"]}
            for k in ("a", "b", "c", "d")
        ],
        "loi_giai_chi_tiet": "giai",
    }
    cb = validate_cau_hoi(cau)
    assert any("khuôn" in c for c in cb)


# ----- canh_bao_cong_thuc_chua_boc_dollar (v139 — AI quên bọc $...$ trong loi_giai_chi_tiet) -----

def test_canh_bao_cong_thuc_ro_ri_frac_ngoai_dollar():
    from app.llm.question_gen import canh_bao_cong_thuc_chua_boc_dollar
    cb = canh_bao_cong_thuc_chua_boc_dollar(r"Hệ số góc m = \frac{y_B - y_A}{x_B - x_A} = 2.")
    assert cb and "$...$" in cb[0]


def test_canh_bao_cong_thuc_ro_ri_dao_ham_ngoai_dollar():
    from app.llm.question_gen import canh_bao_cong_thuc_chua_boc_dollar
    cb = canh_bao_cong_thuc_chua_boc_dollar("Đạo hàm của hàm số là y' = -3x^2 + 6x.")
    assert cb


def test_khong_canh_bao_khi_da_boc_dollar_day_du():
    from app.llm.question_gen import canh_bao_cong_thuc_chua_boc_dollar
    text = r"Đạo hàm của hàm số là $y' = -3x^2 + 6x$. Hệ số góc $m = \frac{y_B - y_A}{x_B - x_A} = 2$."
    assert canh_bao_cong_thuc_chua_boc_dollar(text) == []


def test_khong_canh_bao_khi_khong_co_cong_thuc():
    from app.llm.question_gen import canh_bao_cong_thuc_chua_boc_dollar
    assert canh_bao_cong_thuc_chua_boc_dollar("Ta xét từng mệnh đề rồi kết luận.") == []


def test_khong_canh_bao_khi_rong():
    from app.llm.question_gen import canh_bao_cong_thuc_chua_boc_dollar
    assert canh_bao_cong_thuc_chua_boc_dollar("") == []
    assert canh_bao_cong_thuc_chua_boc_dollar("   ") == []
    assert canh_bao_cong_thuc_chua_boc_dollar(None) == []


def test_validate_cau_hoi_kem_canh_bao_cong_thuc_ro_ri():
    cau = {
        "loai_cau": "TLN", "de_bai": "Test",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "m", "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["g"]},
        ],
        "loi_giai_chi_tiet": "Hệ số góc m = \\frac{y_B - y_A}{x_B - x_A} = 2.",
    }
    cb = validate_cau_hoi(cau)
    assert any("$...$" in c for c in cb)


# ----- canh_bao_dinh_dang_latex_khac (v141 — aligned bị cấm + ký hiệu suy ra trong công thức) --

def test_canh_bao_dung_moi_truong_aligned():
    from app.llm.question_gen import canh_bao_dinh_dang_latex_khac
    cb = canh_bao_dinh_dang_latex_khac(
        r"$\begin{aligned} y' &= 3x^2 - 6x \\ y'(1) &= -3 \end{aligned}$"
    )
    assert cb and "aligned" in cb[0]


def test_canh_bao_ky_hieu_suy_ra_trong_cong_thuc():
    from app.llm.question_gen import canh_bao_dinh_dang_latex_khac
    cb = canh_bao_dinh_dang_latex_khac(r"Ta có $y' = 0 \Rightarrow x = 1$.")
    assert cb and "suy ra" in cb[0].lower()

    cb2 = canh_bao_dinh_dang_latex_khac("Ta có $y' = 0 => x = 1$.")
    assert cb2

    cb3 = canh_bao_dinh_dang_latex_khac("Ta có $y' = 0 ⇒ x = 1$.")
    assert cb3


def test_khong_canh_bao_khi_viet_dung_quy_tac():
    from app.llm.question_gen import canh_bao_dinh_dang_latex_khac
    text = "Ta có $y' = 0$, giải ra $x = 0$ hoặc $x = 2$.\nSuy ra hàm số đạt cực trị tại đó."
    assert canh_bao_dinh_dang_latex_khac(text) == []
    assert canh_bao_dinh_dang_latex_khac("") == []
    assert canh_bao_dinh_dang_latex_khac(None) == []


def test_validate_cau_hoi_kem_canh_bao_dinh_dang_latex_khac():
    cau = {
        "loai_cau": "TLN", "de_bai": "Test",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "m", "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["g"]},
        ],
        "loi_giai_chi_tiet": r"Ta có $y' = 0 \Rightarrow x = 1$.",
    }
    cb = validate_cau_hoi(cau)
    assert any("suy ra" in c.lower() for c in cb)


# ----- Quy tắc LaTeX góc/vectơ/aligned/suy-ra dùng chung (v141) áp cho cả 3 prompt sinh/trích --

def test_prompt_co_du_quy_tac_goc_vecto_aligned_suy_ra():
    """Khóa quy tắc: cả 3 prompt (SINH_CAU_HOI, TAO_BUOC_GOI_Y, DOC_DE_TU_ANH) phải nêu đủ quy
    tắc LaTeX: góc 1 đỉnh $\\widehat{A}$, góc 3 điểm $\\widehat{ABC}$, vectơ 1 chữ $\\vec{u}$,
    vectơ 2 chữ $\\overrightarrow{AB}$, cấm môi trường aligned, cấm ký hiệu suy ra trong công thức."""
    from app.llm import prompts

    for p in (prompts.SYSTEM_SINH_CAU_HOI, prompts.SYSTEM_TAO_BUOC_GOI_Y, prompts.SYSTEM_DOC_DE_TU_ANH):
        assert r"\widehat{A}" in p
        assert r"\widehat{ABC}" in p
        assert r"\vec{u}" in p
        assert r"\overrightarrow{AB}" in p
        assert r"\begin{aligned}" in p
        assert "Suy ra $AB = CD$." in p


# ----- Prompt phải yêu cầu bọc $...$ cho loi_giai_chi_tiet (v139 — chống tái nhiễm bug) -----

def test_prompt_yeu_cau_boc_dollar_cho_loi_giai_chi_tiet():
    """Khóa quy tắc: cả 2 prompt sinh câu hỏi phải nêu rõ "loi_giai_chi_tiet" cần bọc $...$,
    nếu không AI sẽ để lọt công thức trần ra ngoài (nguyên nhân sự cố v139)."""
    from app.llm import prompts

    assert "loi_giai_chi_tiet" in prompts.SYSTEM_SINH_CAU_HOI
    idx = prompts.SYSTEM_SINH_CAU_HOI.index("loi_giai_chi_tiet")
    assert "$...$" in prompts.SYSTEM_SINH_CAU_HOI[max(0, idx - 50):idx + 200]

    assert '"loi_giai_chi_tiet"' in prompts.SYSTEM_TAO_BUOC_GOI_Y
    assert "$...$" in prompts.SYSTEM_TAO_BUOC_GOI_Y
    assert "loi_giai_chi_tiet" in prompts.SYSTEM_TAO_BUOC_GOI_Y.split("ĐỊNH DẠNG CÔNG THỨC")[0][-400:]


# ----- Mẫu prompt KHÔNG được chứa giá trị đáp án thật (chống tái nhiễm few-shot) -----

def test_mau_prompt_khong_chua_dap_an_that():
    """Khóa quy tắc: mẫu ví dụ JSON gửi cho AI không được có giá trị dap_an cụ thể — chỉ được
    dùng placeholder dạng hướng dẫn. Vi phạm quy tắc này chính là nguyên nhân sự cố v137."""
    from app.llm import prompts

    for mau in (prompts._MAU_TN4PA, prompts._MAU_TNDS, prompts._MAU_TLN):
        assert '"dap_an_dung": "A"' not in mau
        assert '"dap_an": "Dung"' not in mau
        assert '"dap_an": "Sai"' not in mau
        assert '"dap_an_cuoi": "5"' not in mau
