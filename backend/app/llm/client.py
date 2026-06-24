import json
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def dien_dat(self, chi_thi: dict) -> str:
        """Nhận ChiThi dict → trả văn bản tự nhiên cho HS."""

    @abstractmethod
    def sinh_cau_hoi(self, yeu_cau: dict) -> dict:
        """Sinh câu hỏi theo mẫu, trả JSON."""


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


class OpenAILLMClient(LLMClient):
    """Gọi OpenAI API."""

    def __init__(self, api_key: str, model: str, temperature: float):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("pip install openai để dùng provider openai")
        self._client = OpenAI(api_key=api_key)
        self._model = model or "gpt-4o-mini"
        self._temperature = temperature

    def _call(self, system: str, user: str) -> str:
        from app.llm.prompts import SYSTEM_DIEN_DAT  # noqa: F401

        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
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
        )
        raw = self._call(SYSTEM_SINH_CAU_HOI, user)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM trả JSON không hợp lệ: {e}") from e
        if "cau_hoi" not in data:
            raise ValueError("LLM trả thiếu khóa 'cau_hoi'")
        return data


def get_llm_client() -> LLMClient:
    from app.config import settings

    if settings.llm_provider == "openai" and settings.llm_api_key:
        return OpenAILLMClient(settings.llm_api_key, settings.llm_model, settings.llm_temperature)
    return StubLLMClient()
