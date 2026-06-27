import json
import re
import time
from abc import ABC, abstractmethod

# Số lần thử lại khi LLM lỗi tạm thời (503/429/timeout) hoặc trả JSON hỏng.
SO_LAN_THU = 3


class LLMClient(ABC):
    @abstractmethod
    def dien_dat(self, chi_thi: dict) -> str:
        """Nhận ChiThi dict → trả văn bản tự nhiên cho HS."""

    @abstractmethod
    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        """Sinh câu hỏi theo mẫu, trả JSON."""

    def phan_tich(self, ho_so: dict) -> dict | None:
        """Diễn giải hồ sơ năng lực → {cho_hoc_sinh, cho_giao_vien}. None = không khả dụng
        (vd StubLLMClient) → caller dùng đề xuất theo luật."""
        return None


class StubLLMClient(LLMClient):
    """Client tất định cho test/demo — không cần mạng."""

    def dien_dat(self, chi_thi: dict) -> str:
        """Diễn đạt tất định nhưng có nhiều biến thể để đỡ máy móc.

        Biến thể chọn theo một "seed" tất định (cấp gợi ý + bước + độ dài ngữ
        cảnh HS) nên cùng đầu vào luôn cho cùng đầu ra (test ổn định), nhưng
        lời nói thay đổi giữa các lượt. Văn bản KHÔNG nêu kết quả: y_goi_y chỉ
        là ý gợi mở, lớp chốt chặn vẫn rà lại trước khi gửi HS.
        """
        y_dinh = chi_thi.get("y_dinh", "")
        y_goi_y = (chi_thi.get("y_goi_y", "") or "").strip()
        cap = int(chi_thi.get("cap_goi_y", 0) or 0)
        buoc = int(chi_thi.get("buoc", 1) or 1)
        y_dang_xet = chi_thi.get("y_dang_xet") or ""
        ngu_canh = (chi_thi.get("ngu_canh_hs", "") or "").strip()

        seed = cap + buoc + len(ngu_canh)

        def pick(opts: list[str]) -> str:
            return opts[seed % len(opts)]

        # Kết thúc / tóm tắt: dùng lời cố định, KHÔNG in y_goi_y (là chỉ thị nội bộ).
        if y_dinh == "ket_thuc":
            return pick([
                "Tuyệt vời, em đã hoàn thành bài rồi! Em tự đi hết các bước rất chắc chắn. 🎉",
                "Hoàn thành rồi đấy! Mạch suy nghĩ của em mạch lạc lắm, giỏi quá. 🎉",
            ])
        if y_dinh == "tom_tat":
            return pick([
                "Em đã xét xong cả bốn ý. Thử nhìn lại mạch suy luận vừa rồi nhé — em làm tốt lắm!",
                "Vậy là bốn ý đã xong. Em nhẩm lại xem mình đã lập luận thế nào ở từng ý nhé. Giỏi lắm!",
            ])

        if not y_goi_y:
            y_goi_y = "em thử suy nghĩ tiếp xem sao"

        if y_dinh == "dinh_huong":
            return pick([
                f"Chào em! Mình cùng bắt đầu nhé. {y_goi_y}",
                f"Ta cùng phân tích bài này từ từ. {y_goi_y}",
                f"Mình vào bài thôi. {y_goi_y}",
            ])
        if y_dinh == "xac_nhan_dung":
            return pick([
                f"Chính xác rồi! 👏 Ta sang bước tiếp nhé: {y_goi_y}",
                f"Rất tốt, đúng rồi đó! Giờ tới bước tiếp theo: {y_goi_y}",
                f"Đúng rồi, em làm tốt lắm! Đi tiếp nào: {y_goi_y}",
            ])
        if y_dinh == "chuyen_y":
            return pick([
                f"Được rồi, mình chuyển sang ý {y_dang_xet} nhé. {y_goi_y}",
                f"Ta xét tiếp ý {y_dang_xet}. {y_goi_y}",
            ])
        if y_dinh == "hoi_nguoc":
            return pick([
                f"Chưa đúng rồi, nhưng đừng nản nhé. Em thử xem lại: {y_goi_y}",
                f"Gần đúng rồi đó! Em kiểm tra lại một chút xem: {y_goi_y}",
                f"Hmm, chỗ này em xem lại nhé. {y_goi_y}",
            ])

        # goi_y (mặc định): lời dẫn leo thang theo cấp gợi ý.
        if cap <= 0:
            return pick([
                f"Gợi ý cho em: {y_goi_y}",
                f"Em thử nghĩ theo hướng này nhé: {y_goi_y}",
            ])
        if cap == 1:
            return pick([
                f"Gợi ý thêm nhé: {y_goi_y}",
                f"Mình nói rõ hơn một chút: {y_goi_y}",
            ])
        return pick([
            f"Gợi ý kỹ hơn nữa: {y_goi_y}",
            f"Mình cùng đi sát từng bước nhé: {y_goi_y}",
        ])

    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        """Trả JSON mẫu tất định cho luồng duyệt (không cần mạng).

        yeu_cau: {chuyen_de, loai_cau, do_kho, so_luong, tai_lieu?}
        Trả: {"cau_hoi": [ <object đúng schema mỗi loại> ]}
        """
        so_luong = int(yeu_cau.get("so_luong", 1))
        loai_cau = yeu_cau.get("loai_cau", "TLN")
        chuyen_de = yeu_cau.get("chuyen_de", "Khảo sát hàm số")
        do_kho = yeu_cau.get("do_kho", "tb")
        so_goi_y = {"de": 2, "tb": 3, "kho": 4}.get(do_kho, 3)

        def goi_y(n: int) -> list[str]:
            # Công thức trong gợi ý đặt trong $...$ để frontend render đúng (nhất quán
            # với SYSTEM_SINH_CAU_HOI). Đây là mẫu tất định cho test/demo.
            base = [
                "Em xác định hướng làm của bước này trước nhé.",
                "Em thử nhớ lại công thức $y' = (x^n)' = n\\,x^{n-1}$ liên quan xem.",
                "Em thử áp dụng vào từng hạng tử của biểu thức.",
                "Em ghép các phần lại rồi tự suy ra kết quả của bước nhé.",
            ]
            return base[:n]

        cau_hoi = []
        for i in range(so_luong):
            if loai_cau == "TN4PA":
                cau_hoi.append({
                    "chuyen_de": chuyen_de, "loai_cau": "TN4PA", "do_kho": do_kho,
                    "de_bai": f"[AI nháp #{i+1}] Hàm số $y=x^3-3x+2$ đồng biến trên khoảng nào?",
                    "loai_dap_an_nhap": "chon_phuong_an", "che_do_so_khop": "tuong_duong",
                    "meta": {
                        "phuong_an": {"A": "$(-1;1)$", "B": "$(1;+\\infty)$",
                                      "C": "$(-\\infty;0)$", "D": "$(0;2)$"},
                        "dap_an_dung": "B",
                        "bat_buoc_suy_luan": do_kho != "de",
                    },
                    "solution_steps": [
                        {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính y' và xét dấu",
                         "bieu_thuc_ket_qua": "3*x**2-3", "danh_sach_goi_y": goi_y(so_goi_y)},
                    ],
                })
            elif loai_cau == "TNDS":
                cau_hoi.append({
                    "chuyen_de": chuyen_de, "loai_cau": "TNDS", "do_kho": do_kho,
                    "de_bai": f"[AI nháp #{i+1}] Cho $f(x)=2\\cos x + x$. Xét đúng/sai các mệnh đề.",
                    "loai_dap_an_nhap": "dung_sai_4y", "che_do_so_khop": "tuong_duong",
                    "meta": {"y": [
                        {"ky_hieu": "a", "noi_dung_y": "$f(0)=2$", "dap_an": "Dung",
                         "bat_buoc_suy_luan": do_kho != "de",
                         "loi_giai_y": "f(0)=2cos0+0=2"},
                        {"ky_hieu": "b", "noi_dung_y": "$f'(x)=-2\\sin x+1$", "dap_an": "Dung",
                         "loi_giai_y": "đạo hàm từng hạng tử"},
                        {"ky_hieu": "c", "noi_dung_y": "Nghiệm $f'(x)=0$ là $\\pi/6$",
                         "dap_an": "Dung", "loi_giai_y": "sinx=1/2 => x=pi/6"},
                        {"ky_hieu": "d", "noi_dung_y": "GTLN trên $[0;\\pi/2]$ là $2$",
                         "dap_an": "Sai", "loi_giai_y": "GTLN=sqrt(3)+pi/6>2"},
                    ]},
                    "solution_steps": [
                        {"thu_tu": 1, "pham_vi": "a", "mo_ta": "Thay x=0",
                         "bieu_thuc_ket_qua": "2", "danh_sach_goi_y": goi_y(so_goi_y)},
                        {"thu_tu": 1, "pham_vi": "b", "mo_ta": "Đạo hàm",
                         "bieu_thuc_ket_qua": "-2*sin(x)+1", "danh_sach_goi_y": goi_y(so_goi_y)},
                        {"thu_tu": 1, "pham_vi": "c", "mo_ta": "Giải f'(x)=0",
                         "bieu_thuc_ket_qua": "pi/6", "danh_sach_goi_y": goi_y(so_goi_y)},
                        {"thu_tu": 1, "pham_vi": "d", "mo_ta": "So GTLN với 2",
                         "bieu_thuc_ket_qua": "sqrt(3)+pi/6", "danh_sach_goi_y": goi_y(so_goi_y)},
                    ],
                })
            else:  # TLN
                cau_hoi.append({
                    "chuyen_de": chuyen_de, "loai_cau": "TLN", "do_kho": do_kho,
                    "de_bai": f"[AI nháp #{i+1}] Tìm GTLN của $f(x)=x^3-3x+2$ trên $[0;3]$.",
                    "loai_dap_an_nhap": "gia_tri", "che_do_so_khop": "tuong_duong",
                    "meta": {"dap_an_cuoi": "20", "quy_tac_lam_tron": None, "don_vi": None},
                    "solution_steps": [
                        {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm",
                         "bieu_thuc_ket_qua": "3*x**2-3", "danh_sach_goi_y": goi_y(so_goi_y)},
                        {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Giải f'(x)=0 trong đoạn",
                         "bieu_thuc_ket_qua": "1", "danh_sach_goi_y": goi_y(so_goi_y)},
                        {"thu_tu": 3, "pham_vi": "ca_bai", "mo_ta": "So sánh giá trị",
                         "bieu_thuc_ket_qua": "20", "danh_sach_goi_y": goi_y(so_goi_y)},
                    ],
                })
        return {"cau_hoi": cau_hoi}

    def phan_tich(self, ho_so: dict) -> dict | None:
        """Bản phân tích tất định (không cần mạng): ghép các đề xuất theo luật thành
        đoạn văn cho HS / GV. Đảm bảo nút 'Tạo phân tích' luôn có kết quả khi chưa
        cấu hình nhà cung cấp AI."""
        if ho_so.get("tong_hoan_thanh", 0) <= 0:
            return None
        hs = " ".join(ho_so.get("de_xuat_hs") or []).strip()
        gv = " ".join(ho_so.get("de_xuat_gv") or []).strip()
        if not hs and not gv:
            return None
        return {"cho_hoc_sinh": hs, "cho_giao_vien": gv}


class OpenAILLMClient(LLMClient):
    """Gọi OpenAI API."""

    def __init__(self, api_key: str, model: str, temperature: float, suy_nghi: bool = False):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("pip install openai để dùng provider openai")
        self._client = OpenAI(api_key=api_key)
        self._model = model or "gpt-4o-mini"
        self._temperature = temperature
        self._suy_nghi = suy_nghi  # bật/tắt suy luận (chỉ tác dụng với model reasoning)

    def _call(self, system: str, user: str) -> str:
        kwargs = dict(
            model=self._model,
            temperature=self._temperature,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        # Model dòng reasoning (o*, gpt-5*) nhận reasoning_effort; model chat thường bỏ qua.
        if self._model.startswith(("o", "gpt-5")):
            kwargs.pop("temperature", None)
            kwargs["reasoning_effort"] = "low" if self._suy_nghi else "minimal"
        resp = self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    def dien_dat(self, chi_thi: dict) -> str:
        from app.llm.prompts import SYSTEM_DIEN_DAT, user_prompt_dien_dat

        try:
            return self._call(
                SYSTEM_DIEN_DAT,
                user_prompt_dien_dat(
                    json.dumps(chi_thi, ensure_ascii=False),
                    chi_thi.get("ngu_canh_hs", ""),
                    chi_thi.get("ngu_canh_hs", ""),
                ),
            )
        except Exception:
            return f"Gợi ý: {chi_thi.get('y_goi_y', '')}"

    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        from app.llm.prompts import SYSTEM_SINH_CAU_HOI, user_prompt_sinh_cau_hoi

        user = user_prompt_sinh_cau_hoi(
            so_luong=int(yeu_cau.get("so_luong", 1)),
            loai_cau=yeu_cau.get("loai_cau", "TLN"),
            chuyen_de=yeu_cau.get("chuyen_de", ""),
            do_kho=yeu_cau.get("do_kho", "tb"),
            tai_lieu=yeu_cau.get("tai_lieu"),
            dang=yeu_cau.get("dang"),
        )
        return _goi_va_parse(lambda s, u: self._call(s, u), SYSTEM_SINH_CAU_HOI, user)

    def phan_tich(self, ho_so: dict) -> dict | None:
        return _phan_tich_qua_call(lambda s, u: self._call(s, u), ho_so)


def _va_escape_json(text: str) -> str:
    r"""Vá backslash đơn không hợp lệ trong JSON do LLM trả LaTeX (\dfrac, \sqrt...).

    JSON chỉ cho \" \\ \/ \b \f \n \r \t \uXXXX. Mọi '\' khác (vd "\d", "\s",
    "\underline") đều khiến json.loads lỗi. Nhân đôi chúng thành '\\' để hợp lệ
    mà vẫn giữ nguyên các escape đã đúng.
    """
    return re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', text)


def _bo_dau_phay_thua(text: str) -> str:
    """Bỏ dấu phẩy thừa trước ] hoặc } (lỗi JSON hay gặp ở LLM)."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _trich_json(text: str) -> str:
    """Lấy đoạn JSON: ưu tiên object {...}, nếu không có thì mảng [...]."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t
        if t[:4].lower() == "json":
            t = t[4:]
        t = t.strip().strip("`").strip()
    if "{" in t and "}" in t:
        return t[t.index("{"): t.rindex("}") + 1]
    if "[" in t and "]" in t:
        return t[t.index("["): t.rindex("]") + 1]
    return t


def _parse_json_cau_hoi(raw: str) -> dict:
    """Tách & parse JSON câu hỏi từ phản hồi LLM — chịu được rào ```, LaTeX, phẩy thừa,
    và trường hợp trả thẳng mảng [...] thay vì {"cau_hoi": [...]}.
    """
    text = _trich_json(raw or "")
    data = None
    last_err = None
    # Thử lần lượt: nguyên bản → vá escape → bỏ phẩy thừa → cả hai.
    for bien_the in (text, _va_escape_json(text), _bo_dau_phay_thua(text),
                     _bo_dau_phay_thua(_va_escape_json(text))):
        try:
            data = json.loads(bien_the)
            break
        except json.JSONDecodeError as e:
            last_err = e
    if data is None:
        raise ValueError(f"LLM trả JSON không hợp lệ: {last_err}")

    # Chấp nhận cả mảng trần lẫn object bọc.
    if isinstance(data, list):
        return {"cau_hoi": data}
    if isinstance(data, dict):
        if "cau_hoi" in data and isinstance(data["cau_hoi"], list):
            return data
        # Một số model trả thẳng 1 object câu hỏi.
        if "de_bai" in data or "loai_cau" in data or "meta" in data:
            return {"cau_hoi": [data]}
    raise ValueError("LLM trả thiếu khóa 'cau_hoi'")


def _parse_phan_tich(raw: str) -> dict | None:
    """Parse JSON {cho_hoc_sinh, cho_giao_vien} từ phản hồi LLM (chịu rào ``` + escape)."""
    text = _trich_json(raw or "")
    for bien_the in (text, _va_escape_json(text), _bo_dau_phay_thua(text)):
        try:
            data = json.loads(bien_the)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and (data.get("cho_hoc_sinh") or data.get("cho_giao_vien")):
            return {
                "cho_hoc_sinh": str(data.get("cho_hoc_sinh") or "").strip(),
                "cho_giao_vien": str(data.get("cho_giao_vien") or "").strip(),
            }
    return None


def _phan_tich_qua_call(call_fn, ho_so: dict) -> dict | None:
    """Gọi LLM diễn giải hồ sơ, tự thử lại; lỗi → None để caller dùng bản theo luật."""
    from app.llm.prompts import SYSTEM_PHAN_TICH, user_prompt_phan_tich

    user = user_prompt_phan_tich(json.dumps(ho_so, ensure_ascii=False))
    for lan in range(SO_LAN_THU):
        try:
            kq = _parse_phan_tich(call_fn(SYSTEM_PHAN_TICH, user))
            if kq:
                return kq
        except Exception:
            pass
        if lan < SO_LAN_THU - 1:
            time.sleep(1.0 * (lan + 1))
    return None


def _goi_va_parse(call_fn, system: str, user: str) -> dict:
    """Gọi LLM rồi parse JSON, tự thử lại khi lỗi tạm thời hoặc JSON hỏng.

    call_fn(system, user) -> str. Ném RuntimeError nếu hết số lần thử vẫn lỗi.
    """
    loi = None
    for lan in range(SO_LAN_THU):
        try:
            raw = call_fn(system, user)
            data = _parse_json_cau_hoi(raw)
            if not data.get("cau_hoi"):
                raise ValueError("LLM trả danh sách câu hỏi rỗng")
            return data
        except Exception as e:  # lỗi mạng/API hoặc JSON → thử lại
            loi = e
            if lan < SO_LAN_THU - 1:
                time.sleep(1.5 * (lan + 1))  # chờ tăng dần trước khi thử lại
    raise RuntimeError(f"Sinh câu hỏi thất bại sau {SO_LAN_THU} lần: {loi}")


class AnthropicLLMClient(LLMClient):
    """Gọi Claude (Anthropic) để sinh câu hỏi & diễn đạt gợi ý."""

    def __init__(self, api_key: str, model: str, temperature: float, suy_nghi: bool = False):
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:
            raise ImportError("pip install anthropic để dùng provider anthropic")
        self._client = Anthropic(api_key=api_key)
        self._model = model or "claude-opus-4-8"
        self._temperature = temperature
        self._suy_nghi = suy_nghi  # bật/tắt thinking (admin cấu hình)

    def _call(self, system: str, user: str, max_tokens: int = 4096,
              suy_nghi: bool | None = None) -> str:
        dung_suy_nghi = self._suy_nghi if suy_nghi is None else suy_nghi
        kwargs = dict(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if dung_suy_nghi:
            # Thinking thích nghi (Claude 4.6+); khi bật, không đặt temperature tùy biến.
            kwargs["thinking"] = {"type": "adaptive"}
        else:
            kwargs["temperature"] = self._temperature
        resp = self._client.messages.create(**kwargs)
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()

    def dien_dat(self, chi_thi: dict) -> str:
        from app.llm.prompts import SYSTEM_DIEN_DAT, user_prompt_dien_dat

        try:
            return self._call(
                SYSTEM_DIEN_DAT,
                user_prompt_dien_dat(
                    json.dumps(chi_thi, ensure_ascii=False),
                    chi_thi.get("ngu_canh_hs", ""),
                    chi_thi.get("ngu_canh_hs", ""),
                ),
                max_tokens=512,
            )
        except Exception:
            return f"Gợi ý: {chi_thi.get('y_goi_y', '')}"

    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        from app.llm.prompts import SYSTEM_SINH_CAU_HOI, user_prompt_sinh_cau_hoi

        user = user_prompt_sinh_cau_hoi(
            so_luong=int(yeu_cau.get("so_luong", 1)),
            loai_cau=yeu_cau.get("loai_cau", "TLN"),
            chuyen_de=yeu_cau.get("chuyen_de", ""),
            do_kho=yeu_cau.get("do_kho", "tb"),
            tai_lieu=yeu_cau.get("tai_lieu"),
            dang=yeu_cau.get("dang"),
        )
        return _goi_va_parse(
            lambda s, u: self._call(s, u, max_tokens=8192), SYSTEM_SINH_CAU_HOI, user
        )

    def phan_tich(self, ho_so: dict) -> dict | None:
        return _phan_tich_qua_call(lambda s, u: self._call(s, u, max_tokens=4096), ho_so)


class GeminiLLMClient(LLMClient):
    """Gọi Google Gemini để sinh câu hỏi & diễn đạt gợi ý."""

    # Model dự phòng khi model chính bị 503 (quá tải) — thử lần lượt.
    _DU_PHONG = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]

    def __init__(self, api_key: str, model: str, temperature: float, suy_nghi: bool = False):
        try:
            from google import genai  # type: ignore
        except ImportError:
            raise ImportError("pip install google-genai để dùng provider gemini")
        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._model = model or "gemini-2.5-flash"
        self._temperature = temperature
        self._suy_nghi = suy_nghi  # bật/tắt thinking (admin cấu hình)
        # Danh sách model thử: model cấu hình trước, rồi các model dự phòng (khử trùng lặp).
        self._models = [self._model] + [m for m in self._DU_PHONG if m != self._model]

    def _call(self, system: str, user: str, max_tokens: int = 4096,
              suy_nghi: bool | None = None) -> str:
        from google.genai import errors as genai_errors  # type: ignore
        from google.genai import types  # type: ignore

        # None = theo cấu hình admin; tác vụ riêng có thể ép (vd phân tích luôn tắt).
        dung_suy_nghi = self._suy_nghi if suy_nghi is None else suy_nghi

        cfg_kwargs = dict(
            system_instruction=system,
            temperature=self._temperature,
            max_output_tokens=max_tokens,
        )
        # Tắt "thinking" cho tác vụ không cần suy luận sâu (vd phân tích) để token
        # đầu ra không bị thinking ăn hết gây cắt cụt JSON. Bọc try vì bản genai cũ
        # có thể chưa có ThinkingConfig.
        if not dung_suy_nghi:
            try:
                cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            except Exception:  # noqa: BLE001
                pass
        cfg = types.GenerateContentConfig(**cfg_kwargs)
        loi = None
        for m in self._models:
            try:
                resp = self._client.models.generate_content(model=m, contents=user, config=cfg)
                return (resp.text or "").strip()
            except genai_errors.ServerError as e:  # 5xx/quá tải → thử model kế
                loi = e
                continue
            except genai_errors.ClientError as e:  # 429 hết quota → thử model khác (quota riêng)
                loi = e
                if getattr(e, "code", None) == 429:
                    continue
                raise
        # Hết model dự phòng vẫn lỗi → ném để lớp trên thử lại/đổi sang 502.
        raise loi if loi else RuntimeError("Gemini không phản hồi")

    def dien_dat(self, chi_thi: dict) -> str:
        from app.llm.prompts import SYSTEM_DIEN_DAT, user_prompt_dien_dat

        try:
            return self._call(
                SYSTEM_DIEN_DAT,
                user_prompt_dien_dat(
                    json.dumps(chi_thi, ensure_ascii=False),
                    chi_thi.get("ngu_canh_hs", ""),
                    chi_thi.get("ngu_canh_hs", ""),
                ),
                max_tokens=512,
            )
        except Exception:
            return f"Gợi ý: {chi_thi.get('y_goi_y', '')}"

    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        from app.llm.prompts import SYSTEM_SINH_CAU_HOI, user_prompt_sinh_cau_hoi

        user = user_prompt_sinh_cau_hoi(
            so_luong=int(yeu_cau.get("so_luong", 1)),
            loai_cau=yeu_cau.get("loai_cau", "TLN"),
            chuyen_de=yeu_cau.get("chuyen_de", ""),
            do_kho=yeu_cau.get("do_kho", "tb"),
            tai_lieu=yeu_cau.get("tai_lieu"),
            dang=yeu_cau.get("dang"),
        )
        return _goi_va_parse(
            lambda s, u: self._call(s, u, max_tokens=8192), SYSTEM_SINH_CAU_HOI, user
        )

    def phan_tich(self, ho_so: dict) -> dict | None:
        return _phan_tich_qua_call(
            lambda s, u: self._call(s, u, max_tokens=4096, suy_nghi=False), ho_so
        )


# Model mặc định mỗi nhà cung cấp (khi admin để trống ô model).
MODEL_MAC_DINH = {
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o-mini",
}


def get_llm_client(cau_hinh: dict | None = None) -> LLMClient:
    """Tạo LLM client theo cấu hình admin (DB). Thiếu khóa → quay về stub an toàn.

    cau_hinh: dict từ admin_service.lay_cau_hinh(db). None → đọc từ env settings.
    """
    from app.config import settings

    if cau_hinh is None:
        provider = (settings.llm_provider or "stub").lower()
        khoa = settings.llm_api_key
        model = settings.llm_model
        temperature = settings.llm_temperature
        suy_nghi = False
    else:
        provider = str(cau_hinh.get("llm_provider") or "stub").lower()
        khoa = cau_hinh.get(f"llm_api_key_{provider}", "") or ""
        model = cau_hinh.get("llm_model") or ""
        temperature = float(cau_hinh.get("llm_temperature", settings.llm_temperature))
        suy_nghi = bool(cau_hinh.get(f"llm_thinking_{provider}", False))

    model = model or MODEL_MAC_DINH.get(provider, "")

    try:
        if provider == "gemini" and khoa:
            return GeminiLLMClient(khoa, model, temperature, suy_nghi)
        if provider == "anthropic" and khoa:
            return AnthropicLLMClient(khoa, model, temperature, suy_nghi)
        if provider == "openai" and khoa:
            return OpenAILLMClient(khoa, model, temperature, suy_nghi)
    except ImportError:
        return StubLLMClient()
    return StubLLMClient()
