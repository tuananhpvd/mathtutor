"""Tests — "AI tạo bước và gợi ý từ hình ảnh": đọc ảnh GV dán, nhận dạng loại câu,
trích đề bài/phương án/ý (chưa giải, chưa lưu)."""

import base64

import pytest

from app.auth.security import hash_password
from app.llm.client import (
    GeminiLLMClient,
    KhongHoTroDocAnhError,
    LLMClient,
    StubLLMClient,
    _parse_json_doc_de_tu_anh,
)
from app.models.user import User, VaiTro
from app.services.question_gen_service import doc_de_tu_anh

# PNG 1x1 hợp lệ nhỏ nhất, dùng chung cho mọi test cần "ảnh thật".
_PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _login(client, dang_nhap):
    return client.post("/api/auth/login",
                       json={"dang_nhap": dang_nhap, "mat_khau": "password"}).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


class _LLMFakeAnh(LLMClient):
    """Test double: trả kết quả cố định cho doc_de_tu_anh, các phương thức khác không dùng tới."""

    def __init__(self, ket_qua=None, loi=None):
        self._ket_qua = ket_qua
        self._loi = loi

    def dien_dat(self, chi_thi):
        return ""

    def sinh_cau_hoi(self, yeu_cau):
        return {"cau_hoi": []}

    def tao_buoc_goi_y(self, yeu_cau):
        return {"cau_hoi": []}

    def doc_de_tu_anh(self, anh_bytes, mime_type, loai_cau_ky_vong):
        if self._loi:
            raise self._loi
        self.anh_bytes_nhan = anh_bytes  # để test kiểm tra đúng bytes đã giải mã
        self.mime_type_nhan = mime_type
        return self._ket_qua


# ---------- question_gen_service.doc_de_tu_anh (validate + giải mã) ----------

def test_doc_de_tu_anh_loai_cau_khong_hop_le():
    llm = _LLMFakeAnh()
    with pytest.raises(ValueError, match="loai_cau_ky_vong"):
        doc_de_tu_anh(llm, _PNG_1X1, "image/png", "SAI_LOAI")


def test_doc_de_tu_anh_mime_khong_ho_tro():
    llm = _LLMFakeAnh()
    with pytest.raises(ValueError, match="không được hỗ trợ"):
        doc_de_tu_anh(llm, _PNG_1X1, "image/gif", "TLN")


def test_doc_de_tu_anh_base64_khong_hop_le():
    llm = _LLMFakeAnh()
    with pytest.raises(ValueError, match="không hợp lệ"):
        doc_de_tu_anh(llm, "!!!khong-phai-base64!!!", "image/png", "TLN")


def test_doc_de_tu_anh_rong():
    llm = _LLMFakeAnh()
    with pytest.raises(ValueError, match="rỗng"):
        doc_de_tu_anh(llm, "", "image/png", "TLN")


def test_doc_de_tu_anh_qua_lon():
    llm = _LLMFakeAnh()
    anh_lon = base64.b64encode(b"0" * (5 * 1024 * 1024 + 1)).decode()
    with pytest.raises(ValueError, match="quá lớn"):
        doc_de_tu_anh(llm, anh_lon, "image/png", "TLN")


def test_doc_de_tu_anh_bo_tien_to_data_url():
    llm = _LLMFakeAnh(ket_qua={"khop_loai_cau": True, "de_bai": "ok"})
    doc_de_tu_anh(llm, f"data:image/png;base64,{_PNG_1X1}", "image/png", "TLN")
    assert llm.anh_bytes_nhan == base64.b64decode(_PNG_1X1)
    assert llm.mime_type_nhan == "image/png"


def test_doc_de_tu_anh_thanh_cong_tra_dung_ket_qua():
    ket_qua_mau = {
        "khop_loai_cau": True, "loai_cau_nhan_dang": "TLN",
        "de_bai": "Tính $x+1$", "meta_nhap": {}, "ly_do_khong_khop": None,
    }
    llm = _LLMFakeAnh(ket_qua=ket_qua_mau)
    ket_qua = doc_de_tu_anh(llm, _PNG_1X1, "image/png", "TLN")
    assert ket_qua == ket_qua_mau


# ---------- LLMClient mặc định: provider không hỗ trợ đọc ảnh ----------

def test_stub_khong_ho_tro_doc_anh_bao_loi_ro():
    llm = StubLLMClient()
    with pytest.raises(KhongHoTroDocAnhError, match="chưa hỗ trợ"):
        llm.doc_de_tu_anh(base64.b64decode(_PNG_1X1), "image/png", "TLN")


# ---------- client._parse_json_doc_de_tu_anh (parse JSON) ----------

def test_parse_json_doc_de_tu_anh_hop_le():
    raw = '{"khop_loai_cau": true, "loai_cau_nhan_dang": "TLN", "de_bai": "abc", "meta_nhap": {}, "ly_do_khong_khop": null}'
    ket = _parse_json_doc_de_tu_anh(raw)
    assert ket["khop_loai_cau"] is True
    assert ket["de_bai"] == "abc"


def test_parse_json_doc_de_tu_anh_co_rao_markdown():
    raw = '```json\n{"khop_loai_cau": false, "loai_cau_nhan_dang": "TNDS", "ly_do_khong_khop": "lech"}\n```'
    ket = _parse_json_doc_de_tu_anh(raw)
    assert ket["khop_loai_cau"] is False
    assert ket["loai_cau_nhan_dang"] == "TNDS"
    assert ket["ly_do_khong_khop"] == "lech"


def test_parse_json_doc_de_tu_anh_thieu_khoa_bat_buoc():
    with pytest.raises(ValueError, match="khop_loai_cau"):
        _parse_json_doc_de_tu_anh('{"de_bai": "abc"}')


# ---------- GeminiLLMClient.doc_de_tu_anh (mock _call_voi_anh, không gọi mạng thật) ----------

def test_gemini_doc_de_tu_anh_goi_dung_va_parse(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)  # bỏ qua __init__ (không cần API key thật)
    goi_lai = {}

    def _fake_call_voi_anh(system, user, anh_bytes, mime_type, max_tokens=4096,
                            response_schema=None):
        goi_lai["mime_type"] = mime_type
        goi_lai["anh_bytes"] = anh_bytes
        goi_lai["response_schema"] = response_schema
        return '{"khop_loai_cau": true, "loai_cau_nhan_dang": "TN4PA", "de_bai": "Tính y\'", "meta_nhap": {"phuong_an": {"A": "1", "B": "2", "C": "3", "D": "4"}}, "ly_do_khong_khop": null}'

    monkeypatch.setattr(llm, "_call_voi_anh", _fake_call_voi_anh)
    anh_bytes = base64.b64decode(_PNG_1X1)
    ket = llm.doc_de_tu_anh(anh_bytes, "image/png", "TN4PA")
    assert ket["khop_loai_cau"] is True
    assert ket["meta_nhap"]["phuong_an"]["A"] == "1"
    assert goi_lai["mime_type"] == "image/png"
    assert goi_lai["anh_bytes"] == anh_bytes
    # Structured Output: schema JSON được truyền để Gemini không tự viết JSON tay nữa
    # (loại tận gốc nhóm lỗi "JSON không hợp lệ" thay vì vá regex sau khi nhận về).
    assert goi_lai["response_schema"] is not None
    assert goi_lai["response_schema"]["required"] == [
        "khop_loai_cau", "loai_cau_nhan_dang", "de_bai", "meta_nhap",
    ]


# ---------- API /questions-ai/doc-de-tu-anh (E2E, dùng Stub mặc định trong test) ----------

def _seed_gv_hs(db):
    gv = User(vai_tro=VaiTro.gv, ho_ten="GV Anh", dang_nhap="gv_anh",
              mat_khau_hash=hash_password("password"))
    hs = User(vai_tro=VaiTro.hs, ho_ten="HS Anh", dang_nhap="hs_anh",
              mat_khau_hash=hash_password("password"))
    db.add_all([gv, hs])
    db.commit()
    return gv, hs


def test_api_provider_mac_dinh_stub_bao_chua_ho_tro(db, client):
    _seed_gv_hs(db)
    tok = _login(client, "gv_anh")
    r = client.post("/api/questions-ai/doc-de-tu-anh", headers=_h(tok), json={
        "anh_base64": _PNG_1X1, "mime_type": "image/png", "loai_cau_ky_vong": "TLN",
    })
    assert r.status_code == 400
    assert "chưa hỗ trợ" in r.json()["detail"]


def test_api_hs_khong_dung_duoc(db, client):
    _seed_gv_hs(db)
    tok = _login(client, "hs_anh")
    r = client.post("/api/questions-ai/doc-de-tu-anh", headers=_h(tok), json={
        "anh_base64": _PNG_1X1, "mime_type": "image/png", "loai_cau_ky_vong": "TLN",
    })
    assert r.status_code == 403


def test_api_mime_khong_hop_le_tra_400(db, client):
    _seed_gv_hs(db)
    tok = _login(client, "gv_anh")
    r = client.post("/api/questions-ai/doc-de-tu-anh", headers=_h(tok), json={
        "anh_base64": _PNG_1X1, "mime_type": "image/gif", "loai_cau_ky_vong": "TLN",
    })
    assert r.status_code == 400


def test_api_payload_khong_lo_bi_chan_o_tang_request(db, client):
    """Chặn NGOÀI (Pydantic max_length) — không để payload khổng lồ tốn RAM giải mã
    trước khi tới được ngưỡng nghiệp vụ 5MB ở tầng service."""
    _seed_gv_hs(db)
    tok = _login(client, "gv_anh")
    r = client.post("/api/questions-ai/doc-de-tu-anh", headers=_h(tok), json={
        "anh_base64": "A" * 10_000_001, "mime_type": "image/png", "loai_cau_ky_vong": "TLN",
    })
    assert r.status_code == 422


def test_api_loai_cau_ky_vong_khong_hop_le_tra_400(db, client):
    _seed_gv_hs(db)
    tok = _login(client, "gv_anh")
    r = client.post("/api/questions-ai/doc-de-tu-anh", headers=_h(tok), json={
        "anh_base64": _PNG_1X1, "mime_type": "image/png", "loai_cau_ky_vong": "SAI",
    })
    assert r.status_code == 400
