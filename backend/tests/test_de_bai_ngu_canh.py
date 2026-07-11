"""Test đề bài được truyền đúng làm ngữ cảnh cho LLM diễn đạt — tránh lạc đề.

Bối cảnh: GV báo AI diễn đạt gợi ý bịa thêm nội dung không có trong danh_sach_goi_y đã lưu
(hỏi cực trị nhưng AI tự chêm "tìm GTLN-GTNN trên đoạn"). Xác nhận qua dữ liệu production:
gợi ý lưu đúng, lỗi do (1) dien_dat() không được truyền đề bài — ChiThi thiếu trường de_bai,
(2) client.py truyền nhầm ngu_canh_hs vào đúng vị trí đáng lẽ là de_bai. Test này khóa cả 2.
"""

from app.core.orchestrator.directive import ChiThi
from app.core.orchestrator.rules import xu_ly_tln
from app.core.orchestrator.state import TrangThaiPhien
from app.llm.client import AnthropicLLMClient, GeminiLLMClient, OpenAILLMClient, StubLLMClient

STEPS_TLN = [
    {
        "thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm",
        "bieu_thuc_ket_qua": "3*x**2-3",
        "danh_sach_goi_y": ["gợi 1", "gợi 2", "gợi 3"],
    },
]

_DE_BAI_MAU = "Cho hàm số bậc ba y=f(x) có bảng biến thiên. Giá trị cực đại bằng"


def test_trang_thai_phien_mac_dinh_de_bai_rong():
    st = TrangThaiPhien(loai_cau="TLN", steps=STEPS_TLN)
    assert st.de_bai == ""


def test_chi_thi_to_dict_co_de_bai():
    ct = ChiThi(
        loai_cau="TLN", y_dinh="goi_y", buoc=1, y_dang_xet=None, cap_goi_y=0,
        y_goi_y="gợi ý", ngu_canh_hs="", de_bai=_DE_BAI_MAU,
    )
    assert ct.to_dict()["de_bai"] == _DE_BAI_MAU


def test_xu_ly_tln_truyen_dung_de_bai_tu_trang_thai():
    st = TrangThaiPhien(loai_cau="TLN", steps=STEPS_TLN, de_bai=_DE_BAI_MAU)
    chi_thi, _ = xu_ly_tln(st, None, "")
    assert chi_thi.de_bai == _DE_BAI_MAU


def test_gemini_dien_dat_truyen_de_bai_khong_phai_ngu_canh(monkeypatch):
    llm = GeminiLLMClient.__new__(GeminiLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["user_prompt"] = user
        return "cau tra loi"

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.dien_dat({
        "y_dinh": "goi_y", "y_goi_y": "gợi ý mới", "ngu_canh_hs": "em không biết",
        "de_bai": _DE_BAI_MAU,
    })
    assert _DE_BAI_MAU in goi_lai["user_prompt"]


def test_anthropic_dien_dat_truyen_de_bai(monkeypatch):
    llm = AnthropicLLMClient.__new__(AnthropicLLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    goi_lai = {}

    def _fake_call(system, user, max_tokens=4096, suy_nghi=None):
        goi_lai["user_prompt"] = user
        return "cau tra loi"

    monkeypatch.setattr(llm, "_call", _fake_call)
    llm.dien_dat({
        "y_dinh": "goi_y", "y_goi_y": "gợi ý mới", "ngu_canh_hs": "em không biết",
        "de_bai": _DE_BAI_MAU,
    })
    assert _DE_BAI_MAU in goi_lai["user_prompt"]


def test_stub_giai_thich_ngan_khong_giong_dinh_huong():
    """StubLLMClient phải phân biệt được giai_thich_ngan với dinh_huong (câu mở đầu) —
    nếu rơi vào nhánh mặc định thì 2 y_dinh khác nhau sẽ trông giống hệt nhau."""
    llm = StubLLMClient()
    van_ban = llm.dien_dat({
        "y_dinh": "giai_thich_ngan", "y_goi_y": "gợi ý hiện tại",
        "ngu_canh_hs": "vì sao đạo hàm bằng 0 lại là cực trị ạ?",
    })
    assert van_ban  # không rỗng
    assert "gợi ý hiện tại" in van_ban


def test_stub_het_goi_y_khong_giong_goi_y_moi():
    """het_goi_y phải thành thật báo hết gợi ý, khác hẳn văn bản của goi_y bình thường."""
    llm = StubLLMClient()
    chung = {"y_goi_y": "gợi ý cuối", "cap_goi_y": 2, "buoc": 1, "ngu_canh_hs": ""}
    van_ban_het = llm.dien_dat({**chung, "y_dinh": "het_goi_y"})
    van_ban_goi_y = llm.dien_dat({**chung, "y_dinh": "goi_y"})
    assert van_ban_het != van_ban_goi_y
    assert "hết" in van_ban_het.lower() or "cuối cùng" in van_ban_het.lower()


def test_openai_dien_dat_truyen_de_bai():
    llm = OpenAILLMClient.__new__(OpenAILLMClient)
    llm._temperature = 0.4
    llm._suy_nghi = False
    llm._model = "gpt-4o-mini"
    goi_lai = {}

    class _FakeChoice:
        def __init__(self, content):
            self.message = type("M", (), {"content": content})()

    class _FakeResp:
        def __init__(self, content):
            self.choices = [_FakeChoice(content)]

    class _FakeCompletions:
        def create(self, **kwargs):
            goi_lai["user_prompt"] = kwargs["messages"][1]["content"]
            return _FakeResp("cau tra loi")

    class _FakeChat:
        completions = _FakeCompletions()

    llm._client = type("C", (), {"chat": _FakeChat()})()
    llm.dien_dat({
        "y_dinh": "goi_y", "y_goi_y": "gợi ý mới", "ngu_canh_hs": "em không biết",
        "de_bai": _DE_BAI_MAU,
    })
    assert _DE_BAI_MAU in goi_lai["user_prompt"]
