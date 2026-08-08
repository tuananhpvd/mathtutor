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

NHIỀU GIÁM KHẢO CÙNG CHẤM (bài học rút ra sau lần chạy đầu 2026-08-03): nếu 2-3 giám khảo
cùng thao tác trên MỘT tài khoản HS, họ dùng chung dữ liệu — mở cùng 1 bài sẽ rơi vào CÙNG 1
hội thoại (`tao_phien()` cố ý tái dùng phiên dang_lam thay vì tạo mới), và người sau sẽ không
còn thấy đúng trạng thái người trước để lại (làm nốt bài dở → hết bài dở; làm thêm bài đúng →
xóa mất "điểm yếu"). Học sinh cũng không xóa được sau khi có phiên học (`xoa_tai_khoan()` chặn
cứng) nên KHÔNG có cách "reset" tài khoản dựng sẵn.

→ Giải pháp: bật MÃ LỚP để mỗi giám khảo TỰ ĐĂNG KÝ một tài khoản HS riêng (mỗi người một
   phiên, một hạn mức AI riêng, không đụng ai). Tài khoản HS dựng sẵn (`hsdemo_dahoc`,
   `hsdemo_danglam`) chỉ còn vai trò XEM MẪU trạng thái đặc thù, không dùng để thao tác tự do
   — vì vậy đã BỎ hẳn `hsdemo_moi` (tự đăng ký đã thay thế đúng vai trò "học sinh mới" của
   nó, mà không có rủi ro bị phá).
→ `gvdemo` vẫn CHỈ MỘT tài khoản dùng chung — tách nhiều bộ GV sẽ làm mỗi lớp trống trơn vì
   mã lớp chỉ trỏ vào 1 lớp; gộp lại thì mọi hoạt động của giám khảo dồn về một dashboard,
   càng dùng càng sinh động (cờ cảnh báo tự sinh thêm khi có giám khảo bí bài).
→ Kho câu hỏi + câu chờ duyệt được "làm dày" (nhiều hơn mức tối thiểu) để chịu được nhiều
   giám khảo thao tác cùng lúc mà không cạn: mỗi dạng có nhiều bài "còn trống" hơn 1, và
   `hsdemo_dahoc` có NHIỀU phiên yếu hơn 2 (để một giám khảo lỡ làm thêm 1 bài đúng không kéo
   điểm thành thạo vọt qua ngưỡng 50%).

TÍNH IDEMPOTENT: chạy lại nhiều lần không nhân đôi dữ liệu. Riêng lịch sử học chỉ tạo khi học
sinh đó chưa có phiên hoàn thành nào, tránh cộng dồn ngoài ý muốn. Mã lớp: nếu lớp đã có mã
còn hiệu lực thì GIỮ NGUYÊN (gọi lại API sẽ ĐỔI mã và làm mã cũ đã phát cho giám khảo hỏng).

CÁCH CHẠY:
    cd backend
    .venv\\Scripts\\python.exe ..\\scripts\\chuan-bi-demo-giam-khao.py ^
        --url https://mathtutor.pro.vn ^
        --admin-user admin --admin-pass "<mật khẩu admin>"

    Thêm --chi-xem-truoc để CHỈ in ra những gì sẽ làm mà không ghi gì (nên chạy trước).

LƯU Ý VỀ HẠN MỨC AI: script tạo lịch sử học bằng cách gọi API thật, mỗi lượt trò chuyện tốn
1 lượt LLM. Nếu vượt `gioi_han_llm_hs_ngay`, hệ thống tự chuyển sang StubLLMClient — phiên vẫn
hoàn thành và số liệu tiến độ vẫn đúng, chỉ lời thoại là mẫu có sẵn. Không gây lỗi, nhưng nên
chạy lúc không trùng giờ học sinh thật đang dùng. Script cũng tự nâng hạn mức AI TOÀN HỆ THỐNG
(không đụng hạn mức mỗi học sinh — mỗi giám khảo tự đăng ký đã có 30 lượt/ngày riêng).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

from sympy import latex as sympy_latex
from sympy import sympify

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
    ("hsdemo_dahoc", "HS Demo - Đã có tiến độ", "hs", "hsdemo123"),
    ("hsdemo_danglam", "HS Demo - Đang làm dở", "hs", "hsdemo123"),
]
MAT_KHAU_THEO_TAI_KHOAN = {t[0]: t[3] for t in TAI_KHOAN_DEMO}

# Tài khoản đợt chạy trước không còn dùng nữa (xem giải thích ở docstring) — dọn nếu còn sót
# và chưa có phiên học nào (an toàn để xóa hẳn thay vì chỉ khóa).
TAI_KHOAN_CU_CAN_DON = ["hsdemo_moi"]

# Hạn mức AI TOÀN HỆ THỐNG tạm nâng trong đợt nhiều giám khảo cùng chấm (không đụng hạn mức
# MỖI học sinh — giữ 30/ngày là đủ vì giờ mỗi giám khảo có tài khoản tự đăng ký riêng).
GIOI_HAN_LLM_HE_THONG_MUC_TIEU = 2000

# Danh mục RIÊNG của gvdemo (ràng buộc #3). Tên đặt giống chương trình Toán 12 thật để
# giám khảo thấy tự nhiên, nhưng là bản riêng của lớp demo, không đụng danh mục GV thật.
DANH_MUC_DEMO = [
    ("Ứng dụng của đạo hàm", ["Tính đơn điệu của hàm số", "Cực trị của hàm số"]),
    ("Nguyên hàm và tích phân", ["Tích phân"]),
]


# ─────────────────────────── Kho câu hỏi của gvdemo ────────────────────────────
# `dang_ten` được script tra sang dang_id lúc chạy (KHÔNG hardcode id — id khác nhau giữa
# các môi trường). Mỗi dạng có ĐỦ 3 loại câu (TLN/TN4PA/TNDS) và trải đủ 3 mức độ (dễ/tb/khó)
# — vừa để giám khảo thấy đa dạng, vừa để `NGUONG_NHOM=2` của hồ sơ năng lực có đủ dữ liệu.
#
# `bo_qua_lich_su=True`: KHÔNG đưa vào lịch sử học tự động của hsdemo_dahoc (xem buoc_6) —
# dùng cho (a) câu "buffer" của dạng yếu để nhiều giám khảo vẫn còn bài chưa làm mà đề xuất,
# (b) câu của dạng "Cực trị" — CỐ Ý để dạng này hoàn toàn chưa có lịch sử, hiện trạng thái
# "chưa đủ dữ liệu" trên Bản đồ năng lực, một trạng thái thật đáng cho giám khảo thấy bên
# cạnh "mạnh"/"yếu". Câu loại TNDS thì KHÔNG BAO GIỜ được script tự làm (xem _dap_an_theo_de)
# nên không cần đánh dấu cờ này cho chúng — để giám khảo tự trải nghiệm luồng chọn Đúng/Sai.

CAU_HOI = [
    # ══ Dạng "Tính đơn điệu của hàm số" — hsdemo_dahoc làm TỐT (thành điểm mạnh) ══
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
    {
        # TNDS mức khó, không đưa vào lịch sử tự động — để giám khảo tự trải nghiệm câu 4 ý.
        "loai_cau": "TNDS", "do_kho": "kho", "dang_ten": "Tính đơn điệu của hàm số",
        "de_bai": "Cho hàm số $y = -x^3 + 3x + 2$. Xét tính đúng sai của các mệnh đề sau:",
        "meta": {
            "y": [
                {"ky_hieu": "a", "noi_dung_y": "$y' = -3x^2 + 3$", "dap_an": "Dung"},
                {"ky_hieu": "b", "noi_dung_y": "Hàm số đồng biến trên $(-1;1)$", "dap_an": "Dung"},
                {"ky_hieu": "c", "noi_dung_y": "Hàm số nghịch biến trên $(-2;0)$", "dap_an": "Sai"},
                {"ky_hieu": "d", "noi_dung_y": "$x=1$ là điểm cực đại của hàm số", "dap_an": "Dung"},
            ],
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "a", "mo_ta": "Kiểm tra công thức đạo hàm",
             "bieu_thuc_ket_qua": "-3*x**2 + 3",
             "danh_sach_goi_y": ["Em tự tính đạo hàm rồi so với mệnh đề.",
                                 "Đạo hàm của $-x^3$ là $-3x^2$, của $3x$ là $3$.",
                                 "So sánh kết quả em tính với biểu thức trong mệnh đề."]},
            {"thu_tu": 1, "pham_vi": "b", "mo_ta": "Xét dấu $y'$ trên khoảng $(-1;1)$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em thử thay $x=0$ vào $y'$ xem dấu ra sao.",
                                 "Nếu $y' > 0$ trên cả khoảng thì hàm đồng biến.",
                                 "Kiểm tra thêm 2 đầu khoảng để chắc dấu không đổi."]},
            {"thu_tu": 1, "pham_vi": "c", "mo_ta": "Xét dấu $y'$ trên khoảng $(-2;0)$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Khoảng $(-2;0)$ chứa nghiệm $x=-1$ của $y'=0$ — thử 2 phía.",
                                 "Thay $x=-1.5$ và $x=-0.5$ vào $y'$, so sánh dấu.",
                                 "Nếu dấu đổi giữa khoảng thì hàm không đơn điệu trên cả khoảng."]},
            {"thu_tu": 1, "pham_vi": "d", "mo_ta": "Xét dấu $y'$ hai bên $x=1$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em xét dấu $y'$ ngay trước và ngay sau $x=1$.",
                                 "Nếu $y'$ đổi từ dương sang âm thì đó là điểm cực đại.",
                                 "Thay $x=0.9$ và $x=1.1$ vào $y'$ để kiểm tra."]},
        ],
    },
    # ══ Dạng "Tích phân" — hsdemo_dahoc làm CHẬT VẬT (thành điểm yếu) ══
    # 4 câu hsdemo_dahoc làm SAI/xin nhiều gợi ý (buoc_6) + 3 câu "buffer" để trống (đủ cho
    # nhiều giám khảo vẫn còn bài mà "đề xuất theo điểm yếu") + 1 câu TNDS không đụng tới.
    {
        "loai_cau": "TLN", "do_kho": "de", "dang_ten": "Tích phân",
        "de_bai": "Tính tích phân $I = \\int_0^1 6x \\, dx$.",
        "meta": {"dap_an_cuoi": "3"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $6x$",
             "bieu_thuc_ket_qua": "3*x**2",
             "danh_sach_goi_y": ["Em nhớ công thức nguyên hàm của $x^n$.",
                                 "Nguyên hàm của $x$ là $\\frac{x^2}{2}$.",
                                 "Với $6x$, em nhân hệ số 6 vào nguyên hàm của $x$."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 0 và 1 rồi tính hiệu",
             "bieu_thuc_ket_qua": "3",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tại $x=1$: $3\\cdot1^2 = 3$. Tại $x=0$ thì bằng bao nhiêu?",
                                 "Lấy giá trị tại 1 trừ giá trị tại 0."]},
        ],
    },
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
        "loai_cau": "TN4PA", "do_kho": "tb", "dang_ten": "Tích phân",
        "de_bai": "Tính tích phân $I = \\int_1^3 (2x - 1) \\, dx$.",
        "meta": {
            "dap_an_dung": "B",
            "phuong_an": {"A": "4", "B": "6", "C": "8", "D": "5"},
            "bat_buoc_suy_luan": True,
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $2x-1$",
             "bieu_thuc_ket_qua": "x**2 - x",
             "danh_sach_goi_y": ["Em tìm nguyên hàm từng hạng tử một.",
                                 "Nguyên hàm của $2x$ là $x^2$, của $-1$ là $-x$.",
                                 "Cộng hai nguyên hàm vừa tìm lại với nhau."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 1 và 3 rồi tính hiệu",
             "bieu_thuc_ket_qua": "6",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tại $x=3$: $3^2-3=6$. Em tính tiếp tại $x=1$.",
                                 "Lấy giá trị tại 3 trừ giá trị tại 1."]},
        ],
    },
    {
        "loai_cau": "TLN", "do_kho": "de", "dang_ten": "Tích phân", "bo_qua_lich_su": True,
        "de_bai": "Tính tích phân $I = \\int_0^2 4x \\, dx$.",
        "meta": {"dap_an_cuoi": "8"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $4x$",
             "bieu_thuc_ket_qua": "2*x**2",
             "danh_sach_goi_y": ["Em nhớ công thức nguyên hàm của $x^n$.",
                                 "Nguyên hàm của $x$ là $\\frac{x^2}{2}$.",
                                 "Với $4x$, em nhân hệ số 4 vào nguyên hàm của $x$."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 0 và 2 rồi tính hiệu",
             "bieu_thuc_ket_qua": "8",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tại $x=2$: $2\\cdot2^2 = 8$. Tại $x=0$ thì bằng bao nhiêu?",
                                 "Lấy giá trị tại 2 trừ giá trị tại 0."]},
        ],
    },
    {
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
    {
        "loai_cau": "TLN", "do_kho": "kho", "dang_ten": "Tích phân", "bo_qua_lich_su": True,
        "de_bai": "Tính tích phân $I = \\int_1^2 (3x^2 - 4x + 1) \\, dx$.",
        "meta": {"dap_an_cuoi": "2"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm nguyên hàm của $3x^2 - 4x + 1$",
             "bieu_thuc_ket_qua": "x**3 - 2*x**2 + x",
             "danh_sach_goi_y": ["Em tìm nguyên hàm từng hạng tử một.",
                                 "Nguyên hàm của $3x^2$ là $x^3$, của $-4x$ là $-2x^2$, của $1$ là $x$.",
                                 "Cộng ba nguyên hàm vừa tìm lại với nhau."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay cận 1 và 2 rồi tính hiệu",
             "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới.",
                                 "Tại $x=2$: $8-8+2=2$. Em tính tiếp tại $x=1$.",
                                 "Lấy giá trị tại 2 trừ giá trị tại 1."]},
        ],
    },
    {
        "loai_cau": "TNDS", "do_kho": "kho", "dang_ten": "Tích phân", "bo_qua_lich_su": True,
        "de_bai": "Cho $I = \\int_0^1 (2x+1) \\, dx$. Xét tính đúng sai của các mệnh đề sau:",
        "meta": {
            "y": [
                {"ky_hieu": "a", "noi_dung_y": "Một nguyên hàm của $2x+1$ là $x^2+x$", "dap_an": "Dung"},
                {"ky_hieu": "b", "noi_dung_y": "$I = 2$", "dap_an": "Dung"},
                {"ky_hieu": "c", "noi_dung_y": "Nếu đổi cận thành $\\int_0^2$ thì kết quả bằng $4$",
                 "dap_an": "Sai"},
                {"ky_hieu": "d", "noi_dung_y": "Hàm số $2x+1$ luôn dương trên đoạn $[0;1]$",
                 "dap_an": "Dung"},
            ],
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "a", "mo_ta": "Kiểm tra nguyên hàm",
             "bieu_thuc_ket_qua": "x**2 + x",
             "danh_sach_goi_y": ["Em tìm nguyên hàm của $2x+1$ rồi so với mệnh đề.",
                                 "Nguyên hàm của $2x$ là $x^2$, của $1$ là $x$.",
                                 "Cộng hai kết quả lại rồi so sánh."]},
            {"thu_tu": 1, "pham_vi": "b", "mo_ta": "Tính $I$ bằng cách thay cận",
             "bieu_thuc_ket_qua": "2",
             "danh_sach_goi_y": ["Em thay cận trên trừ cận dưới vào nguyên hàm vừa tìm.",
                                 "Tại $x=1$: $1+1=2$. Tại $x=0$ thì bằng bao nhiêu?",
                                 "Lấy giá trị tại 1 trừ giá trị tại 0."]},
            {"thu_tu": 1, "pham_vi": "c", "mo_ta": "Tính lại với cận mới $0$ đến $2$",
             "bieu_thuc_ket_qua": "6",
             "danh_sach_goi_y": ["Em thay cận trên là 2 vào nguyên hàm $x^2+x$.",
                                 "Tại $x=2$: $4+2=6$. So sánh với con số $4$ trong mệnh đề.",
                                 "Kết quả có khớp $4$ không?"]},
            {"thu_tu": 1, "pham_vi": "d", "mo_ta": "Xét dấu $2x+1$ trên $[0;1]$",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em thử thay $x=0$ và $x=1$ vào biểu thức $2x+1$.",
                                 "Cả hai đầu đoạn cho giá trị dương thì trên cả đoạn dương.",
                                 "$2x+1$ có nghiệm âm ở đâu không trong đoạn $[0;1]$?"]},
        ],
    },
    # ══ Dạng "Cực trị của hàm số" — CỐ Ý để trống hoàn toàn (chưa đủ dữ liệu) ══
    # Cả 3 câu đều bo_qua_lich_su — dạng này hiện trạng thái "chưa đủ dữ liệu" trên Bản đồ
    # năng lực, một trạng thái thật (khác mạnh/yếu) đáng cho giám khảo thấy, và để dành cho
    # giám khảo tự làm qua tài khoản tự đăng ký.
    {
        "loai_cau": "TLN", "do_kho": "de", "dang_ten": "Cực trị của hàm số", "bo_qua_lich_su": True,
        "de_bai": "Cho hàm số $f(x) = x^2 - 6x + 5$. Tìm giá trị cực tiểu của hàm số.",
        "meta": {"dap_an_cuoi": "-4"},
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tìm hoành độ điểm cực tiểu",
             "bieu_thuc_ket_qua": "3",
             "danh_sach_goi_y": ["Em tính đạo hàm rồi cho bằng 0 để tìm hoành độ.",
                                 "Đạo hàm là $2x-6$, giải $2x-6=0$.",
                                 "Nghiệm tìm được chính là hoành độ điểm cực tiểu."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Thay hoành độ vào hàm số ban đầu",
             "bieu_thuc_ket_qua": "-4",
             "danh_sach_goi_y": ["Em thay giá trị $x$ vừa tìm vào $f(x)$.",
                                 "Tính $3^2 - 6\\cdot3 + 5$.",
                                 "Kết quả chính là giá trị cực tiểu cần tìm."]},
        ],
    },
    {
        "loai_cau": "TN4PA", "do_kho": "kho", "dang_ten": "Cực trị của hàm số", "bo_qua_lich_su": True,
        "de_bai": "Số điểm cực trị của hàm số $y = x^4 - 2x^2 + 1$ là?",
        "meta": {
            "dap_an_dung": "C",
            "phuong_an": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "bat_buoc_suy_luan": True,
        },
        "solution_steps": [
            {"thu_tu": 1, "pham_vi": "ca_bai", "mo_ta": "Tính đạo hàm $y'$",
             "bieu_thuc_ket_qua": "4*x**3 - 4*x",
             "danh_sach_goi_y": ["Em tính đạo hàm của hàm số đã cho.",
                                 "Đạo hàm của $x^4$ là $4x^3$, của $-2x^2$ là $-4x$."]},
            {"thu_tu": 2, "pham_vi": "ca_bai", "mo_ta": "Đếm số nghiệm của $y'=0$ mà đạo hàm đổi dấu",
             "bieu_thuc_ket_qua": "",
             "danh_sach_goi_y": ["Em phân tích $4x^3-4x = 4x(x^2-1)$ rồi tìm nghiệm.",
                                 "Phương trình có 3 nghiệm phân biệt: $x=0, x=1, x=-1$.",
                                 "Mỗi nghiệm đơn của đa thức bậc lẻ đều làm đạo hàm đổi dấu."]},
        ],
    },
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
# Làm dày hơn mức tối thiểu để nhiều giám khảo vẫn còn câu để thao tác cùng lúc.
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
    {"loai_cau": "TLN", "chuyen_de": "Ứng dụng của đạo hàm", "do_kho": "de",
     "de_bai": "[Bản nháp chờ duyệt] Cho $f(x) = 4x - 1$. Tính $f'(x)$.",
     "meta": {"dap_an_cuoi": "4"}},
    {"loai_cau": "TLN", "chuyen_de": "Ứng dụng của đạo hàm", "do_kho": "tb",
     "de_bai": "[Bản nháp chờ duyệt] Cho $f(x) = x^2 - 8x + 1$. Tìm $x$ để $f'(x) = 0$.",
     "meta": {"dap_an_cuoi": "4"}},
    {"loai_cau": "TLN", "chuyen_de": "Nguyên hàm và tích phân", "do_kho": "de",
     "de_bai": "[Bản nháp chờ duyệt] Tính $\\int_0^2 5 \\, dx$.",
     "meta": {"dap_an_cuoi": "10"}},
    {"loai_cau": "TLN", "chuyen_de": "Nguyên hàm và tích phân", "do_kho": "tb",
     "de_bai": "[Bản nháp chờ duyệt] Tính $\\int_1^3 4x \\, dx$.",
     "meta": {"dap_an_cuoi": "16"}},
    {"loai_cau": "TLN", "chuyen_de": "Nguyên hàm và tích phân", "do_kho": "kho",
     "de_bai": "[Bản nháp chờ duyệt] Tính $\\int_0^1 (6x^2 + 2x) \\, dx$.",
     "meta": {"dap_an_cuoi": "3"}},
    {"loai_cau": "TLN", "chuyen_de": "Ứng dụng của đạo hàm", "do_kho": "de",
     "de_bai": "[Bản nháp chờ duyệt] Cho $f(x) = x^2 + 2x$. Tính $f'(1)$.",
     "meta": {"dap_an_cuoi": "4"}},
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

    def delete(self, dd):
        return self._goi("DELETE", dd, ghi=True)

    def dang_nhap(self, dang_nhap: str, mat_khau: str):
        # Đăng nhập không phải thao tác ghi → chạy cả ở chế độ xem trước.
        kq = self._goi("POST", "/auth/login", {"dang_nhap": dang_nhap, "mat_khau": mat_khau})
        self.token = kq["access_token"]
        return kq


def buoc_1_don_dep_tai_khoan_cu(api: Api, users: list[dict]) -> None:
    """Xóa tài khoản đợt trước không còn dùng (TAI_KHOAN_CU_CAN_DON), CHỈ khi chưa có phiên
    học nào — nếu hệ thống từ chối (đã có dữ liệu) thì báo và bỏ qua, không chặn script."""
    theo_ten = {u["dang_nhap"]: u for u in users}
    for dang_nhap in TAI_KHOAN_CU_CAN_DON:
        u = theo_ten.get(dang_nhap)
        if u is None:
            continue
        try:
            api.delete(f"/admin/users/{u['id']}")
            print(f"      ĐÃ XÓA tài khoản cũ không còn dùng: {dang_nhap}")
        except RuntimeError as e:
            print(f"      !! không xóa được {dang_nhap} (có thể đã có dữ liệu): {e}")


def buoc_2_tai_khoan_va_lop(api: Api) -> dict:
    print("\n[2/8] Tài khoản và lớp demo")
    users = api.get("/admin/users") or []
    buoc_1_don_dep_tai_khoan_cu(api, users)
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

    for dang_nhap in ("hsdemo_dahoc", "hsdemo_danglam"):
        if dang_nhap in ids and lop_id:
            api.patch(f"/admin/users/{ids[dang_nhap]}/lop", {"lop_id": lop_id})
            print(f"      gán {dang_nhap} → lớp demo")
    return {"ids": ids, "lop_id": lop_id}


def buoc_3_ma_lop(api_gv: Api, lop_id: int | None) -> str | None:
    """Bật mã lớp để giám khảo TỰ ĐĂNG KÝ tài khoản HS riêng (xem giải thích ở docstring).
    KHÔNG gọi lại nếu lớp đã có mã CÒN HIỆU LỰC — gọi lại sẽ ĐỔI mã, làm mã cũ đã phát hỏng.
    `GET /gv/lop` trả `ma_lop` bất kể còn hạn hay không (chỉ `lop_theo_ma()` lúc đăng ký mới
    kiểm hạn) — nên phải tự so `ma_het_han` với giờ hiện tại ở đây, không thể chỉ kiểm tồn
    tại."""
    from datetime import datetime, timezone

    print("\n[3/8] Mã lớp để giám khảo tự đăng ký")
    if lop_id is None:
        print("      !! không có lop_id (chế độ xem trước) — bỏ qua")
        return None
    cac_lop = api_gv.get("/gv/lop") or []
    lop = next((x for x in cac_lop if x["id"] == lop_id), None)
    het_han_raw = lop.get("ma_het_han") if lop else None
    het_han = datetime.fromisoformat(het_han_raw) if het_han_raw else None
    if het_han is not None and het_han.tzinfo is None:
        het_han = het_han.replace(tzinfo=timezone.utc)  # phòng trường hợp cột không có offset
    con_hieu_luc = het_han is not None and het_han > datetime.now(timezone.utc)
    if lop and lop.get("ma_lop") and con_hieu_luc:
        print(f"      đã có mã còn hiệu lực, GIỮ NGUYÊN: {lop['ma_lop']} (hết hạn {het_han})")
        return lop["ma_lop"]
    kq = api_gv.post(f"/gv/lop/{lop_id}/ma")
    ma = kq["ma_lop"] if kq else None
    print(f"      TẠO MỚI mã lớp (mã cũ nếu có đã hết hạn/không tồn tại): {ma}")
    return ma


def buoc_4_danh_muc(api_gv: Api) -> dict[str, int]:
    """Danh mục RIÊNG của gvdemo (ràng buộc #3) → trả map {tên dạng: dang_id}."""
    print("\n[4/8] Danh mục (chuyên đề + dạng) riêng của gvdemo")
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


def buoc_5_kho_cau_hoi(api_gv: Api, map_dang: dict[str, int]):
    """Kho câu hỏi thuộc sở hữu gvdemo (ràng buộc #1, #2) — có bước giải + thang gợi ý."""
    print("\n[5/8] Kho câu hỏi của gvdemo (đã duyệt, có bước giải + thang gợi ý)")
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


def buoc_6_cau_cho_duyet(api_gv: Api):
    print("\n[6/8] Câu hỏi 'chờ duyệt' cho giám khảo thao tác kiểm duyệt")
    hien_co = api_gv.get("/problems") or []
    so_cho_duyet = sum(1 for p in hien_co if p.get("trang_thai_duyet") == "cho_duyet")
    if so_cho_duyet >= len(CAU_HOI_CHO_DUYET):
        print(f"      đã có {so_cho_duyet} câu chờ duyệt — bỏ qua")
        return
    kq = api_gv.post("/problems/import-batch", {"items": CAU_HOI_CHO_DUYET})
    if kq:
        print(f"      đã tạo {kq.get('da_tao', '?')} câu ở trạng thái chờ duyệt")


def _sang_latex(bieu_thuc: str) -> str:
    """Chuyển biểu thức cú pháp SymPy (như lưu trong CSDL "bieu_thuc_ket_qua", vd
    "x**4 - x**2") sang LaTeX ("x^{4} - x^{2}") để HIỂN THỊ trong "noi_dung".

    Sự cố thực tế phát hiện (giám khảo báo, 2026-08-08): học sinh THẬT nhập qua math-field
    editor nên luôn gửi LaTeX (`AnswerInputTLN.jsx`, biến đặt tên "bieu_thuc" nhưng thật ra là
    LaTeX lấy từ `mf.value`), KHÔNG BAO GIỜ gửi cú pháp SymPy. Bọc thẳng cú pháp SymPy vào
    "$...$" khiến KaTeX không hiểu "**" — hiện dấu sao thô ("x**4") thay vì số mũ đẹp.
    Chỉ dùng cho HIỂN THỊ — "dap_an_nhap" gửi API vẫn giữ nguyên cú pháp SymPy, CAS
    (`_parse_an_toan`) chấp nhận cả 2 cú pháp nên không cần đổi, và đổi có thể làm sai lệch
    biểu thức nếu latex hoá rồi diễn giải lại.
    """
    try:
        return sympy_latex(sympify(bieu_thuc))
    except Exception:
        return bieu_thuc  # không parse được thì giữ nguyên, còn hơn làm hỏng cả tin nhắn


def _dap_an_theo_de() -> dict[str, list[tuple[str, str]]]:
    """Đáp án đúng từng bước, kèm SẴN "noi_dung" ĐÚNG NGUYÊN VĂN định dạng frontend thật dùng
    cho từng loại hành động — để phiên demo do script dựng hiển thị Y HỆT phiên của học sinh
    thật khi GV mở "Xem lại bài", không lộ dấu vết dựng sẵn.

    Sự cố thực tế phát hiện (giám khảo báo, 2026-08-08): script tự soạn "noi_dung" khác quy
    ước frontend — (1) trả lời KHÔNG bọc "$...$" như `AnswerInputTLN.jsx` ('Em trả lời:
    $${bieu_thuc}$') nên công thức hiện chữ thường không qua KaTeX; (2) TN4PA đáp án cuối là
    CHỮ CÁI, frontend dùng mẫu KHÁC hẳn ('Em chọn: ${chon}' — `AnswerInputTN4PA.jsx`), không
    bọc $ vì không phải công thức; (3) dù đã bọc $...$, nội dung bên trong vẫn là cú pháp
    SymPy ("x**4") thay vì LaTeX ("x^{4}") — xem `_sang_latex`.

    CHỈ điền cho TLN/TN4PA — TNDS cần luồng chọn Đúng/Sai riêng, để giám khảo tự trải nghiệm.
    """
    ra: dict[str, list[tuple[str, str]]] = {}  # de_bai -> [(dap_an_nhap, noi_dung), ...]
    for cau in CAU_HOI:
        khoa = cau["de_bai"][:60]
        buoc = [b["bieu_thuc_ket_qua"] for b in cau["solution_steps"] if b["bieu_thuc_ket_qua"]]
        cac_buoc = [(bt, f"Em trả lời: ${_sang_latex(bt)}$") for bt in buoc]
        if cau["loai_cau"] == "TLN":
            ra[khoa] = cac_buoc
        elif cau["loai_cau"] == "TN4PA":
            chu_cai = cau["meta"]["dap_an_dung"]
            ra[khoa] = cac_buoc + [(chu_cai, f"Em chọn: {chu_cai}")]
    return ra


def _lam_bai(api_hs: Api, problem_id: int, cac_dap_an: list[tuple[str, str]],
             so_lan_xin_goi_y: int = 0, so_lan_sai: int = 0) -> bool:
    """Mở 1 phiên rồi làm bài. `so_lan_xin_goi_y`/`so_lan_sai` dùng để nặn ra hồ sơ năng lực
    ĐA DẠNG — điểm thành thạo tính theo `1.0 - 0.1*số lần sai - 0.15*số lần xin gợi ý`, nên
    muốn có "điểm yếu" (thành thạo < 50) thì phải cố ý sai + xin gợi ý nhiều lần.

    Mọi "noi_dung" gửi lên đều dùng ĐÚNG NGUYÊN VĂN mẫu câu frontend thật tạo ra cho hành động
    tương ứng (xem `PhongHoc.jsx`/`AnswerInputTLN.jsx`) — không tự bịa câu khác, để "Xem lại
    bài" không có bong bóng trống hay công thức hiện sai.
    """
    phien = api_hs.post("/sessions", {"problem_id": problem_id})
    if not phien:
        return False
    sid = phien["session_id"]

    for _ in range(so_lan_xin_goi_y):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Xin thầy/cô gợi ý thêm cho em", "yeu_cau_goi_y": True})
    for _ in range(so_lan_sai):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Em trả lời: $99999$", "dap_an_nhap": "99999"})
    for dap_an, noi_dung in cac_dap_an:
        kq = api_hs.post(f"/sessions/{sid}/message",
                         {"noi_dung": noi_dung, "dap_an_nhap": dap_an})
        if kq and kq.get("da_xong"):
            return True
    return False


def buoc_7_lich_su_hoc(url: str, chi_xem_truoc: bool):
    """hsdemo_dahoc: LÀM TỐT dạng "Tính đơn điệu", CHẬT VẬT dạng "Tích phân" (NHIỀU phiên
    yếu — chống mài mòn: một giám khảo lỡ làm thêm 1 bài đúng không kéo điểm thành thạo vọt
    qua ngưỡng 50%). Dạng "Cực trị" CỐ Ý không đụng tới (xem CAU_HOI) — hiện "chưa đủ dữ liệu".

    Nếu làm đúng hết mọi thứ, `diem_yeu` sẽ rỗng và các tính năng cá nhân hóa ("Bài nên luyện
    tiếp" của HS, "đề xuất theo điểm yếu" của GV, màu sắc trên Bản đồ năng lực) không hiện gì.
    """
    print("\n[7/8] Lịch sử học cho hsdemo_dahoc (có cả điểm mạnh lẫn điểm yếu)")
    api_hs = Api(url, chi_xem_truoc)
    api_hs.dang_nhap("hsdemo_dahoc", MAT_KHAU_THEO_TAI_KHOAN["hsdemo_dahoc"])

    tien_do = api_hs.get("/progress/me") or []
    if sum(t.get("so_bai_hoan_thanh", 0) for t in tien_do) >= 6:
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


def buoc_8_bai_dang_lam(url: str, chi_xem_truoc: bool):
    """hsdemo_danglam: 1 bài dở + xin gợi ý tới cạn → cờ 'không hiểu nhiều' TỰ phát sinh.

    Cố ý KHÔNG gọi API tạo cờ thủ công: để cờ sinh ra đúng cơ chế thật của sản phẩm, giám
    khảo thấy được cảnh báo tự động chứ không phải dữ liệu dựng sẵn.
    """
    print("\n[8/8] Bài đang làm dở + cờ cảnh báo tự phát sinh cho gvdemo xử lý")
    api_hs = Api(url, chi_xem_truoc)
    api_hs.dang_nhap("hsdemo_danglam", MAT_KHAU_THEO_TAI_KHOAN["hsdemo_danglam"])

    if api_hs.get("/sessions/dang-do"):
        print("      đã có bài đang làm dở — bỏ qua")
        return

    bai_hs = api_hs.get("/problems") or []
    bai = next((b for b in bai_hs if b.get("do_kho") == "kho"), bai_hs[0] if bai_hs else None)
    if not bai:
        print("      !! không có bài nào — kiểm tra lại bước 5")
        return

    phien = api_hs.post("/sessions", {"problem_id": bai["id"]})
    if not phien:
        return
    sid = phien["session_id"]
    print(f"      mở bài: {bai.get('de_bai', '')[:45]}...")
    for _ in range(4):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Xin thầy/cô gợi ý thêm cho em", "yeu_cau_goi_y": True})
    for _ in range(2):
        api_hs.post(f"/sessions/{sid}/message",
                    {"noi_dung": "Em trả lời: $5$", "dap_an_nhap": "5"})
    print("      đã xin 4 lần gợi ý + 2 lần trả lời sai → cờ cảnh báo tự phát sinh")


def buoc_9_han_muc_ai(api: Api):
    """Nâng hạn mức AI TOÀN HỆ THỐNG (không đụng hạn mức mỗi học sinh) — nhiều giám khảo tự
    đăng ký cùng lúc có thể cộng dồn vượt hạn mức hệ thống dù mỗi người còn quota riêng."""
    print("\n[9/8] Hạn mức AI toàn hệ thống")
    cau_hinh = api.get("/admin/config") or {}
    hien_tai = cau_hinh.get("gioi_han_llm_he_thong_ngay")
    if isinstance(hien_tai, int) and hien_tai >= GIOI_HAN_LLM_HE_THONG_MUC_TIEU:
        print(f"      đã đủ cao ({hien_tai}) — giữ nguyên")
        return
    api.patch("/admin/config", {"khoa": "gioi_han_llm_he_thong_ngay",
                                "gia_tri": GIOI_HAN_LLM_HE_THONG_MUC_TIEU})
    print(f"      nâng gioi_han_llm_he_thong_ngay: {hien_tai} → {GIOI_HAN_LLM_HE_THONG_MUC_TIEU}")


def main():
    p = argparse.ArgumentParser(description="Chuẩn bị dữ liệu demo cho Ban giám khảo")
    p.add_argument("--url", required=True, help="vd https://mathtutor.pro.vn")
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

    thong_tin_lop = buoc_2_tai_khoan_va_lop(api)
    if args.chi_xem_truoc:
        print("\n(Xem trước dừng ở đây — các bước sau cần tài khoản đã thật sự tồn tại.)")
        return

    api_gv = Api(args.url, False)
    api_gv.dang_nhap("gvdemo", MAT_KHAU_THEO_TAI_KHOAN["gvdemo"])
    ma_lop = buoc_3_ma_lop(api_gv, thong_tin_lop.get("lop_id"))
    map_dang = buoc_4_danh_muc(api_gv)
    buoc_5_kho_cau_hoi(api_gv, map_dang)
    buoc_6_cau_cho_duyet(api_gv)
    buoc_7_lich_su_hoc(args.url, False)
    buoc_8_bai_dang_lam(args.url, False)
    buoc_9_han_muc_ai(api)

    print("\n" + "=" * 62)
    print("XONG. Tài khoản demo:")
    for dang_nhap, ho_ten, vai_tro, mat_khau in TAI_KHOAN_DEMO:
        print(f"  {dang_nhap:16} / {mat_khau:12} [{vai_tro}]  {ho_ten}")
    print(f"\nMã lớp để giám khảo tự đăng ký: {ma_lop}")
    print("=" * 62)
    print("Kịch bản demo từng tài khoản: xem docs/DEMO_GIAM_KHAO.md")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"\nLỖI: {e}", file=sys.stderr)
        sys.exit(1)
