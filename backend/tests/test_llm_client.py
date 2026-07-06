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
