# PHASE_PROMPTS.md — Prompt copy-paste vào Claude Code (v3)

Mỗi phase copy nguyên khối dán vào Claude Code. MỌI prompt đều ngầm yêu cầu vòng lặp
**tự build → test → fix đến hết lỗi → báo cáo lỗi đã gặp & cách xử lý** (đã quy định trong
CLAUDE.md mục 2). Làm xong một phase mới sang phase kế.

---

## Prompt khởi động (chạy 1 lần)

```
Đây là dự án MathTutor tại D:\claude\mathtutor. Đọc CLAUDE.md và toàn bộ docs/ (ARCHITECTURE.md,
DATA_MODEL.md, PLAN.md, PROMPTS_LLM.md, UIUX_DESIGN.md, TESTING.md).

Tóm tắt bằng lời của bạn: (1) sản phẩm và 3 vai trò; (2) mô hình "kịch bản mềm"; (3) nguyên tắc
bất biến; (4) vòng lặp tự build-test-fix bạn sẽ áp dụng mỗi bước; (5) kế hoạch 12 phase.
Liệt kê quyết định kỹ thuật bạn sẽ chốt (thư viện, cấu trúc). KHÔNG viết code. Dừng cho tôi xác nhận.
```

---

## Phase 0 — Khởi tạo + auth/phân quyền

```
Thực hiện Phase 0 (PLAN.md) tại D:\claude\mathtutor theo cây thư mục ARCHITECTURE.md.

- backend FastAPI: config đọc env, SQLAlchemy (DATABASE_URL mặc định sqlite:///dev.db),
  pyproject (ruff/black/pytest), .env.example (JWT_SECRET, LLM_PROVIDER=stub...).
- auth: bcrypt + JWT + require_role(admin|gv|hs); models users, lop; seed 3 tài khoản (DATA_MODEL mục 9).
- API: POST /api/auth/login, GET /api/health, mỗi vai trò 1 route thử.
- frontend Vite+React+Tailwind: trang Login, lưu token, điều hướng theo vai trò.
- git init + .gitignore (Python+Node).

Sau đó TỰ chạy vòng lặp build-test-fix đến khi xanh (ruff + import smoke + pytest + npm run build).
Báo cáo theo mẫu trong CLAUDE.md mục 2 (build/test/lỗi đã gặp/cách xử lý/DoD). Đề xuất commit. Dừng.
```

---

## Phase 1 — Lõi so khớp CAS + parse_latex + bậc thang

```
Thực hiện Phase 1 (PLAN.md): module core/matching THUẦN PYTHON (không import fastapi/llm/db).

- app/core/matching/cas.py: tuong_duong(hs, chuan, che_do, lam_tron=None) dùng SymPy
  (lấy hiệu hai biểu thức, simplify, =0 thì tương đương). che_do: "tuong_duong" hoặc "dung_dang"
  (dung_dang yêu cầu cùng dạng chuẩn hóa). Parse an toàn; lỗi -> KHONG_PHAN_TICH_DUOC.
- app/core/matching/latex.py: latex_sang_sympy(latex_str) dùng sympy parse_latex (cài antlr4
  nếu cần); bắt lỗi rõ ràng.
- app/core/matching/scoring.py: diem_bac_thang(k) -> 0/0.1/0.25/0.5/1.0.
- app/core/matching/matcher.py: so_khop(loai_cau, dap_an_nhap, du_lieu_chuan, che_do_so_khop).

Viết test theo TESTING.md Phase 1. TỰ build-test-fix đến xanh. Báo cáo + commit. Dừng.
```

---

## Phase 2 — Điều phối + lát cắt dọc TLN + editor cơ bản

```
Thực hiện Phase 2 (PLAN.md): core/orchestrator THUẦN PYTHON + chạy trọn 1 bài TLN với LLM stub
+ nhập công thức qua editor.

- orchestrator: state.py, rules.py (quy tắc mục 4 đặc tả), directive.py (ChiThi gồm y_dinh, buoc,
  y_dang_xet, cap_goi_y, y_goi_y (Ý CHÍNH lấy từ danh_sach_goi_y[cap_goi_y]), ngu_canh_hs,
  rang_buoc cấm lộ đáp án). SỐ GỢI Ý MỖI BƯỚC LINH HOẠT: đọc len(step.danh_sach_goi_y), không
  hard-code 3; nâng cap_goi_y tới tối đa = độ dài danh sách rồi dừng nâng.
- llm/client.py: chỉ StubLLMClient.dien_dat(chi_thi) tất định từ y_goi_y.
- services/tutor_service: message -> matching -> orchestrator -> stub.
- models problem/solution_step/session/turn + repository; seed bài TLN (DATA_MODEL 10.1).
- API POST /api/sessions, /api/sessions/{id}/message.
- frontend: Formula.jsx (KaTeX), FormulaEditor.jsx (MathLive cơ bản), PhongHoc tối giản gọi API.

Viết test orchestrator (đúng liên tục; sai -> hỏi ngược; xin gợi ý tới hết danh sách của bước —
với bài tb là 3, kiểm dừng nâng đúng khi hết danh sách). TỰ build-test-fix
đến xanh. NHẮC: orchestrator không import llm; ChiThi không chứa giá trị đáp án. Báo cáo + commit. Dừng.
```

---

## Phase 3 — TN4PA & TNDS + LLM thật + hội thoại tự nhiên

```
Thực hiện Phase 3 (PLAN.md).

- orchestrator: TN4PA (dẫn tìm kết quả rồi đối chiếu phương án; chọn bừa -> yêu cầu loại trừ);
  TNDS (vòng lặp từng ý a->d, y_hien_tai, tổng hợp điểm bậc thang).
- llm/client.py: thêm provider thật (OpenAI hoặc Gemini) đọc env; prompts.py theo PROMPTS_LLM.md.
  LLM diễn đạt TỰ NHIÊN từ y_goi_y + ngu_canh_hs, được trả lời câu hỏi phụ trong phạm vi bài.
  Nhiệt độ thấp. Lỗi API -> gợi ý mặc định từ y_goi_y, không sập.
- seed thêm TN4PA (10.2) và TNDS (10.3); API answer trả kết quả theo loại (TNDS kèm bậc thang).

Viết test orchestrator TNDS/TN4PA (TESTING.md Phase 3). TỰ build-test-fix đến xanh (với
LLM_PROVIDER=stub). Báo cáo + commit. Dừng. NHẮC: mọi prompt nằm trong prompts.py.
```

---

## Phase 4 — Sáu lớp kiểm soát + gắn cờ + giám sát

```
Thực hiện Phase 4 (PLAN.md): core/guard đầy đủ + lưới an toàn.

- answer_guard.py: ra_soat(van_ban, du_lieu_chuan) phát hiện chứa dap_an_cuoi/dap_an ý/
  bieu_thuc_ket_qua (so chuỗi chuẩn hóa VÀ so giá trị số qua CAS). Lộ -> yêu cầu LLM viết lại 1
  lần với ràng buộc mạnh; vẫn lộ -> thay câu an toàn từ y_goi_y. Ghi co_bi_chot_chan vào Turn.
- scope.py khóa phạm vi; safety.py lọc lứa tuổi + dấu hiệu khó khăn tâm lý (-> thông điệp hỗ trợ,
  không dẫn toán tiếp).
- ghép guard vào tutor_service đúng thứ tự ARCHITECTURE mục 3.
- flag logic + monitor_service; API /api/monitor/flags, /sessions/{id}, /flags/{id}/done.

Viết test BỘ CA BẪY 3 loại + scope + safety + flag (TESTING.md Phase 4). TỰ build-test-fix đến
xanh. Báo cáo + commit. Dừng.
```

---

## Phase 5 — AI sinh câu hỏi + GV duyệt

```
Thực hiện Phase 5 (PLAN.md).

- llm/question_gen.py + services/question_gen_service: nhận yêu cầu (chuyên đề/loại/độ khó/số
  lượng) hoặc tài liệu nguồn; LLM trả JSON đúng mẫu (PROMPTS_LLM.md mục sinh câu hỏi cho TN4PA/
  TNDS/TLN); validate JSON + SymPy parse được bieu_thuc_ket_qua; cảnh báo nếu không parse được.
- SỐ GỢI Ý theo độ khó (Phương án C): LLM sinh danh_sach_goi_y với độ dài theo bảng mặc định
  (de→2, tb→3, kho→4, đọc từ cấu hình); GV thêm/bớt khi duyệt.
- API POST /api/questions-ai/generate, POST /api/questions-ai/{id}/duyet (gv).
- câu sinh ở trang_thai_duyet=cho_duyet; chỉ da_duyet mới tới HS.

Viết test: sinh đúng mẫu 3 loại với số gợi ý theo độ khó; câu chưa duyệt KHÔNG xuất hiện trong
GET /api/problems của HS.
TỰ build-test-fix đến xanh. Báo cáo + commit. Dừng.
```

---

## Phase 6 — Tiến độ + làm tiếp bài dở

```
Thực hiện Phase 6 (PLAN.md).

- progress_service: cập nhật progress khi xong bài; GET /api/progress/me (hs),
  GET /api/progress/students (gv, lớp mình).
- khôi phục phiên: GET /api/sessions/dang-do; mở lại đúng buoc_hien_tai/y_hien_tai/trang_thai_y/bộ đếm.

Viết test khôi phục phiên + tính progress. TỰ build-test-fix đến xanh. Báo cáo + commit. Dừng.
```

---

## Phase 7 — Thiết kế UI/UX (đọc UIUX_DESIGN.md, có thể dùng Claude Design)

```
Thực hiện Phase 7 (PLAN.md) theo docs/UIUX_DESIGN.md. Mục tiêu: hệ thống thiết kế nhất quán
TRƯỚC khi dựng nhiều trang.

- Chốt design tokens (màu, typography, spacing, radius, shadow) -> frontend/src/styles.
- Dựng bộ component cơ bản Tailwind: Button, Card, Input, Select, Badge trạng thái, Table,
  ProgressChart, RoleLayout (3 bố cục theo vai trò).
- Phác layout 4 màn hình trụ cột: Login, PhongHoc (HS), Dashboard GV, Dashboard Admin.

GỢI Ý: nếu tôi cung cấp thiết kế từ Claude Design, hãy chuyển thành component React+Tailwind
khớp tokens. Nếu chưa có, tự đề xuất thiết kế theo UIUX_DESIGN.md.

TỰ build-test-fix (npm run build) đến xanh; render thử các component. Báo cáo + commit. Dừng.
```

> Tùy chọn dùng Claude Design: xem quy trình trong `docs/UIUX_DESIGN.md` mục 4. Bạn có thể tạo
> thiết kế các màn hình ở Claude Design rồi đưa cho Claude Code chuyển sang code ở phase này.

---

## Phase 8 — Frontend Học sinh

```
Thực hiện Phase 8 (PLAN.md). Dựng đầy đủ khu vực Học sinh dùng tokens & component Phase 7.

- pages/hs: TrangChu (bảng tiến độ + bài đang dở, nút làm tiếp), ChonBai (lọc chủ đề/loại/mức độ),
  PhongHoc (hội thoại + vùng nhập theo loại + FormulaEditor + bản render xác nhận + nút "Em chưa hiểu"),
  KetThuc (TNDS hiện số ý đúng + điểm bậc thang), TienDo.
- AnswerInputTN4PA/TNDS/TLN, ProgressChart, nối api.js.

TỰ build-test-fix đến xanh; mô tả cách thử luồng e2e. Báo cáo + commit. Dừng.
```

---

## Phase 9 — Frontend Giáo viên

```
Thực hiện Phase 9 (PLAN.md). Khu vực Giáo viên.

- pages/gv: QuanLyCauHoi (danh sách + lọc + trạng thái duyệt), SoanBai (sửa đề/bước/ý gợi ý),
  AISinhCauHoi (nhập yêu cầu/tải tài liệu -> xem nháp -> duyệt/sửa/loại), QuanLyCo (hàng đợi cờ +
  xem nhật ký + đánh dấu xử lý), QuanLyHocSinh, TheoDoiTienBo (bảng + biểu đồ).

TỰ build-test-fix đến xanh. Báo cáo + commit. Dừng.
```

---

## Phase 10 — Frontend Quản trị

```
Thực hiện Phase 10 (PLAN.md). Khu vực Quản trị.

- pages/admin: Dashboard (số người dùng/bài/phiên/cờ chưa xử lý/mức dùng LLM), QuanLyTaiKhoan
  (tạo/khóa GV-HS, phân quyền, gán GV-lớp), CauHinh (ngưỡng cờ, nhiệt độ LLM, bảng bậc thang),
  NhatKy. API /api/admin/...

TỰ build-test-fix đến xanh; kiểm phân quyền chặn HS/GV vào admin. Báo cáo + commit. Dừng.
```

---

## Phase 11 — Hoàn thiện + demo + rà DoD

```
Thực hiện Phase 11 (PLAN.md).

- seed đủ 2-3 chuyên đề, mỗi loại vài bài (giữ cấu trúc DATA_MODEL).
- kịch bản/checklist demo cố định (seed + LLM stub hoặc nhiệt độ thấp), chạy lại được.
- chạy FULL test + build cả backend lẫn frontend; rà toàn bộ DoD mục 12 đặc tả v3, liệt kê
  mục nào đạt/chưa đạt.

TỰ build-test-fix đến xanh. Báo cáo tổng + trạng thái từng DoD + commit. Dừng.
```

---

## Prompt rà soát giữa các phase (dùng khi nghi ngờ)

```
Trước khi sang phase mới, rà: (1) core/matching và core/orchestrator có import llm không;
(2) có chỗ nào LLM tự quyết đúng/sai không; (3) response nào có thể chứa đáp án mà chưa qua
answer_guard không; (4) endpoint nào thiếu kiểm vai trò không. Liệt kê vi phạm + đề xuất sửa.
Chưa sửa, chờ tôi đồng ý.
```
