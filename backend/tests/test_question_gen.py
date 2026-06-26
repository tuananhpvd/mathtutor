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
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"), lop_id=lop.id)
    db.add_all([gv, hs])
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
