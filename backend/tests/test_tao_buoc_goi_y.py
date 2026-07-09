"""Tests — "AI tạo bước và gợi ý": GV viết đề bài sẵn, AI CHỈ giải + chia bước + viết gợi ý."""

from app.auth.security import hash_password
from app.llm.client import StubLLMClient
from app.llm.question_gen import sinh_buoc_goi_y
from app.models.danh_muc import ChuyenDe, Dang
from app.models.problem import Nguon, Problem, TrangThaiDuyet
from app.models.user import User, VaiTro
from app.services.question_gen_service import luu_cau_nhap, tao_nhap_buoc_goi_y


def _login(client, dang_nhap):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dang_nhap, "mat_khau": "password"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV", dang_nhap="gv_bg",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS", dang_nhap="hs_bg",
              mat_khau_hash=hash_password("password"))
    db.add_all([gv, hs])
    db.flush()
    cd = ChuyenDe(ten="Tổ hợp - Xác suất", nguoi_tao_id=gv.id)
    db.add(cd)
    db.flush()
    dang = Dang(chuyen_de_id=cd.id, ten="Xác suất cổ điển", nguoi_tao_id=gv.id)
    db.add(dang)
    db.commit()
    return gv, hs, dang


def _yc_tln(dang_id, so_buoc=2):
    return {
        "dang_id": dang_id, "loai_cau": "TLN", "do_kho": "tb",
        "de_bai": "Một hộp có 5 bi đỏ, 3 bi xanh. Lấy ngẫu nhiên 2 bi. Tính xác suất lấy được 2 bi đỏ.",
        "meta_nhap": {},
        "cau_truc_buoc": [{"pham_vi": "ca_bai", "so_goi_y": i + 2} for i in range(so_buoc)],
    }


def _yc_tn4pa(dang_id):
    return {
        "dang_id": dang_id, "loai_cau": "TN4PA", "do_kho": "kho",
        "de_bai": "Hàm số $y=x^3-3x+2$ đồng biến trên khoảng nào?",
        "meta_nhap": {"phuong_an": {"A": "$(-1;1)$", "B": "$(1;+\\infty)$",
                                     "C": "$(-\\infty;0)$", "D": "$(0;2)$"}},
        "cau_truc_buoc": [{"pham_vi": "ca_bai", "so_goi_y": 3}],
    }


def _yc_tnds(dang_id):
    return {
        "dang_id": dang_id, "loai_cau": "TNDS", "do_kho": "tb",
        "de_bai": "Cho $f(x)=2\\cos x + x$. Xét đúng/sai các mệnh đề.",
        "meta_nhap": {"y": [
            {"ky_hieu": "a", "noi_dung_y": "$f(0)=2$"},
            {"ky_hieu": "b", "noi_dung_y": "$f'(x)=-2\\sin x+1$"},
            {"ky_hieu": "c", "noi_dung_y": "Nghiệm $f'(x)=0$ là $\\pi/6$"},
            {"ky_hieu": "d", "noi_dung_y": "GTLN trên $[0;\\pi/2]$ là $2$"},
        ]},
        "cau_truc_buoc": [
            {"pham_vi": "a", "so_goi_y": 1}, {"pham_vi": "b", "so_goi_y": 2},
            {"pham_vi": "c", "so_goi_y": 3}, {"pham_vi": "d", "so_goi_y": 2},
        ],
    }


# ---------- question_gen.sinh_buoc_goi_y (đơn vị, dùng StubLLMClient) ----------

def test_sinh_buoc_giu_nguyen_de_bai_va_dung_cau_truc():
    llm = StubLLMClient()
    yc = _yc_tln(dang_id=1, so_buoc=3)
    ket = sinh_buoc_goi_y(llm, yc)
    cau, canh_bao = ket["cau"], ket["canh_bao"]
    assert cau["de_bai"] == yc["de_bai"]  # giữ NGUYÊN VĂN đề GV viết, không đổi
    assert len(cau["solution_steps"]) == 3
    assert [len(s["danh_sach_goi_y"]) for s in cau["solution_steps"]] == [2, 3, 4]
    assert canh_bao == []  # đúng cấu trúc yêu cầu → không cảnh báo


def test_sinh_buoc_tn4pa_giu_nguyen_phuong_an_gv_viet():
    llm = StubLLMClient()
    yc = _yc_tn4pa(dang_id=1)
    ket = sinh_buoc_goi_y(llm, yc)
    cau = ket["cau"]
    assert cau["meta"]["phuong_an"] == yc["meta_nhap"]["phuong_an"]
    assert cau["meta"]["dap_an_dung"] in {"A", "B", "C", "D"}
    assert ket["canh_bao"] == []


def test_sinh_buoc_tnds_giu_nguyen_noi_dung_y_gv_viet():
    llm = StubLLMClient()
    yc = _yc_tnds(dang_id=1)
    ket = sinh_buoc_goi_y(llm, yc)
    cau = ket["cau"]
    noi_dung_theo_ky_hieu = {y["ky_hieu"]: y["noi_dung_y"] for y in cau["meta"]["y"]}
    for y_gv in yc["meta_nhap"]["y"]:
        assert noi_dung_theo_ky_hieu[y_gv["ky_hieu"]] == y_gv["noi_dung_y"]
    assert len(cau["solution_steps"]) == 4
    assert [s["pham_vi"] for s in cau["solution_steps"]] == ["a", "b", "c", "d"]
    assert [len(s["danh_sach_goi_y"]) for s in cau["solution_steps"]] == [1, 2, 3, 2]
    assert ket["canh_bao"] == []


def test_sinh_buoc_canh_bao_khi_lech_so_buoc_hoac_so_goi_y():
    class _LLMLech(StubLLMClient):
        def tao_buoc_goi_y(self, yeu_cau):
            ket = super().tao_buoc_goi_y(yeu_cau)
            # Cắt bớt 1 gợi ý của bước đầu so với yêu cầu (2 → 1).
            ket["cau_hoi"][0]["solution_steps"][0]["danh_sach_goi_y"] = ["chỉ 1 gợi ý"]
            return ket

    ket = sinh_buoc_goi_y(_LLMLech(), _yc_tln(dang_id=1, so_buoc=2))
    assert any("Số gợi ý AI viết cho bước 1" in c for c in ket["canh_bao"])


def test_sinh_buoc_canh_bao_khi_ai_khong_tra_cau_hoi():
    class _LLMRong(StubLLMClient):
        def tao_buoc_goi_y(self, yeu_cau):
            return {"cau_hoi": []}

    try:
        sinh_buoc_goi_y(_LLMRong(), _yc_tln(dang_id=1))
        assert False, "phải ném ValueError"
    except ValueError:
        pass


# ---------- question_gen_service ----------

def test_tao_nhap_gan_dang_va_chuyen_de_dung(db):
    gv, hs, dang = _seed(db)
    ket = tao_nhap_buoc_goi_y(db, _yc_tln(dang.id), StubLLMClient())
    assert ket["cau"]["dang_id"] == dang.id
    assert ket["cau"]["chuyen_de"] == "Tổ hợp - Xác suất"
    # CHƯA lưu DB — bản nháp thuần túy
    assert db.query(Problem).count() == 0


def test_tao_nhap_khong_tim_thay_dang(db):
    gv, hs, dang = _seed(db)
    try:
        tao_nhap_buoc_goi_y(db, _yc_tln(dang_id=99999), StubLLMClient())
        assert False, "phải ném ValueError"
    except ValueError as e:
        assert "dạng" in str(e)


def test_tao_nhap_tnds_sai_cau_truc_bi_chan(db):
    gv, hs, dang = _seed(db)
    yc = _yc_tnds(dang.id)
    yc["cau_truc_buoc"] = yc["cau_truc_buoc"][:3]  # thiếu ý d
    try:
        tao_nhap_buoc_goi_y(db, yc, StubLLMClient())
        assert False, "phải ném ValueError"
    except ValueError as e:
        assert "4 bước" in str(e) or "a, b, c, d" in str(e)


def test_tao_nhap_tn4pa_pham_vi_khac_ca_bai_bi_chan(db):
    gv, hs, dang = _seed(db)
    yc = _yc_tn4pa(dang.id)
    yc["cau_truc_buoc"] = [{"pham_vi": "a", "so_goi_y": 2}]
    try:
        tao_nhap_buoc_goi_y(db, yc, StubLLMClient())
        assert False, "phải ném ValueError"
    except ValueError as e:
        assert "ca_bai" in str(e)


def test_luu_cau_nhap_dung_trang_thai_va_nguon(db):
    gv, hs, dang = _seed(db)
    ket = tao_nhap_buoc_goi_y(db, _yc_tln(dang.id), StubLLMClient())
    problem = luu_cau_nhap(db, ket["cau"], gv.id)
    assert problem.trang_thai_duyet == TrangThaiDuyet.cho_duyet
    assert problem.nguon == Nguon.ai_sinh
    assert problem.nguoi_tao_id == gv.id
    assert problem.dang_id == dang.id
    assert len(problem.solution_steps) == 2
    # AI tự sinh loi_giai_chi_tiet trong bản nháp — GV sửa rồi lưu; hien mặc định vẫn False.
    assert problem.loi_giai_chi_tiet.strip() != ""
    assert problem.hien_loi_giai_chi_tiet is False


# ---------- API end-to-end ----------

def test_api_tao_buoc_goi_y_khong_luu_db(db, client):
    gv, hs, dang = _seed(db)
    h = _h(_login(client, "gv_bg"))
    r = client.post("/api/questions-ai/tao-buoc-goi-y", headers=h, json=_yc_tln(dang.id))
    assert r.status_code == 200, r.text
    data = r.json()
    assert "cau" in data and "canh_bao" in data
    assert db.query(Problem).count() == 0  # chưa lưu


def test_api_luu_buoc_goi_y_thanh_cong(db, client):
    gv, hs, dang = _seed(db)
    h = _h(_login(client, "gv_bg"))
    nhap = client.post("/api/questions-ai/tao-buoc-goi-y", headers=h,
                       json=_yc_tn4pa(dang.id)).json()
    r = client.post("/api/questions-ai/tao-buoc-goi-y/luu", headers=h,
                    json={"cau": nhap["cau"]})
    assert r.status_code == 200, r.text
    assert r.json()["trang_thai_duyet"] == "cho_duyet"
    p = db.get(Problem, r.json()["id"])
    assert p.nguon == Nguon.ai_sinh
    assert p.loai_cau.value == "TN4PA"


def test_api_hs_khong_dung_duoc(db, client):
    gv, hs, dang = _seed(db)
    h = _h(_login(client, "hs_bg"))
    r = client.post("/api/questions-ai/tao-buoc-goi-y", headers=h, json=_yc_tln(dang.id))
    assert r.status_code == 403


def test_api_loai_cau_khong_hop_le(db, client):
    gv, hs, dang = _seed(db)
    h = _h(_login(client, "gv_bg"))
    yc = _yc_tln(dang.id)
    yc["loai_cau"] = "TN5PA"
    r = client.post("/api/questions-ai/tao-buoc-goi-y", headers=h, json=yc)
    assert r.status_code == 400


def test_api_cau_truc_sai_tra_400(db, client):
    gv, hs, dang = _seed(db)
    h = _h(_login(client, "gv_bg"))
    yc = _yc_tnds(dang.id)
    yc["cau_truc_buoc"] = yc["cau_truc_buoc"][:2]  # thiếu ý c, d
    r = client.post("/api/questions-ai/tao-buoc-goi-y", headers=h, json=yc)
    assert r.status_code == 400
