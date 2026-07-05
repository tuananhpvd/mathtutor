"""Tests B4 — phanh chi phí LLM (đếm lượt + giới hạn theo ngày)."""

from app.auth.security import hash_password
from app.llm.client import LLMClient, StubLLMClient
from app.models.user import User, VaiTro
from app.services.llm_quota_service import (
    LOAI_HOI_THOAI,
    LOAI_PHAN_TICH,
    LOAI_SINH_CAU_HOI,
    ap_quota_hoi_thoai,
    ap_quota_tac_vu,
    ghi_luot,
    thong_ke_su_dung,
    tong_hom_nay,
    vuot_nguong_he_thong,
    vuot_nguong_hs,
)


class _LLMGia(LLMClient):
    """LLM giả KHÔNG phải stub — để kiểm tra logic quota với 'LLM thật'."""

    def dien_dat(self, chi_thi):
        return "llm-that"

    def sinh_cau_hoi(self, yeu_cau):
        return {}

    def tao_buoc_goi_y(self, yeu_cau):
        return {"cau_hoi": [{}]}

    def phan_tich(self, ho_so):
        return None


def _login(client, dn):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dn, "mat_khau": "password"}).json()["access_token"]


def _seed(db):
    admin = User(vai_tro=VaiTro.admin, ho_ten="Quản trị", dang_nhap="admin",
                 mat_khau_hash=hash_password("password"))
    gv = User(vai_tro=VaiTro.gv, ho_ten="Cô Lan", dang_nhap="gv1",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS A", dang_nhap="hs1",
              mat_khau_hash=hash_password("password"))
    db.add_all([admin, gv, hs])
    db.commit()
    return admin, gv, hs


# ---------- Đếm lượt ----------

def test_ghi_luot_cong_don(db):
    ghi_luot(db, 1, LOAI_HOI_THOAI)
    ghi_luot(db, 1, LOAI_HOI_THOAI)
    ghi_luot(db, 2, LOAI_HOI_THOAI)
    ghi_luot(db, 1, LOAI_SINH_CAU_HOI, so=3)
    assert tong_hom_nay(db) == 6
    assert tong_hom_nay(db, user_id=1) == 5
    assert tong_hom_nay(db, user_id=1, loai=LOAI_HOI_THOAI) == 2
    assert tong_hom_nay(db, loai=LOAI_SINH_CAU_HOI) == 3


def test_ghi_luot_so_khong_duong_bo_qua(db):
    ghi_luot(db, 1, LOAI_PHAN_TICH, so=0)
    ghi_luot(db, 1, LOAI_PHAN_TICH, so=-2)
    assert tong_hom_nay(db) == 0


# ---------- Ngưỡng ----------

def test_vuot_nguong_hs_va_he_thong(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": 2, "gioi_han_llm_he_thong_ngay": 5}
    assert not vuot_nguong_hs(db, cau_hinh, 1)
    ghi_luot(db, 1, LOAI_HOI_THOAI, so=2)
    assert vuot_nguong_hs(db, cau_hinh, 1)
    assert not vuot_nguong_hs(db, cau_hinh, 2)  # HS khác chưa dùng
    assert not vuot_nguong_he_thong(db, cau_hinh)
    ghi_luot(db, None, LOAI_PHAN_TICH, so=3)
    assert vuot_nguong_he_thong(db, cau_hinh)


def test_gioi_han_0_la_khong_gioi_han(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": 0, "gioi_han_llm_he_thong_ngay": 0}
    ghi_luot(db, 1, LOAI_HOI_THOAI, so=99999)
    assert not vuot_nguong_hs(db, cau_hinh, 1)
    assert not vuot_nguong_he_thong(db, cau_hinh)


def test_gioi_han_gia_tri_rac_coi_nhu_khong_gioi_han(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": "abc", "gioi_han_llm_he_thong_ngay": None}
    ghi_luot(db, 1, LOAI_HOI_THOAI, so=100)
    assert not vuot_nguong_hs(db, cau_hinh, 1)
    assert not vuot_nguong_he_thong(db, cau_hinh)


# ---------- Áp quota hội thoại ----------

def test_hoi_thoai_stub_khong_dem_khong_gioi_han(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": 1, "gioi_han_llm_he_thong_ngay": 1}
    stub = StubLLMClient()
    ket = ap_quota_hoi_thoai(db, cau_hinh, 1, stub)
    assert ket is stub
    assert tong_hom_nay(db) == 0  # stub không tính lượt


def test_hoi_thoai_llm_that_dem_va_thay_stub_khi_vuot(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": 2, "gioi_han_llm_he_thong_ngay": 100}
    llm = _LLMGia()
    # 2 lượt đầu: dùng LLM thật, mỗi lượt đếm 1
    assert ap_quota_hoi_thoai(db, cau_hinh, 1, llm) is llm
    assert ap_quota_hoi_thoai(db, cau_hinh, 1, llm) is llm
    assert tong_hom_nay(db, user_id=1, loai=LOAI_HOI_THOAI) == 2
    # Lượt 3: vượt ngưỡng HS → trả stub, KHÔNG đếm thêm
    ket = ap_quota_hoi_thoai(db, cau_hinh, 1, llm)
    assert isinstance(ket, StubLLMClient)
    assert tong_hom_nay(db, user_id=1, loai=LOAI_HOI_THOAI) == 2
    # HS khác vẫn dùng LLM thật bình thường
    assert ap_quota_hoi_thoai(db, cau_hinh, 2, llm) is llm


def test_hoi_thoai_vuot_nguong_he_thong_cung_thay_stub(db):
    cau_hinh = {"gioi_han_llm_hs_ngay": 0, "gioi_han_llm_he_thong_ngay": 3}
    ghi_luot(db, 99, LOAI_SINH_CAU_HOI, so=3)  # nguồn khác đã ăn hết quota hệ thống
    ket = ap_quota_hoi_thoai(db, cau_hinh, 1, _LLMGia())
    assert isinstance(ket, StubLLMClient)


# ---------- Áp quota tác vụ (sinh câu hỏi / phân tích) ----------

def test_tac_vu_vuot_nguong_tra_none(db):
    cau_hinh = {"gioi_han_llm_he_thong_ngay": 2}
    llm = _LLMGia()
    assert ap_quota_tac_vu(db, cau_hinh, 5, llm, LOAI_SINH_CAU_HOI) is llm
    assert ap_quota_tac_vu(db, cau_hinh, 5, llm, LOAI_SINH_CAU_HOI) is llm
    assert ap_quota_tac_vu(db, cau_hinh, 5, llm, LOAI_SINH_CAU_HOI) is None
    assert tong_hom_nay(db, loai=LOAI_SINH_CAU_HOI) == 2


def test_tac_vu_stub_di_qua_khong_dem(db):
    cau_hinh = {"gioi_han_llm_he_thong_ngay": 1}
    stub = StubLLMClient()
    assert ap_quota_tac_vu(db, cau_hinh, 5, stub, LOAI_PHAN_TICH) is stub
    assert tong_hom_nay(db) == 0


# ---------- API ----------

def test_endpoint_llm_su_dung_chi_admin(db, client):
    _seed(db)
    h_admin = {"Authorization": f"Bearer {_login(client, 'admin')}"}
    h_hs = {"Authorization": f"Bearer {_login(client, 'hs1')}"}

    r = client.get("/api/admin/llm-su-dung", headers=h_hs)
    assert r.status_code == 403

    ghi_luot(db, 1, LOAI_HOI_THOAI, so=4)
    r = client.get("/api/admin/llm-su-dung", headers=h_admin)
    assert r.status_code == 200
    data = r.json()
    assert data["tong"] == 4
    assert data["theo_loai"][LOAI_HOI_THOAI] == 4
    assert data["gioi_han_hs_ngay"] == 30       # mặc định
    assert data["gioi_han_he_thong_ngay"] == 500


def test_sinh_cau_hoi_429_khi_het_quota(db, client, monkeypatch):
    """Provider thật + quota hệ thống đã cạn → /questions-ai/generate trả 429 rõ ràng."""
    import app.api.questions_ai as qa

    _seed(db)
    monkeypatch.setattr(qa, "get_llm_client", lambda cau_hinh: _LLMGia())
    from app.services.admin_service import dat_cau_hinh
    dat_cau_hinh(db, "gioi_han_llm_he_thong_ngay", 1)
    ghi_luot(db, None, LOAI_HOI_THOAI, so=1)

    h_gv = {"Authorization": f"Bearer {_login(client, 'gv1')}"}
    r = client.post("/api/questions-ai/generate", headers=h_gv,
                    json={"loai_cau": "TLN", "chuyen_de": "Đạo hàm", "do_kho": "de", "so_luong": 1})
    assert r.status_code == 429
    assert "hạn mức" in r.json()["detail"]


def test_thong_ke_su_dung_du_truong(db):
    ket = thong_ke_su_dung(db, {"gioi_han_llm_hs_ngay": 10, "gioi_han_llm_he_thong_ngay": 20})
    assert ket["tong"] == 0
    assert set(ket["theo_loai"]) == {LOAI_HOI_THOAI, LOAI_SINH_CAU_HOI, LOAI_PHAN_TICH}
    assert ket["gioi_han_hs_ngay"] == 10
    assert ket["gioi_han_he_thong_ngay"] == 20
