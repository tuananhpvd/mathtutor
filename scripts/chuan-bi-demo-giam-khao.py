"""
Chuẩn bị dữ liệu demo cho Ban giám khảo trên production (hoặc bất kỳ môi trường nào).

VÌ SAO ĐI QUA API, KHÔNG GHI THẲNG DATABASE:
Mọi thứ script này làm đều là việc một người dùng thật có thể làm qua giao diện. Đi qua API
nghĩa là mọi ràng buộc nghiệp vụ, phân quyền và tính nhất quán dữ liệu do chính hệ thống bảo
đảm — không thể tạo ra trạng thái "không thể xảy ra trong thực tế" như khi INSERT thẳng DB.

BA RÀNG BUỘC KIẾN TRÚC ĐÃ KIỂM CHỨNG (quyết định toàn bộ thiết kế script này — nếu bỏ qua
bất kỳ cái nào, tài khoản demo sẽ trống rỗng và giám khảo không thấy được gì):

  1. `hs_duoc_truy_cap_bai()` — học sinh CHỈ truy cập bài của GV chủ nhiệm lớp mình
     (hoặc bài được giao qua nhiệm vụ).
  2. `giao_nhiem_vu()` — giáo viên CHỈ giao được bài DO CHÍNH MÌNH tạo.
  3. `get_danh_muc()` — DANH MỤC (chuyên đề/dạng) cũng thuộc sở hữu từng GV; học sinh chỉ
     thấy danh mục của GV chủ nhiệm.

  → Hệ quả: `gvdemo` phải tự có DANH MỤC riêng VÀ KHO CÂU HỎI riêng. Không thể mượn danh
    mục/câu hỏi của GV thật (và cũng không nên — sẽ lẫn dữ liệu demo vào dữ liệu thật).

  4. `POST /api/problems` (GV nhập tay) → tự động `da_duyet`, CÓ nhận `solution_steps`
     (bước giải + thang gợi ý) → dùng cho kho câu hỏi chính, học sinh luyện được ngay.
  5. `POST /api/problems/import-batch` → tạo ở trạng thái `cho_duyet` nhưng KHÔNG nhận bước
     giải → dùng riêng để tạo vài câu "chờ duyệt" cho giám khảo bấm duyệt/sửa/loại.

TÍNH IDEMPOTENT: chạy lại nhiều lần không nhân đôi dữ liệu. Riêng lịch sử học chỉ tạo khi học
sinh đó chưa có phiên hoàn thành nào, tránh cộng dồn ngoài ý muốn.

CÁCH CHẠY:
    cd backend
    .venv\\Scripts\\python.exe ..\\scripts\\chuan-bi-demo-giam-khao.py ^
        --url https://mathtutor-1.onrender.com ^
        --admin-user admin --admin-pass "<mật khẩu admin>"

    Thêm --chi-xem-truoc để CHỈ in ra những gì sẽ làm mà không ghi gì (nên chạy trước).

LƯU Ý VỀ HẠN MỨC AI: script tạo lịch sử học bằng cách gọi API thật, mỗi lượt trò chuyện tốn
1 lượt LLM (~60-80 lượt cho toàn bộ). Nếu vượt `gioi_han_llm_hs_ngay`, hệ thống tự chuyển
sang StubLLMClient — phiên vẫn hoàn thành và số liệu tiến độ vẫn đúng, chỉ lời thoại là mẫu
có sẵn. Không gây lỗi, nhưng nên chạy lúc không trùng giờ học sinh thật đang dùng.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

# Console Windows mặc định dùng bảng mã cp1252, không in được tiếng Việt có dấu → script sẽ
# chết giữa chừng bằng UnicodeEncodeError. Ép UTF-8 để chạy được trên PowerShell/cmd lẫn
# terminal Linux/macOS.
for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        _luong.reconfigure(encoding="utf-8", errors="replace")

TEN_LOP_DEMO = "Lớp Demo"

# (đăng_nhập, họ tên, vai trò, mật khẩu) — mật khẩu riêng theo vai trò, tối thiểu 6 ký tự
# theo ràng buộc TaoTaiKhoanRequest.
TAI_KHOAN_DEMO = [
    ("gvdemo", "GV Demo (Ban giám khảo)", "gv", "gvdemo123"),
    ("hsdemo_moi", "HS Demo - Mới bắt đầu", "hs", "hsdemo123"),
    ("hsdemo_dahoc", "HS Demo - Đã có tiến độ", "hs", "hsdemo123"),
    ("hsdemo_danglam", "HS Demo - Đang làm dở", "hs", "hsdemo123"),
]
MAT_KHAU_THEO_TAI_KHOAN = {t[0]: t[3] for t in TAI_KHOAN_DEMO}

# Danh mục RIÊNG của gvdemo (ràng buộc #3). Tên đặt giống chương trình Toán 12 thật để
# giám khảo thấy tự nhiên, nhưng là bản riêng của lớp demo, không đụng danh mục GV thật.
DANH_MUC_DEMO = [
    ("Ứng dụng của đạo hàm", ["Tính đơn điệu của hàm số", "Cực trị của hàm số"]),
    ("Nguyên hàm và tích phân", ["Tích phân"]),
]


# ─────────────────────────── Kho câu hỏi của gvdemo ────────────────────────────
# `dang_ten` được script tra sang dang_id lúc chạy (KHÔNG hardcode id — id khác nhau giữa
# các môi trường). Mỗi dạng có >= 2 câu để đạt NGUONG_NHOM=2 của hồ sơ năng lực, nếu không
# bản đồ năng lực và điểm mạnh/điểm yếu sẽ không có dữ liệu để hiện.

CAU_HOI = [
    # ── Dạng "Tính đơn điệu" — hsdemo_dahoc sẽ làm TỐT dạng này (thành điểm mạnh) ──
    {
        "loai_cau": "TLN", "do_kho": "de", "dang_ten": "Tính đơn điệu của hàm số",
        "de_bai": "Cho hàm số $f(x) = x^2 - 4x + 3$. Tìm hoành độ điểm cực tiểu của hàm số.",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm $f'(x)$",
             "bieu_thuc_ket_qua": "2*x - 4",
             "danh_sach_goi_y": ["Em nhớ lại công thức đạo hàm của $x^n$ nhé.",
                                 "Đạo hàm của $x^2$ là $2x$, của $-4x$ là $-4$."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Giải $f'(x) = 0$",
             "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["Em cho đạo hàm bằng 0 rồi giải phương trình bậc nhất.",
                                 "Từ $2x - 4 = 0$, em chuyển vế tìm $x$."]},
        ],
    },
    {
        "loai_cau": "TLN", "do_kho": "tb", "dang_ten": "Tính đơn điệu của hàm số",
        "de_bai": "Cho hàm số $f(x) = x^3 - 3x$. Hàm số nghịch biến trên khoảng $(-a; a)$ với $a > 0$. Tìm $a$.",
        "meta": {"dap_an_cuoi": "1"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm $f'(x)$",
             "bieu_thuc_ket_qua": "3*x**2 - 3",
             "danh_sach_goi_y": ["Em áp dụng công thức đạo hàm của lũy thừa.",
                                 "Đạo hàm của $x^3$ là $3x^2$.",
                                 "Ghép lại: đạo hàm của $x^3 - 3x$ gồm hai phần."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Giải $f'(x) = 0$ tìm nghiệm dương",
             "bieu_thuc_ket_qua": "1",
             "danh_sach_goi_y": ["Em cho $3x^2 - 3 = 0$ rồi giải.",
                                 "Rút gọn thành $x^2 = 1$, em tìm nghiệm dương.",
                                 "Nghiệm dương của $x^2 = 1$ chính là giá trị $a$ cần tìm."]},
        ],
    },
    {
        "loai_cau": "TN4PA", "do_kho": "de", "dang_ten": "Tính đơn điệu của hàm số",
        "de_bai": "Hàm số $y = x^3 - 3x + 3$ đồng biến trên khoảng nào sau đây?",
        "meta": {
            "dap_an_dung": "B",
            "phuong_an": {"A": "$(-\\infty; 1)$", "B": "$(1; +\\infty)$",
                          "C": "$(-\\infty; 2)$", "D": "$(-1; 1)$"},
            "bat_buoc_suy_luan": True,
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm $y'$",
             "bieu_thuc_ket_qua": "3*x**2 - 3",
             "danh_sach_goi_y": ["Em tính đạo hàm của hàm số đã cho trước.",
                                 "Đạo hàm của $x^3$ là $3x^2$, của $-3x$ là $-3$."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Xét dấu $y'$ và kết luận",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em giải $y' = 0$ rồi lập bảng xét dấu.",
                                 "Hàm đồng biến ở khoảng mà $y' > 0$."]},
        ],
    },
    # ── Dạng "Tích phân" — hsdemo_dahoc sẽ làm CHẬT VẬT (thành điểm yếu) ──
    {
        "loai_cau": "TLN", "do_kho": "tb", "dang_ten": "Tích phân",
        "de_bai": "Tính tích phân $I = \\int_0^2 3x^2 \\, dx$.",
        "meta": {"dap_an_cuoi": "8"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $3x^2$",
             "bieu_thuc_ket_qua": "x**3",
             "danh_sach_goi_y": ["Em nhớ công thức nguyên hàm của $x^n$.",
                                 "Nguyên hàm của $x^n$ là $\\frac{x^{n+1}}{n+1}$.",
                                 "Với $3x^2$, em tăng bậc lên 3 rồi chia cho hệ số phù hợp."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận và tính hiệu",
             "bieu_thuc_ket_qua": "8",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tính $2^3 - 0^3$.",
                                 "Kết quả là hiệu của hai giá trị vừa tính."]},
        ],
    },
    {
        "loai_cau": "TLN", "do_kho": "kho", "dang_ten": "Tích phân",
        "de_bai": "Tính tích phân $I = \\int_1^2 (4x^3 - 2x) \\, dx$.",
        "meta": {"dap_an_cuoi": "12"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $4x^3 - 2x$",
             "bieu_thuc_ket_qua": "x**4 - x**2",
             "danh_sach_goi_y": ["Em tìm nguyên hàm từng hạng tử một.",
                                 "Nguyên hàm của $x^n$ là $\\frac{x^{n+1}}{n+1}$.",
                                 "Nguyên hàm của $4x^3$ là $x^4$; em làm tương tự với $-2x$.",
                                 "Cộng hai nguyên hàm vừa tìm lại với nhau."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 1 và 2 rồi tính hiệu",
             "bieu_thuc_ket_qua": "12",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tính giá trị tại $x=2$ trước, rồi tại $x=1$.",
                                 "Tại $x=2$: $2^4 - 2^2 = 12$. Em tính tiếp tại $x=1$.",
                                 "Lấy giá trị tại 2 trừ giá trị tại 1."]},
        ],
    },
    {
        # CỐ Ý để hsdemo_dahoc KHÔNG làm bài này (xem `bo_qua_lich_su`): dạng "Tích phân"
        # là điểm yếu của em, mà `de_xuat_theo_diem_yeu()` chỉ đề xuất bài CHƯA hoàn thành —
        # nếu em làm hết sạch thì GV bấm "đề xuất theo điểm yếu" sẽ ra danh sách RỖNG, và
        # "Bài nên luyện tiếp" bên phía HS cũng không còn gì để dẫn tới.
        "loai_cau": "TLN", "do_kho": "tb", "dang_ten": "Tích phân", "bo_qua_lich_su": True,
        "de_bai": "Tính tích phân $I = \\int_0^1 (3x^2 + 2x) \\, dx$.",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $3x^2 + 2x$",
             "bieu_thuc_ket_qua": "x**3 + x**2",
             "danh_sach_goi_y": ["Em tìm nguyên hàm từng hạng tử một.",
                                 "Nguyên hàm của $3x^2$ là $x^3$.",
                                 "Nguyên hàm của $2x$ là $x^2$; cộng hai kết quả lại."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 0 và 1 rồi tính hiệu",
             "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tại $x=1$: $1^3 + 1^2 = 2$. Tại $x=0$ thì bằng bao nhiêu?",
                                 "Lấy giá trị tại 1 trừ giá trị tại 0."]},
        ],
    },
    # ── Dạng "Cực trị" — TNDS, để giám khảo thấy loại câu Đúng/Sai 4 ý ──
    {
        "loai_cau": "TNDS", "do_kho": "tb", "dang_ten": "Cực trị của hàm số",
        "de_bai": "Cho hàm số $y = x^3 - 3x^2 + 2$. Xét tính đúng sai của các mệnh đề sau:",
        "meta": {
            "y": [
                {"ky_hieu": "a", "noi_dung_y": "$y' = 3x^2 - 6x$", "dap_an": "Dung"},
                {"ky_hieu": "b", "noi_dung_y": "Hàm số có 2 điểm cực trị", "dap_an": "Dung"},
                {"ky_hieu": "c", "noi_dung_y": "Hàm số đồng biến trên $(0; 2)$", "dap_an": "Sai"},
                {"ky_hieu": "d", "noi_dung_y": "Đồ thị cắt trục tung tại điểm có tung độ 2",
                 "dap_an": "Dung"},
            ],
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "a", "mo_ta": "Kiểm tra công thức đạo hàm",
             "bieu_thuc_ket_qua": "3*x**2 - 6*x",
             "danh_sach_goi_y": ["Em tự tính đạo hàm rồi so với mệnh đề.",
                                 "Đạo hàm của $x^3$ là $3x^2$, của $-3x^2$ là $-6x$.",
                                 "So sánh kết quả em tính với biểu thức trong mệnh đề."]},
            {"thu_tu": 1, "pham_vi": "b", "mo_ta": "Đếm số nghiệm của $y' = 0$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Số điểm cực trị liên quan tới số nghiệm của $y' = 0$.",
                                 "Em giải $3x^2 - 6x = 0$ xem có mấy nghiệm.",
                                 "Mỗi nghiệm mà đạo hàm đổi dấu cho một điểm cực trị."]},
            {"thu_tu": 1, "pham_vi": "c", "mo_ta": "Xét dấu $y'$ trên khoảng $(0; 2)$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em thử thay một giá trị bất kỳ trong khoảng $(0; 2)$.",
                                 "Chẳng hạn thay $x = 1$ vào $y'$ xem dấu ra sao.",
                                 "Nếu $y' < 0$ thì hàm nghịch biến chứ không đồng biến."]},
            {"thu_tu": 1, "pham_vi": "d", "mo_ta": "Tính giá trị hàm số tại $x = 0$",
             "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["Đồ thị cắt trục tung tại điểm có hoành độ bằng 0.",
                                 "Em thay $x = 0$ vào hàm số ban đầu.",
                                 "Giá trị vừa tính chính là tung độ giao điểm."]},
        ],
    },
]

# Câu để ở trạng thái "chờ duyệt" — giám khảo bấm Duyệt / Sửa / Loại ngay trên giao diện GV.
CAU_HOI_CHO_DUYET = [
    {"loai_cau": "TLN", "chuyen_de": "Ứng dụng của đạo hàm", "do_kho": "de",
     "de_bai": "[Bản nháp chờ duyệt] Cho $f(x) = 2x + 5$. Tính $f'(x)$.",
     "meta": {"dap_an_cuoi": "2"}},
    {"loai_cau": "TLN", "chuyen_de": "Nguyên hàm và tích phân", "do_kho": "tb",
     "de_bai": "[Bản nháp chờ duyệt] Tính $\\int_0^1 2x \\, dx$.",
     "meta": {"dap_an_cuoi": "1"}},
    {"loai_cau": "TLN", "chuyen_de": "Ứng dụng của đạo hàm", "do_kho": "kho",
     "de_bai": "[Bản nháp chờ duyệt] Cho $f(x) = x^4 - 2x^2$. Tìm số điểm cực trị.",
     "meta": {"dap_an_cuoi": "3"}},
]


class Api:
    def __init__(self, goc: str, chi_xem_truoc: bool = False):
        self.goc = goc.rstrip("/")
        self.token: str | None = None
        self.chi_xem_truoc = chi_xem_truoc

    def _goi(self, phuong_thuc: str, duong_dan: str, du_lieu=None, ghi: bool = False):
        if ghi and self.chi_xem_truoc:
            print(f"      [XEM TRƯỚC] bỏ qua {phuong_thuc} {duong_dan}")
            return None
        url = f"{self.goc}/api{duong_dan}"
        body = json.dumps(du_lieu).encode() if du_lieu is not None else None
        req = urllib.request.Request(url, data=body, method=phuong_thuc)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"{phuong_thuc} {duong_dan} → HTTP {e.code}: {e.read().decode()[:400]}"
            ) from e

    def get(self, dd):
        return self._goi("GET", dd)

    def post(self, dd, du_lieu=None):
        return self._goi("POST", dd, du_lieu, ghi=True)

    def patch(self, dd, du_lieu=None):
        return self._goi("PATCH", dd, du_lieu, ghi=True)

    def dang_nhap(self, dang_nhap: str, mat_khau: str):
        # Đăng nhập không phải thao tác ghi → chạy cả ở chế độ xem trước.
        kq = self._goi("POST", "/auth/login", {"dang_nhap": dang_nhap, "mat_khau": mat_khau})
        self.token = kq["access_token"]
        return kq


def buoc_1_tai_khoan_va_lop(api: Api) -> dict:
    print("\n[1/6] Tài khoản và lớp demo")
    users = api.get("/admin/users") or []
    theo_ten = {u["dang_nhap"]: u for u in users}
    ids: dict[str, int] = {}

    for dang_nhap, ho_ten, vai_tro, mat_khau in TAI_KHOAN_DEMO:
        if dang_nhap in theo_ten:
            ids[dang_nhap] = theo_ten[dang_nhap]["id"]
            print(f"      đã có: {dang_nhap}")
            continue
        kq = api.post("/admin/users", {"ho_ten": ho_ten, "dang_nhap": dang_nhap,
                                       "mat_khau": mat_khau, "vai_tro": vai_tro})
        if kq:
            ids[dang_nhap] = kq["id"]
        print(f"      TẠO MỚI: {dang_nhap} ({vai_tro})")

    cac_lop = api.get("/admin/lop") or []
    lop = next((x for x in cac_lop if x["ten"] == TEN_LOP_DEMO), None)
    if lop:
        lop_id = lop["id"]
        print(f"      đã có lớp: {TEN_LOP_DEMO} (id={lop_id})")
    else:
        kq = api.post("/admin/lop", {"ten": TEN_LOP_DEMO, "gv_id": ids.get("gvdemo")})
        lop_id = kq["id"] if kq else None
        print(f"      TẠO MỚI lớp: {TEN_LOP_DEMO} (chủ nhiệm: gvdemo)")

    for dang_nhap in ("hsdemo_moi", "hsdemo_dahoc", "hsdemo_danglam"):
        if dang_nhap in ids and lop_id:
            api.patch(f"/admin/users/{ids[dang_nhap]}/lop", {"lop_id": lop_id})
            print(f"      gán {dang_nhap} → lớp demo")
    return {"ids": ids, "lop_id": lop_id}


def buoc_2_danh_muc(api_gv: Api) -> dict[str, int]:
    """Danh mục RIÊNG của gvdemo (ràng buộc #3) → trả map {tên dạng: dang_id}."""
    print("\n[2/6] Danh mục (chuyên đề + dạng) riêng của gvdemo")
    hien_co = api_gv.get("/danh-muc") or []
    cd_theo_ten = {c["ten"]: c for c in hien_co}
    map_dang: dict[str, int] = {}

    for ten_cd, cac_dang in DANH_MUC_DEMO:
        cd = cd_theo_ten.get(ten_cd)
        if cd:
            cd_id = cd["id"]
            print(f"      đã có chuyên đề: {ten_cd}")
            for d in cd.get("dang_list") or []:
                map_dang[d["ten"]] = d["id"]
        else:
            kq = api_gv.post("/danh-muc/chuyen-de", {"ten": ten_cd})
            cd_id = kq["id"] if kq else None
            print(f"      TẠO MỚI chuyên đề: {ten_cd}")

        for ten_dang in cac_dang:
            if ten_dang in map_dang:
                continue
            if cd_id is None:
                continue
            kq = api_gv.post("/danh-muc/dang", {"chuyen_de_id": cd_id, "ten": ten_dang})
            if kq:
                map_dang[ten_dang] = kq["id"]
            print(f"         TẠO MỚI dạng: {ten_dang}")
    return map_dang


def buoc_3_kho_cau_hoi(api_gv: Api, map_dang: dict[str, int]):
    """Kho câu hỏi thuộc sở hữu gvdemo (ràng buộc #1, #2) — có bước giải + thang gợi ý."""
    print("\n[3/6] Kho câu hỏi của gvdemo (đã duyệt, có bước giải + thang gợi ý)")
    hien_co = api_gv.get("/problems") or []
    de_bai_co = {p.get("de_bai", "")[:60] for p in hien_co}

    for cau in CAU_HOI:
        if cau["de_bai"][:60] in de_bai_co:
            print(f"      đã có: {cau['de_bai'][:52]}...")
            continue
        than = {k: v for k, v in cau.items() if k not in ("dang_ten", "bo_qua_lich_su")}
        dang_id = map_dang.get(cau["dang_ten"])
        if dang_id:
            than["dang_id"] = dang_id
        else:
            print(f"      !! không tìm thấy dạng '{cau['dang_ten']}' — tạo không gắn dạng")
        api_gv.post("/problems", than)
        print(f"      TẠO MỚI [{cau['loai_cau']}/{cau['do_kho']}] {cau['dang_ten']}: "
              f"{cau['de_bai'][:42]}...")


def buoc_4_cau_cho_duyet(api_gv: Api):
    print("\n[4/6] Câu hỏi 'chờ duyệt' cho giám khảo thao tác kiểm duyệt")
    hien_co = api_gv.get("/problems") or []
    if any(p.get("trang_thai_duyet") == "cho_duyet" for p in hien_co):
        print("      đã có câu chờ duyệt — bỏ qua")
        return
    kq = api_gv.post("/problems/import-batch", {"items": CAU_HOI_CHO_DUYET})
    if kq:
        print(f"      đã tạo {kq.get('da_tao', '?')} câu ở trạng thái chờ duyệt")


def _dap_an_theo_de() -> dict[str, list[str]]:
    """Đáp án đúng từng bước, tra theo đề bài (script biết vì chính nó tạo kho câu hỏi)."""
    ra: dict[str, list[str]] = {}
    for cau in CAU_HOI:
        khoa = cau["de_bai"][:60]
        buoc = [b["bieu_thuc_ket_qua"] for b in cau["solution_steps"] if b["bieu_thuc_ket_qua"]]
        if cau["loai_cau"] == "TLN":
            ra[khoa] = buoc
        elif cau["loai_cau"] == "TN4PA":
            ra[khoa] = buoc + [cau["meta"]["dap_an_dung"]]
        # TNDS cần luồng chọn Đúng/Sai riêng — để giám khảo tự trải nghiệm, không dựng sẵn
    return ra


def _lam_bai(api_hs: Api, problem_id: int, cac_dap_an: list[str],
             so_lan_xin_goi_y: int = 0, so_lan_sai: int = 0) -> bool:
    """Mở 1 phiên rồi làm bài. `so_lan_xin_goi_y`/`so_lan_sai` dùng để nặn ra hồ sơ năng lực
    ĐA DẠNG — điểm thành thạo tính theo `1.0 - 0.1*số lần sai - 0.15*số lần xin gợi ý`, nên
    muốn có "điểm yếu" (thành thạo < 50) thì phải cố ý sai + xin gợi ý nhiều lần.
    """
    phien = api_hs.post("/sessions", {"problem_id": problem_id})
    if not phien:
        return False
    sid = phien["session_id"]

    for _ in range(so_lan_xin_goi_y):
        api_hs.post(f"/sessions/{sid}/message", {"noi_dung": "", "yeu_cau_goi_y": True})
    for _ in range(so_lan_sai):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Em thử đáp án này", "dap_an_nhap": "99999"})
    for dap_an in cac_dap_an:
        kq = api_hs.post(f"/sessions/{sid}/message",
                         {"noi_dung": f"Em trả lời: {dap_an}", "dap_an_nhap": dap_an})
        if kq and kq.get("da_xong"):
            return True
    return False


def buoc_5_lich_su_hoc(url: str, chi_xem_truoc: bool):
    """hsdemo_dahoc: LÀM TỐT dạng "Tính đơn điệu", CHẬT VẬT dạng "Tích phân".

    Cố ý tạo chênh lệch để hồ sơ năng lực có CẢ điểm mạnh LẪN điểm yếu — nếu làm đúng hết,
    `diem_yeu` sẽ rỗng và các tính năng cá nhân hóa ("Bài nên luyện tiếp" của HS, "đề xuất
    theo điểm yếu" của GV, màu sắc trên Bản đồ năng lực) sẽ không hiện được gì.
    """
    print("\n[5/6] Lịch sử học cho hsdemo_dahoc (có cả điểm mạnh lẫn điểm yếu)")
    api_hs = Api(url, chi_xem_truoc)
    api_hs.dang_nhap("hsdemo_dahoc", MAT_KHAU_THEO_TAI_KHOAN["hsdemo_dahoc"])

    tien_do = api_hs.get("/progress/me") or []
    if sum(t.get("so_bai_hoan_thanh", 0) for t in tien_do) >= 4:
        print("      đã có lịch sử học — bỏ qua để không cộng dồn")
        return

    bai_hs = api_hs.get("/problems") or []
    print(f"      học sinh nhìn thấy {len(bai_hs)} bài")
    dap_an = _dap_an_theo_de()
    dang_cua_de = {c["de_bai"][:60]: c["dang_ten"] for c in CAU_HOI}
    bo_qua = {c["de_bai"][:60] for c in CAU_HOI if c.get("bo_qua_lich_su")}

    so_xong = 0
    for bai in bai_hs:
        khoa = bai.get("de_bai", "")[:60]
        if khoa not in dap_an or khoa in bo_qua:
            continue
        ten_dang = dang_cua_de.get(khoa, "")
        if ten_dang == "Tích phân":
            xin, sai = 3, 3   # chật vật → thành thạo thấp → vào "điểm yếu"
        else:
            xin, sai = 0, 0   # làm gọn → thành thạo cao → vào "điểm mạnh"
        if _lam_bai(api_hs, bai["id"], dap_an[khoa], xin, sai):
            so_xong += 1
            print(f"      xong [{ten_dang}] xin {xin} gợi ý, sai {sai} lần: "
                  f"{bai.get('de_bai', '')[:38]}...")
    print(f"      → tổng {so_xong} bài hoàn thành")


def buoc_6_bai_dang_lam(url: str, chi_xem_truoc: bool):
    """hsdemo_danglam: 1 bài dở + xin gợi ý tới cạn → cờ 'không hiểu nhiều' TỰ phát sinh.

    Cố ý KHÔNG gọi API tạo cờ thủ công: để cờ sinh ra đúng cơ chế thật của sản phẩm, giám
    khảo thấy được cảnh báo tự động chứ không phải dữ liệu dựng sẵn.
    """
    print("\n[6/6] Bài đang làm dở + cờ cảnh báo tự phát sinh cho gvdemo xử lý")
    api_hs = Api(url, chi_xem_truoc)
    api_hs.dang_nhap("hsdemo_danglam", MAT_KHAU_THEO_TAI_KHOAN["hsdemo_danglam"])

    if api_hs.get("/sessions/dang-do"):
        print("      đã có bài đang làm dở — bỏ qua")
        return

    bai_hs = api_hs.get("/problems") or []
    bai = next((b for b in bai_hs if b.get("do_kho") == "kho"), bai_hs[0] if bai_hs else None)
    if not bai:
        print("      !! không có bài nào — kiểm tra lại bước 3")
        return

    phien = api_hs.post("/sessions", {"problem_id": bai["id"]})
    if not phien:
        return
    sid = phien["session_id"]
    print(f"      mở bài: {bai.get('de_bai', '')[:45]}...")
    for _ in range(4):
        api_hs.post(f"/sessions/{sid}/message", {"noi_dung": "", "yeu_cau_goi_y": True})
    for _ in range(2):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Em nghĩ là 5", "dap_an_nhap": "5"})
    print("      đã xin 4 lần gợi ý + 2 lần trả lời sai → cờ cảnh báo tự phát sinh")


def main():
    p = argparse.ArgumentParser(description="Chuẩn bị dữ liệu demo cho Ban giám khảo")
    p.add_argument("--url", required=True, help="vd https://mathtutor-1.onrender.com")
    p.add_argument("--admin-user", required=True)
    p.add_argument("--admin-pass", required=True)
    p.add_argument("--chi-xem-truoc", action="store_true",
                   help="CHỈ in ra những gì sẽ làm, không ghi bất cứ thứ gì")
    args = p.parse_args()

    print("=== CHẾ ĐỘ XEM TRƯỚC — không ghi dữ liệu ===" if args.chi_xem_truoc
          else f"=== GHI DỮ LIỆU THẬT vào {args.url} ===")

    api = Api(args.url, args.chi_xem_truoc)
    api.dang_nhap(args.admin_user, args.admin_pass)
    print(f"Đã đăng nhập admin: {args.admin_user}")

    buoc_1_tai_khoan_va_lop(api)
    if args.chi_xem_truoc:
        print("\n(Xem trước dừng ở đây — các bước sau cần tài khoản đã thật sự tồn tại.)")
        return

    api_gv = Api(args.url, False)
    api_gv.dang_nhap("gvdemo", MAT_KHAU_THEO_TAI_KHOAN["gvdemo"])
    map_dang = buoc_2_danh_muc(api_gv)
    buoc_3_kho_cau_hoi(api_gv, map_dang)
    buoc_4_cau_cho_duyet(api_gv)
    buoc_5_lich_su_hoc(args.url, False)
    buoc_6_bai_dang_lam(args.url, False)

    print("\n" + "=" * 62)
    print("XONG. Tài khoản demo:")
    for dang_nhap, ho_ten, vai_tro, mat_khau in TAI_KHOAN_DEMO:
        print(f"  {dang_nhap:16} / {mat_khau:12} [{vai_tro}]  {ho_ten}")
    print("=" * 62)
    print("Kịch bản demo từng tài khoản: xem docs/DEMO_GIAM_KHAO.md")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"\nLỖI: {e}", file=sys.stderr)
        sys.exit(1)
