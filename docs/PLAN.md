# PLAN.md — Kế hoạch triển khai 12 phase (v3, 6 tuần)

Lát cắt dọc, hai lõi tự viết trước, LLM + kiểm soát giữa, vai trò + giao diện + giám sát sau.
Mỗi phase: làm → TỰ build-test-fix đến xanh (xem CLAUDE.md mục 2) → báo cáo lỗi & cách xử lý →
kiểm DoD → commit → DỪNG. Prompt copy-paste ở `PHASE_PROMPTS.md`.

Lệnh chuẩn (Windows, D:\claude\mathtutor):
- Backend test: `cd backend && pytest -q`
- Backend lint/smoke: `ruff check . && python -c "import app.main"`
- Frontend build: `cd frontend && npm run build`

Ánh xạ tuần: T1=Phase 0–2 · T2=Phase 3–4 · T3=Phase 5–6 · T4=Phase 7–8 · T5=Phase 9–10 · T6=Phase 11.

---

## Phase 0 — Khởi tạo dự án + xác thực/phân quyền nền

**Mục tiêu:** khung backend+frontend chạy; đăng nhập JWT; phân quyền 3 vai trò.

- backend: FastAPI, config đọc env, SQLAlchemy (`DATABASE_URL` mặc định SQLite), pyproject
  (ruff/black/pytest), `.env.example` (gồm `JWT_SECRET`, `LLM_*`).
- auth: hash bcrypt, JWT, `require_role(admin|gv|hs)`; models `users`,`lop`; seed 3 tài khoản.
- API: `POST /api/auth/login`, `GET /api/health`, một route thử mỗi vai trò.
- frontend: Vite+React+Tailwind; trang Login; lưu token; điều hướng theo vai trò.
- Git init, .gitignore.

**DoD:** health OK; login 3 tài khoản seed trả JWT + vai trò đúng; route chặn sai vai trò (403);
`pytest` xanh; `npm run build` OK.

---

## Phase 1 — Lõi 2: So khớp CAS + parse_latex + bậc thang  ★

**Mục tiêu:** `core/matching` thuần Python.

- `cas.py`: `tuong_duong(hs, chuan, che_do, lam_tron=None)` dùng SymPy (lấy hiệu rút gọn=0).
  Hỗ trợ `che_do`=`tuong_duong`/`dung_dang`. Parse an toàn; lỗi cú pháp → `KHONG_PHAN_TICH_DUOC`.
- `latex.py`: `latex_sang_sympy(latex_str)` dùng `parse_latex`; bắt lỗi rõ ràng.
- `scoring.py`: `diem_bac_thang(k)`.
- `matcher.py`: `so_khop(loai_cau, dap_an_nhap, du_lieu_chuan, che_do_so_khop)`.

**DoD (test):** `x^2-1`=`-1+x^2`=`(x-1)(x+1)`; `1/2`=`0.5`=`2/4`; `dung_dang` phân biệt dạng;
lỗi cú pháp ra KHONG_PHAN_TICH_DUOC; bậc thang đủ 5 ca; `latex_sang_sympy` chuyển `\frac{x^2-1}{2}`
đúng; `core/matching` không import fastapi/llm/db.

---

## Phase 2 — Lõi 1: Điều phối + lát cắt dọc TLN (LLM stub) + editor cơ bản  ★

**Mục tiêu:** `core/orchestrator` + chạy trọn 1 bài TLN; nhập công thức qua editor → CAS.

- `state.py`,`rules.py`,`directive.py`: ChiThi gồm `y_dinh`,`buoc`,`y_dang_xet`,`cap_goi_y`,
  `y_goi_y` (Ý CHÍNH lấy từ `danh_sach_goi_y[cap_goi_y]`),`ngu_canh_hs`,`rang_buoc`. Quy tắc mục 4 đặc tả.
  **Số gợi ý mỗi bước linh hoạt (Phương án C): orchestrator đọc `len(step.danh_sach_goi_y)` của
  bước hiện tại, KHÔNG hard-code 3; nâng `cap_goi_y` tới tối đa = độ dài danh sách rồi dừng nâng.**
- `llm/client.py`: chỉ `StubLLMClient.dien_dat` tất định từ `y_goi_y`.
- `services/tutor_service`: ghép message→matching→orchestrator→stub.
- seed bài TLN; models problem/solution_step/session/turn; API sessions + message.
- frontend: `Formula.jsx` (KaTeX), `FormulaEditor.jsx` (MathLive cơ bản), `PhongHoc` tối giản.

**DoD:** hội thoại TLN chạy: hỏi định hướng → HS nhập bước qua editor → CAS chấm → đi hết bài;
test orchestrator (đúng/sai/xin gợi ý tới hết danh sách của bước); ChiThi luôn có `rang_buoc` cấm lộ đáp án;
`core/orchestrator` không import LLM.

---

## Phase 3 — Mở rộng TN4PA & TNDS + LLM thật + hội thoại tự nhiên (kịch bản mềm)

**Mục tiêu:** đủ 3 loại; LLM thật diễn đạt tự nhiên, bám câu trả lời HS.

- orchestrator: TN4PA (tìm kết quả rồi đối chiếu; chọn bừa→yêu cầu loại trừ); TNDS (vòng lặp
  từng ý a→d; `y_hien_tai`; tổng hợp bậc thang).
- `llm/client.py`: thêm provider thật + `prompts.py` theo PROMPTS_LLM.md; LLM diễn đạt từ
  `y_goi_y` + `ngu_canh_hs`, trả lời câu hỏi phụ trong phạm vi bài; nhiệt độ thấp.
- xử lý lỗi API → gợi ý mặc định từ `y_goi_y`.
- seed thêm TN4PA, TNDS; API `answer` trả kết quả theo loại.

**DoD:** dẫn dắt cả 3 loại; với stub mọi test chạy không cần mạng; LLM thật không thêm nội dung
toán ngoài `y_goi_y` (kiểm thủ công); test orchestrator TNDS/TN4PA.

---

## Phase 4 — Sáu lớp kiểm soát + gắn cờ + API giám sát  ★

**Mục tiêu:** `core/guard` đầy đủ + lưới an toàn.

- `answer_guard.py`: rà phản hồi, phát hiện chứa đáp án (so chuỗi chuẩn hóa + so giá trị số qua
  CAS); lộ→yêu cầu viết lại 1 lần→vẫn lộ thì thay câu an toàn từ `y_goi_y`; ghi `co_bi_chot_chan`.
- `scope.py` khóa phạm vi; `safety.py` lọc lứa tuổi + dấu hiệu khó khăn tâm lý.
- ghép guard vào tutor_service đúng thứ tự ARCHITECTURE mục 3.
- flag + `monitor_service`; API `/api/monitor/...`.

**DoD (test):** bộ ca BẪY cho 3 loại (stub trả câu chứa đáp án) → chốt chặn kích hoạt; khóa phạm
vi kéo lạc đề về bài; lọc an toàn đúng; phiên nhiều "không hiểu" sinh cờ; API giám sát trả hàng đợi.

---

## Phase 5 — AI sinh câu hỏi theo mẫu + GV duyệt

**Mục tiêu:** giảm tải soạn cho GV.

- `llm/question_gen.py` + `question_gen_service`: nhận yêu cầu (chuyên đề/loại/độ khó/số lượng)
  hoặc tài liệu nguồn; LLM trả JSON đúng mẫu (PROMPTS_LLM.md mục sinh câu hỏi); validate JSON +
  SymPy parse được `bieu_thuc_ket_qua`.
- API `/api/questions-ai/generate`, `/api/questions-ai/{id}/duyet`.
- câu sinh ở `cho_duyet`; chỉ `da_duyet` mới tới HS.

**DoD:** sinh nháp cho cả 3 loại đúng mẫu; cảnh báo khi CAS không parse được; GV duyệt/sửa/loại;
test: câu chưa duyệt không xuất hiện trong `GET /api/problems` của HS.

---

## Phase 6 — Tiến độ + làm tiếp bài dang dở

**Mục tiêu:** Progress + khôi phục phiên.

- `progress_service`: cập nhật khi xong bài; `GET /api/progress/me` (HS), `/api/progress/students` (GV).
- session khôi phục: `GET /api/sessions/dang-do`; mở lại đúng `buoc_hien_tai`/`y_hien_tai`/bộ đếm.

**DoD:** HS bỏ giữa chừng rồi vào lại → tiếp đúng chỗ; bảng tiến độ HS hiển thị; GV xem tiến bộ
lớp mình; test khôi phục phiên + tính progress.

---

## Phase 7 — Thiết kế UI/UX (Claude Design) + hệ thống thiết kế

**Mục tiêu:** định hình giao diện đẹp, hiện đại, nhất quán TRƯỚC khi dựng nhiều trang.

- Theo `docs/UIUX_DESIGN.md`: chốt design tokens (màu, font, spacing, bo góc, bóng), thành phần
  cơ bản (button, card, input, badge trạng thái, bảng, biểu đồ), 3 bố cục theo vai trò.
- Có thể dùng Claude Design để phác layout các màn hình chính (Login, PhongHoc, Dashboard GV,
  Dashboard Admin) rồi chuyển thành component React + Tailwind.
- Tạo `frontend/src/styles` chứa tokens; `RoleLayout.jsx`; bộ component dùng lại.

**DoD:** có hệ thống thiết kế tài liệu hóa ngắn; các component cơ bản render mẫu; `npm run build` OK.

---

## Phase 8 — Frontend Học sinh (đầy đủ)

- pages/hs: `TrangChu` (tiến độ + bài dở), `ChonBai` (lọc chủ đề/loại/mức độ), `PhongHoc`
  (hội thoại + 3 vùng nhập + editor + nút "em chưa hiểu"), `KetThuc` (TNDS bậc thang), `TienDo`.
- `AnswerInputTN4PA/TNDS/TLN`, `ProgressChart`.

**DoD:** HS đăng nhập → chọn bài → luyện đủ 3 loại → editor công thức + bản render xác nhận →
làm tiếp bài dở → xem tiến độ; `npm run build` OK; thử luồng e2e thủ công.

---

## Phase 9 — Frontend Giáo viên (đầy đủ)

- pages/gv: `QuanLyCauHoi`, `SoanBai` (sửa đề/bước/ý gợi ý), `AISinhCauHoi` (sinh+duyệt),
  `QuanLyCo`, `QuanLyHocSinh`, `TheoDoiTienBo`.

**DoD:** GV quản lý câu hỏi, sinh+duyệt bằng AI, xử lý cờ, theo dõi tiến bộ HS lớp mình;
`npm run build` OK.

---

## Phase 10 — Frontend Quản trị + dashboard tổng

- pages/admin: `Dashboard` (thống kê tổng), `QuanLyTaiKhoan`, `CauHinh` (ngưỡng cờ, nhiệt độ
  LLM, bảng bậc thang), `NhatKy`.

**DoD:** Admin xem dashboard, quản lý tài khoản, chỉnh cấu hình; phân quyền chặn HS/GV vào admin.

---

## Phase 11 — Hoàn thiện + kịch bản demo + rà DoD toàn sản phẩm

- seed đủ 2–3 chuyên đề, mỗi loại vài bài.
- kịch bản demo cố định (seed + LLM stub/nhiệt độ thấp), lặp lại được.
- rà toàn bộ DoD mục 12 đặc tả v3; chạy full test + build; báo trạng thái từng mục.

**DoD = mục 12 đặc tả v3** (3 vai trò; 3 loại câu; hội thoại tự nhiên không lộ đáp án; editor
LaTeX→CAS; CAS hiểu tương đương; TNDS bậc thang; AI sinh+duyệt; 6 lớp kiểm soát; làm tiếp +
tiến độ; dashboard Admin; demo lặp lại được).

---

## Bản đồ phase → mục đặc tả v3
| Phase | Mục |
|------|-----|
| 0 | 2 (phân quyền), 10 (nền tảng) |
| 1 | 6.1 (CAS), 4 (bậc thang) |
| 2 | 1.1 (kịch bản mềm), 3 (TLN), 6.2 (editor) |
| 3 | 3 (3 loại), 3.4 (tự nhiên), 7 (LLM tầng 3) |
| 4 | 8 (6 lớp) |
| 5 | 5 (AI sinh câu hỏi) |
| 6 | 2.3 (làm tiếp), 9.1 (tiến độ) |
| 7 | 9 (giao diện), UIUX_DESIGN.md |
| 8–10 | 9.1/9.2/9.3 (giao diện theo vai trò) |
| 11 | 12 (DoD) |
