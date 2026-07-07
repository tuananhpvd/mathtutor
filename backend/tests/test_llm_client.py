"""Test get_llm_client(): rơi về StubLLMClient phải LUÔN kèm log cảnh báo rõ nguyên nhân.

Bối cảnh: production từng âm thầm rơi về Stub do thiếu gói google-genai, không ai phát
hiện được vì không có log. Test này khóa hành vi ghi log cho từng nguyên nhân rơi về Stub.
"""

import logging
from unittest.mock import patch

from app.llm.client import AnthropicLLMClient, GeminiLLMClient, StubLLMClient, get_llm_client


def test_thieu_thu_vien_roi_ve_stub_co_log_canh_bao(caplog):
    cau_hinh = {"llm_provider": "gemini", "llm_api_key_gemini": "fake-key"}
    with patch(
        "app.llm.client.GeminiLLMClient.__init__",
        side_effect=ImportError("pip install google-genai để dùng provider gemini"),
    ):
        with caplog.at_level(logging.WARNING):
            llm = get_llm_client(cau_hinh)
    assert isinstance(llm, StubLLMClient)
    assert any("thiếu thư viện" in r.message.lower() for r in caplog.records)
    assert any("gemini" in r.message.lower() for r in caplog.records)


def test_thieu_api_key_roi_ve_stub_co_log_canh_bao(caplog):
    cau_hinh = {"llm_provider": "gemini", "llm_api_key_gemini": ""}
    with caplog.at_level(logging.WARNING):
        llm = get_llm_client(cau_hinh)
    assert isinstance(llm, StubLLMClient)
    assert any("thiếu" in r.message.lower() and "key" in r.message.lower() for r in caplog.records)


def test_provider_khong_ho_tro_roi_ve_stub_co_log_canh_bao(caplog):
    cau_hinh = {"llm_provider": "khong_ton_tai", "llm_api_key_khong_ton_tai": "abc"}
    with caplog.at_level(logging.WARNING):
        llm = get_llm_client(cau_hinh)
    assert isinstance(llm, StubLLMClient)
    assert any("không được hỗ trợ" in r.message.lower() for r in caplog.records)


def test_provider_stub_chu_dinh_khong_bi_coi_la_canh_bao(caplog):
    cau_hinh = {"llm_provider": "stub"}
    with caplog.at_level(logging.WARNING):
        llm = get_llm_client(cau_hinh)
    assert isinstance(llm, StubLLMClient)
    assert not any(r.levelno >= logging.WARNING for r in caplog.records)


def test_gemini_du_dieu_kien_khong_roi_ve_stub():
    cau_hinh = {"llm_provider": "gemini", "llm_api_key_gemini": "fake-key"}
    with patch.object(GeminiLLMClient, "__init__", return_value=None):
        llm = get_llm_client(cau_hinh)
    assert isinstance(llm, GeminiLLMClient)


# ---------- dien_dat/phan_tich luôn tắt "thinking" (tránh cắt cụt câu, sự cố thật gặp) ----------
#
# Bối cảnh: bật "thinking" cho Gemini trong Admin khiến dien_dat() (câu diễn đạt ngắn, max_tokens
# thấp) bị cắt cụt giữa câu vì suy luận nội bộ ăn hết ngân sách token — đã xác nhận bằng gọi
# Gemini thật với đúng config production. Test này khóa lại: dien_dat/phan_tich LUÔN gọi _call
# với suy_nghi=False, bất kể client được khởi tạo với suy_nghi=True (Admin bật "thinking").

def test_gemini_dien_dat_luon_tat_thinking(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = True  # mô phỏng Admin bật "thinking" cho Gemini
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["suy_nghi"] = suy_nghi
        return "cau tra loi day du"

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.dien_dat({"y_dinh": "goi_y", "y_goi_y": "test"})
    assert goi_lai["suy_nghi"] is False


def test_gemini_phan_tich_luon_tat_thinking(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = True
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["suy_nghi"] = suy_nghi
        return '{"cho_hoc_sinh": "a", "cho_giao_vien": "b"}'

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.phan_tich({})
    assert goi_lai["suy_nghi"] is False


def test_anthropic_dien_dat_luon_tat_thinking(monkeypatch):
    llm = AnthropicLLMClient.__new__(AnthropicLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = True
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["suy_nghi"] = suy_nghi
        return "cau tra loi day du"

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.dien_dat({"y_dinh": "goi_y", "y_goi_y": "test"})
    assert goi_lai["suy_nghi"] is False


def test_anthropic_phan_tich_luon_tat_thinking(monkeypatch):
    llm = AnthropicLLMClient.__new__(AnthropicLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = True
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["suy_nghi"] = suy_nghi
        return '{"cho_hoc_sinh": "a", "cho_giao_vien": "b"}'

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.phan_tich({})
    assert goi_lai["suy_nghi"] is False


# ---------- Gemini: model bị khai tử (404)/hết quota (429) phải chuyển model dự phòng ----------
#
# Bối cảnh: "gemini-2.0-flash" (từng nằm trong _DU_PHONG) bị Google khai tử — gọi thật trả 404
# NOT_FOUND, nhưng code cũ chỉ coi 429 là "thử model khác", các mã 4xx khác (gồm 404) bị raise
# ngay không thử model dự phòng — khiến cả 3 lần thử lại đều lỗi y hệt. Test khóa hành vi mới:
# cả 404 và 429 đều chuyển sang model kế tiếp trong self._models.

def _gia_client_error(code):
    from google.genai import errors
    return errors.ClientError(code, {"error": {"code": code, "message": "gia lap"}})


def test_gemini_404_chuyen_sang_model_du_phong(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    llm._models = ["model-bi-khai-tu", "model-du-phong"]
    goi_lai = []

    class _FakeModels:
        def generate_content(self, model, contents, config):
            goi_lai.append(model)
            if model == "model-bi-khai-tu":
                raise _gia_client_error(404)
            return type("R", (), {"text": "cau tra loi tu model du phong"})()

    llm._client = type("C", (), {"models": _FakeModels()})()
    ket = llm._call("system", "user")
    assert ket == "cau tra loi tu model du phong"
    assert goi_lai == ["model-bi-khai-tu", "model-du-phong"]


def test_gemini_429_van_chuyen_sang_model_du_phong(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    llm._models = ["model-het-quota", "model-du-phong"]
    goi_lai = []

    class _FakeModels:
        def generate_content(self, model, contents, config):
            goi_lai.append(model)
            if model == "model-het-quota":
                raise _gia_client_error(429)
            return type("R", (), {"text": "ok"})()

    llm._client = type("C", (), {"models": _FakeModels()})()
    llm._call("system", "user")
    assert goi_lai == ["model-het-quota", "model-du-phong"]


def test_gemini_400_khong_thu_model_khac():
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    llm._models = ["model-a", "model-b"]
    goi_lai = []

    class _FakeModels:
        def generate_content(self, model, contents, config):
            goi_lai.append(model)
            raise _gia_client_error(400)

    llm._client = type("C", (), {"models": _FakeModels()})()
    try:
        llm._call("system", "user")
        raised = False
    except Exception:
        raised = True
    assert raised
    assert goi_lai == ["model-a"]  # KHÔNG thử model-b vì 400 không liên quan tới model


def test_gemini_khong_con_model_khai_tu_trong_danh_sach_du_phong():
    assert "gemini-2.0-flash" not in GeminiLLMClient._DU_PHONG
