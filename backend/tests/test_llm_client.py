"""Test get_llm_client(): rơi về StubLLMClient phải LUÔN kèm log cảnh báo rõ nguyên nhân.

Bối cảnh: production từng âm thầm rơi về Stub do thiếu gói google-genai, không ai phát
hiện được vì không có log. Test này khóa hành vi ghi log cho từng nguyên nhân rơi về Stub.
"""

import logging
from unittest.mock import patch

from app.llm.client import GeminiLLMClient, StubLLMClient, get_llm_client


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
