# PROGRESS.md — Trạng thái & bàn giao (cập nhật để kế thừa giữa các phiên/máy)

> File này là "trí nhớ đi theo repo" (lên GitHub). Bộ nhớ tự động của Claude Code nằm trên máy
> local, KHÔNG lên GitHub — nên mọi quyết định/trạng thái cần nhớ hãy ghi vào đây hoặc vào `docs/`.
> **Đọc cùng `CLAUDE.md` đầu mỗi phiên. Mỗi lần làm xong việc đáng kể, CẬP NHẬT file này.**

## 1. Trạng thái tổng quan (cập nhật 2026-07-18, phiên bản **v126**)

- **✨ (v126) Làm DỨT ĐIỂM docs lỗi thời (Hướng B — thu hẹp về phần ổn định + trỏ nguồn tự
  đúng), thay cho cảnh báo tạm ở v125.** Thuần tài liệu, KHÔNG đụng code.
  - **Vấn đề gốc**: `ARCHITECTURE.md` (cây thư mục + bảng endpoint) và `DATA_MODEL.md` là spec
    Phase 0, không cập nhật qua ~40 phiên → lệch nặng (8/20 models, ~20/154 endpoint, bảng
    endpoint dẫn SAI ~90%: kiểm 6 path thì 5 đã biến mất). Nguyên nhân: liệt kê tay thứ mà code
    đã tự mô tả → chắc chắn lỗi thời lại nếu chỉ "viết lại cho đúng hôm nay".
  - **ARCHITECTURE.md**: mục 4 (cây thư mục liệt kê từng file) → thay bằng **bảng thư mục →
    vai trò + quy ước đặt tên** (ls thấy file thật; doc chỉ giải thích ý nghĩa lớp). Mục 5
    (bảng 20 endpoint tay) → thay bằng **trỏ `/docs` + `/openapi.json` (FastAPI tự sinh, luôn
    khớp code)** + giữ lại NGUYÊN TẮC BẤT BIẾN (lọc đáp án, kiểm vai trò).
  - **DATA_MODEL.md**: giữ 8 bảng lõi (chỉ cột cốt lõi) + thêm cảnh báo "nguồn sự thật là
    `models/*.py` + Alembic baseline" + mục 13 mới **liệt kê 12 nhóm bảng mở rộng** (tên +
    mục đích, không chép cột) + cập nhật ghi chú seed (4 tài khoản, hành vi v120 trên Postgres).
  - **CLAUDE.md**: thêm quy ước — đổi endpoint/model KHÔNG cần sửa 2 doc này trừ khi chạm phần
    cốt lõi/bất biến; đừng chép lại chi tiết file/cột/endpoint (đó là thứ gây lỗi thời). Đây là
    cơ chế chống tái lỗi thời — gánh nặng đồng bộ gần như biến mất.
  - **Nhân tiện sửa lỗi cascade tái diễn**: quy trình cascade nhãn `## 1x.` trong file này lại
    tạo trùng nhãn (v122 và v121 cùng `1d`) — đã sửa; cần cẩn thận nhãn CŨ NHẤT mỗi lần dời.

## 1a. Trạng thái trước đó (v125)

- **✨ (v125) #5–#8 (P2, đợt rà soát 2026-07-18): nén PROGRESS.md, cập nhật docs, gắn Sentry,
  đưa E2E vào CI.** Toàn bộ danh sách rà soát 2 đợt (14 mục + 8 mục) giờ đã đóng, trừ #12/#13
  hoãn tới khi scale.
  - **#5**: `docs/PROGRESS.md` 1757→228 dòng — lịch sử v113–v120 chuyển sang
    `docs/PROGRESS_ARCHIVE.md` mới; SỬA LUÔN lỗi trùng nhãn `## 1j.` (2 mục khác nhau cùng
    nhãn, sót lại từ lần cascade tự động trước) thành `1j`/`1k` riêng biệt trong file archive.
  - **#6**: `docs/TESTING.md` thêm mục Migration (Alembic) + E2E (Playwright); `docs/
    ARCHITECTURE.md` thêm mục 6 (Alembic) + cảnh báo rõ mục 4/5 (cây thư mục, bảng endpoint)
    là thiết kế GỐC Phase 0, đã lỗi thời nhiều chỗ ngoài phạm vi đợt sửa này (không viết lại
    toàn bộ — rủi ro sai sót cao, ngoài yêu cầu).
  - **#7 Sentry — GẮN CODE xong, cần user tự đăng ký để BẬT THẬT**: `frontend/src/sentry.js`
    (`initSentry()` ở `main.jsx`, `ErrorBoundary` tự báo lỗi qua `baoLoi()`) — an toàn mặc
    định, KHÔNG phát request nào nếu chưa cấu hình `VITE_SENTRY_DSN`. Hướng dẫn bật đầy đủ ở
    mục 7 bên dưới.
  - **#8**: job `e2e` mới trong CI (`needs: [backend, frontend]`, cài Playwright+Chromium,
    upload báo cáo lỗi nếu fail). **Phát hiện + sửa luôn 1 lỗi thật**: `playwright.config.js`
    dùng lệnh khởi động backend kiểu Windows-only (`del ...`, `.venv\Scripts\python.exe`) —
    sẽ CHẮC CHẮN lỗi trên CI Ubuntu. Viết lại thành `frontend/e2e/start-backend.mjs` (Node,
    cross-platform: tự dò `.venv` local hay `python3` hệ thống trên CI) — đã tự kiểm lại E2E
    local sau khi đổi, vẫn 3/3 xanh.
  - Backend không đổi code (trừ không có gì mới ngoài #5-8 thuần frontend/docs/CI).
    `eslint`/`vite build` sạch, `vitest` 23/23, `playwright` 3/3 (Windows, qua PowerShell —
    Git Bash trên máy này có lỗi môi trường `spawn UNKNOWN` khi Playwright tự fork worker,
    không liên quan code, chỉ cần dùng PowerShell).

## 1b. Trạng thái trước đó (v124)

- **✨ (v124) Nâng chuẩn mật khẩu tối thiểu 4 → 6 ký tự (đợt rà soát mới 2026-07-18).** Tài
  khoản GV/quản lý dùng "1234" quá yếu dù đã có throttle chống dò (`auth/throttle.py`).
  - **Backend**: 9 chỗ `min_length=4` → `6` trong 3 schema (`admin.py` ×4, `gv.py` ×4,
    `hs.py` ×1) — phủ TẤT CẢ đường tạo/sửa/import tài khoản + đổi hồ sơ admin/gv/hs. Comment
    giải thích policy đặt tại `TaoTaiKhoanRequest`. `LoginRequest` KHÔNG áp min → mật khẩu
    seed/cũ ngắn hơn (vd seed gv123 5 ký tự) vẫn đăng nhập được; ràng buộc chỉ lúc TẠO/ĐỔI,
    mật khẩu cũ đã hash không bị ảnh hưởng.
  - **Frontend**: 2 dialog import (check `<4` + text gợi ý) sửa sang 6 để không lệch backend;
    thêm `minLength={6}` + gợi ý "tối thiểu 6 ký tự" cho các ô mật khẩu tạo/sửa/hồ sơ (2 form
    tạo + 3 self-service TaiKhoanCaNhan + 2 modal sửa) — báo ngay thay vì chờ 422.
  - **Tests**: sửa các test tạo/import tài khoản dùng "1234" → "123456"; thêm
    `test_mat_khau_toi_thieu_6_ky_tu` (5 ký tự → 422, 6 ký tự → 200, seed cũ vẫn login được).
  - `pytest` 532/532 (+1), `ruff`/`eslint`/`vite build` sạch, `vitest` 23/23, `playwright` 3/3.
  - **Trạng thái rà soát**: #4 thực nghiệm người dùng thật (C5) — **user báo đã làm** (không
    nhắc lại). Còn mở (P2, làm khi rảnh): nén PROGRESS.md (>170KB), cập nhật docs TESTING/
    ARCHITECTURE cho Alembic+E2E, Sentry, đưa `npm run e2e` vào CI.

## 1c. Trạng thái trước đó (v123)

- **✨ (v123) #11 (mục P0/P1 cuối cùng còn code được): E2E Playwright 3 "luồng vàng" trên trình
  duyệt thật + #14 viết lại mục 7 (lỗi thời từ v32).** Với v123, TOÀN BỘ 14 mục đợt rà soát
  2026-07-17 đã chốt xong (xem mục 7: đã xong / hoãn #12 #13 / bỏ hẳn Báo cáo PH Pha 2).
  - **E2E (`frontend/e2e/luong-vang.spec.js`, chạy `npm run e2e`)**: ① HS đăng nhập → Chọn
    bài → lọc TLN → giải trọn bài 2 bước (nhập công thức vào MathLive math-field qua
    `el.value` + dispatch event `input` — đúng event FormulaEditor lắng nghe, gõ phím thật
    vào math-field không ổn định headless) → banner "Trả lời đúng — Hoàn thành bài!";
    ② GV import 1 câu (dàn cảnh qua API) → bảng Câu hỏi → bấm Duyệt → hàng (nhận diện qua
    cột ID vì bảng không hiện đề bài) chuyển "Đã duyệt"; ③ HS nhờ thầy/cô (API) → GV Hỗ trợ
    học sinh → Xem chi tiết → Trả lời trong popup → "Đã trả lời".
  - **Hạ tầng cách ly hoàn toàn khỏi dev**: cặp server riêng (backend uvicorn :18000 + vite
    dev :15173) do Playwright tự bật/tắt; DB `backend/e2e.db` XÓA TẠO LẠI mỗi lần chạy (lệnh
    `del ... &` ngay trong webServer command); vite proxy nhận đích qua env `MT_API_PROXY`
    (mặc định vẫn 8000 — dev không đổi gì); LLM tự rơi về stub (không key) nên tất định.
    `vitest` phải exclude `e2e/**` (pattern mặc định `*.spec.js` của vitest sẽ bắt nhầm spec
    Playwright — chặn từ đầu).
  - **#14**: mục 7 PROGRESS viết lại thành bảng trạng thái 14 mục (xong/hoãn/bỏ); quyết định
    user: **BỎ HẲN Báo cáo phụ huynh Pha 2** (không nhắc lại nữa), #12/#13 hoãn — chỉ nhắc
    khi bàn tới scale/nhiều trường.
  - Backend KHÔNG đổi dòng code nào đợt này. `eslint`/`vite build` sạch (sửa 1 lỗi no-undef
    `process` trong vite.config bằng `import process from 'node:process'`), `vitest` 23/23,
    `playwright` 3/3 (chạy 2 lần liên tiếp xác nhận lặp lại được).

## 1d. Trạng thái trước đó (v122)

- **✨ (v122) #8 (P0): chặn batch import khổng lồ + giới hạn tổng dung lượng request toàn
  app.** Rà lại 3 endpoint import hàng loạt (`ImportTaiKhoanRequest.tai_khoans`,
  `ImportHSBatchRequest.hoc_sinhs`, `ImportBatchRequest.items` câu hỏi) — chỉ có
  `min_length=1`, KHÔNG có giới hạn trên → batch khổng lồ (hàng triệu dòng) tốn RAM/CPU không
  kiểm soát.
  - Thêm `max_length` (2000/2000/1000 tương ứng, đủ rộng cho quy mô 1 trường/khối).
  - Thêm middleware toàn app `main.py::gioi_han_dung_luong_request` — chặn SỚM qua header
    `Content-Length` (413) TRƯỚC khi Starlette buffer toàn bộ body vào RAM, phòng vệ chung cho
    MỌI endpoint (kể cả endpoint tương lai lỡ quên validate field riêng) — 15MB đủ rộng cho ảnh
    base64 (giới hạn nghiệp vụ ≤10MB) + mọi batch import.
  - 5 test mới (3 batch quá giới hạn bị 422 + 2 middleware). `pytest` 531/531, `ruff` sạch.

## 1e. Trạng thái trước đó (v121)

- **✨ (v121) #7 (P0): chuyển hẳn sang Alembic — thay cơ chế tự viết
  `_migrate_them_cot()` (ADD COLUMN thủ công, không rollback/dry-run). User CHỦ ĐỘNG hỏi lại
  sau khi từng hoãn quyết định này "tới sau mùa thi" (phiên 2026-07-13) — đã xác nhận rõ trước
  khi code vì đây là thay đổi rủi ro cao, khó đảo ngược, đụng thẳng cơ chế deploy trên DB
  production có dữ liệu GV/HS thật.**
  - **Migration baseline** (`alembic/versions/2929ecbc70fc_..._baseline...py`) sinh bằng
    `alembic revision --autogenerate` khớp đúng schema hiện tại (DB rỗng) — phải SỬA TAY 2 lỗi
    autogenerate: (1) thiếu `import app.db.types` cho kiểu cột `UTCDateTime` tùy biến; (2) FK
    VÒNG TRÒN `lop.gv_id↔users.id` (autogenerate tạo `lop` kèm FK tới `users` TRƯỚC KHI bảng
    `users` tồn tại → lỗi "relation users does not exist" thật trên Postgres nếu không sửa) —
    tách bằng `op.batch_alter_table` thêm FK SAU khi cả 2 bảng đã tạo (batch mode để cùng chạy
    được cả SQLite lẫn Postgres).
  - **`app/db/migrate.py::chay_migration()`** (mới, thay `create_all()+_migrate_them_cot()`
    trong `init_db()`): tự soi bảng qua `settings.database_url` — CSDL đã có bảng `users`
    nhưng CHƯA có `alembic_version` (= production cũ, hoặc dev.db có sẵn dữ liệu) → **STAMP**
    (đánh dấu đã ở đúng baseline, KHÔNG chạy lại DDL tạo bảng); ngược lại → `upgrade head` bình
    thường. Đã tự kiểm bằng bản sao CHÍNH `dev.db` thật (12 users/11 problems/10 sessions,
    tháo `alembic_version` để mô phỏng đúng production trước khi chuyển) — stamp thành công,
    dữ liệu nguyên vẹn 100%.
  - **Tự gây lỗi rồi tự phát hiện + sửa qua build-test-fix**: `alembic/env.py`'s
    `fileConfig()` mặc định `disable_existing_loggers=True` → XÓA SẠCH handler logging của
    pytest `caplog` mỗi lần `chay_migration()` chạy trong test, làm 1 test KHÁC hoàn toàn
    không liên quan (`test_question_gen.py`) fail khi chạy CHUNG suite (nhưng pass khi chạy
    riêng) — phát hiện qua đối chiếu "pass riêng lẻ, fail khi chạy full suite", sửa bằng
    `disable_existing_loggers=False`.
  - Xóa `_migrate_them_cot()` (183 dòng ALTER TABLE thủ công, đã hết tác dụng — mọi cột đã
    seed vào baseline). `docs/PROGRESS.md`/quy tắc schema DB trong memory cập nhật theo quy
    trình Alembic mới (xem mục 5 bên dưới).
  - `pytest` 526/526 (+3 test mới `test_migrate.py`), `ruff` sạch.

> Lịch sử chi tiết các phiên bản trước v121 đã chuyển sang
> [`docs/PROGRESS_ARCHIVE.md`](PROGRESS_ARCHIVE.md) (2026-07-18) để file này gọn lại.

## 2. ⚙️ CHẾ ĐỘ VẬN HÀNH HIỆN TẠI = "PHÁT TRIỂN" (tiết kiệm quota Gemini)

Đặt trong `dev.db` (Admin config), **không nằm trong code/GitHub**:
- `llm_provider = stub` → mọi lời gọi LLM dùng mẫu cố định = **0 quota**; logic/orchestrator/
  matching/guard/leo-thang/cờ/điểm chạy y như thật, chỉ lời thoại là templated.
- `tu_dong_phan_tich = false` → tắt quét nền (tránh đốt quota mỗi lần backend `--reload`).
- Key Gemini **vẫn được lưu** trong dev.db. Thinking để TẮT theo provider (mặc định).

**⚠️ KHI USER NÓI "hoàn thiện / chạy thật / dự thi" → NHẮC bật production (chỉ chỉnh trong Admin,
KHÔNG sửa code):** (1) bật billing Google hoặc key hạn mức cao; (2) Admin→AI: `llm_provider`
stub→gemini, chọn model; (3) bật lại `tu_dong_phan_tich` + chu kỳ ~360'; (4) tùy chọn bật thinking;
(5) làm thử 1 bài để chắc lời thoại tự nhiên + AI sinh câu hỏi OK.
Lý do tiết kiệm: trò chuyện gia sư gọi Gemini MỖI lượt (1 bài ≈ 6–20 lượt); free tier ~20 lượt/
ngày/model.

## 3. Tính năng đã hiện thực (ngoài PLAN gốc)

- **LLM thật (đã làm — KHÁC PROGRESS cũ):** abstraction `LLMClient` ở `backend/app/llm/client.py`
  với `StubLLMClient` / `OpenAILLMClient` / `AnthropicLLMClient` / `GeminiLLMClient`;
  `get_llm_client(cau_hinh)` đọc cấu hình Admin (DB). Có retry (`SO_LAN_THU=3`), Gemini fallback
  model (2.5-flash → 2.0-flash → 2.5-flash-lite, đổi model cả khi 429), parse JSON chịu lỗi LaTeX.
  Bật/tắt **thinking theo từng provider** (mặc định tắt; phân tích luôn tắt thinking chống cắt cụt).
- **AI sinh câu hỏi thật** theo cấu trúc từng loại (Admin chọn provider/key/model). Hàng đợi chờ
  duyệt hiện đủ nội dung + nút Sửa/Duyệt/Loại; danh sách câu hỏi mới-trước, cột Người tạo (GV/AI)
  + Ngày giờ tạo.
- **Phân tích năng lực học sinh** (`backend/app/services/phan_tich_service.py`): hồ sơ TẤT ĐỊNH
  theo chuyên đề/dạng/loại (điểm thành thạo, tỉ lệ hoàn thành, phụ thuộc gợi ý, thời gian) →
  đề xuất theo LUẬT → diễn giải bằng LLM (2 giọng HS/GV) cache ở bảng `phan_tich_hs`. Có bản dự
  phòng theo luật (`nguon = ai|luat`, tự nâng cấp khi AI sẵn sàng), xu hướng tiến bộ (`_xu_huong`),
  tổng hợp lớp cho GV, lối tắt "Luyện ngay". Hiển thị qua component `PhanTichNangLuc.jsx` (tiêu đề
  "Đánh giá tổng quan"; nút cập nhật thông minh theo trạng thái).
- **Tự động phân tích theo lịch nền** (`backend/app/services/lich_phan_tich.py`): quét HS đến hạn
  (≥5 bài mới / quá 7 ngày), Admin bật/tắt + chu kỳ + "Quét ngay". Chạy quét ngay khi backend khởi
  động (đây là lý do đốt quota khi reload nhiều → đang tắt ở chế độ dev).
- **Tự gắn cờ theo dõi theo ngưỡng (Admin):** `khong_hieu_nhieu` (HS xin gợi ý/bí ≥ ngưỡng) và
  `chot_chan_nhieu` (phản hồi bị chốt chặn rò rỉ ≥ ngưỡng); gắn 1 lần/phiên.
- **Thời gian làm bài theo hoạt động thực**: cộng dồn, chặn khoảng nghỉ dài (ngưỡng cấu hình) để
  không phồng khi "quay lại làm sau".
- **TNDS phòng học:** hiện "Việc cần làm cho ý x)" (mô tả bước theo đúng ý) trên ô nhập; nhãn
  "Nhập câu trả lời vào ô bên dưới".
- **Trang HS:** Trang chủ (tổng quan + bài dở phân trang + thống kê Dễ/TB/Khó); Chọn bài (lọc theo
  trạng thái Hoàn thành/Đang dở/Chưa làm); Tiến độ ("Theo thời gian" + "Theo mức độ" 2 cột bằng
  chiều cao, "Theo dạng bài" chia 2 cột).
- **Trang GV:** Tổng quan (nhóm lớp/HS, câu hỏi, cờ, dạng & loại tốn thời gian); Tiến bộ học sinh
  (phân trang 5/trang, lọc theo lớp, cột Lớp, tổng hợp lớp; Nhật ký hoàn thành phân trang đặt trên).
- **Import từ Excel (v16–v17):**
  - GV — "Thêm lớp": import hàng loạt tên lớp từ Excel; preview modal hiển thị lớp trùng (trong
    phạm vi GV) tô đỏ, Xác nhận chỉ tạo lớp mới. Nút "Thêm lớp" thủ công cũng kiểm tra trùng
    tên inline trước khi tạo.
  - GV / Admin — "Thêm danh sách học sinh" trong từng lớp: import HS từ Excel; preview trong
    dialog (Họ tên, Tên đăng nhập, Mật khẩu, Trạng thái); tô đỏ tên đăng nhập trùng toàn hệ thống
    hoặc dữ liệu thiếu/lỗi; Xác nhận chỉ tạo HS hợp lệ. `ImportHocSinhDialog` dùng chung props
    `onKiemTra`/`onImport` cho cả GV lẫn Admin.
  - Admin — "Thêm lớp": GV phụ trách bắt buộc; kiểm tra trùng (tên lớp + GV) trước khi tạo,
    hiện cảnh báo inline.
  - Admin — "Tạo tài khoản": nút "Import từ Excel" trong header; modal `ImportTaiKhoanDialog`
    với tải file mẫu (4 cột: Họ tên, Tên đăng nhập, Mật khẩu, Vai trò); parse → validate
    (thiếu trường, mật khẩu < 4 ký tự, vai trò không hợp lệ → đỏ + lý do); kiểm tra trùng
    tên đăng nhập toàn hệ thống; preview 5 cột; Xác nhận chỉ tạo dòng hợp lệ.
- **Phân quyền câu hỏi pham_vi (v22):** enum `PhamVi` (`rieng_tu` | `chung`) trên bảng `problems`.
  Luồng: GV tạo thủ công → `da_duyet + rieng_tu` ngay (không cần duyệt); AI sinh → `cho_duyet +
  rieng_tu`; GV duyệt AI → `da_duyet + chung` (tự chia sẻ 1 bước). GV có thể "Chia sẻ" câu riêng tư
  lên kho chung qua endpoint `/problems/{id}/chia-se`. GV thấy câu của mình + kho chung; HS chỉ thấy
  `da_duyet + chung + !bi_an`. Bảo vệ sửa/xóa theo người tạo; giao nhiệm vụ câu riêng tư chỉ người
  tạo được giao. Migration tự động khi khởi động (`init_db._migrate_them_cot`). 213/213 test xanh.

## 4. Quyết định sản phẩm cần nhớ

- **Gợi ý leo thang KHÔNG lỗi** (đã kiểm chứng end-to-end): cap tăng theo `len(danh_sach_goi_y)`
  thực tế; thêm gợi ý giữa phiên vẫn leo tiếp. Cảm giác "đứng yên" trước đây là do diễn đạt LLM khi
  hết quota / prompt thiếu quy tắc `goi_y` — đã bổ sung quy tắc trong `SYSTEM_DIEN_DAT`.
- **Chat 2 chiều:** backend `/api/sessions/{id}/message` vẫn nhận `noi_dung` tự do; UI HS có nút
  "GỢI Ý CHO EM" + ô gửi đáp án (TNDS có nút Đúng/Sai).
- **Bí mật:** `.env`, `dev.db` gitignore — không commit. Khóa API lưu server-side, không hiển thị lại.

## 5. Chạy dự án

Backend: `cd backend` → (lần đầu) `python -m venv .venv && .venv\Scripts\activate && pip install -e .`
→ `uvicorn app.main:app --reload --port 8000` (DB tự seed nếu chưa có user).
Frontend: `cd frontend` → (lần đầu) `npm install` → `npm run dev` (http://localhost:5173, proxy /api).
Tài khoản seed (CHỈ local/dev, SQLite): `admin/admin123`, `gv1/gv123`, `hs1/hs123`. Trên
production (Postgres) `init_db()` KHÔNG dùng các mật khẩu công khai này — nếu CSDL rỗng chỉ tạo
1 admin với mật khẩu ngẫu nhiên in ra log khởi động một lần (xem `db/init_db.py`).
Build-test trước khi commit: backend `ruff check app/` + `pytest`; frontend `npm run build`.

> DB: từ v121 dùng **Alembic** (`backend/alembic/`), KHÔNG còn `_migrate_them_cot()` thủ công.
> App tự chạy `alembic upgrade head` lúc khởi động (`app/db/migrate.py::chay_migration()`) —
> KHÔNG cần bước deploy riêng. **Mỗi lần đổi model (thêm/sửa cột, bảng)**:
> 1. Sửa model trong `app/models/`.
> 2. `cd backend && alembic revision --autogenerate -m "mô tả ngắn"` (đọc kỹ file sinh ra trong
>    `alembic/versions/` — đặc biệt FK vòng tròn, kiểu cột tùy biến như `UTCDateTime` cần
>    `import app.db.types` tay, và bất kỳ chỗ nào autogenerate không suy ra đúng ý).
> 3. Test cả `alembic upgrade head` LẪN `alembic downgrade -1` trên bản sao dữ liệu thật (không
>    phải DB rỗng) trước khi push.
> 4. Commit file migration mới cùng với thay đổi model — KHÔNG sửa tay migration đã push/deploy.

## 6. Đồng hành GV↔HS (A1–B1, C1) — triển khai tháng 2026-06

| Phase | Mô tả | Trạng thái |
|---|---|---|
| A1 | Thông báo (chuông) + GV nhận xét HS (AI gợi ý nhận xét sẵn) | ✅ Done |
| A2 | HS nhờ thầy/cô trong bài, GV trả lời inline | ✅ Done |
| A3 | GV giao nhiệm vụ/bài tập theo lớp/từng HS/theo điểm yếu | ✅ Done |
| A4 | Khép vòng cờ: GV xử lý cờ kèm nhắn HS (trung tính/minh bạch) | ✅ Done |
| B1 | Mục tiêu học tập: HS tự đặt / GV đặt / hệ thống gợi ý theo điểm yếu | ✅ Done |
| C1 | Chuỗi ngày học (streak) + 8 cột mốc nhẹ (bài/chuỗi ngày) | ✅ Done |

## 7. Việc tiếp theo & quyết định đã chốt (viết lại 2026-07-17, thay bản cũ lỗi thời từ v32)

Trạng thái đợt rà soát toàn dự án 14 mục P0/P1/P2 (2026-07-17):

- **✅ Đã xong**: #1 checklist production (đã bật trên production) · #3a đổi mật khẩu seed ·
  #3b rate-limit login (có sẵn từ trước, `auth/throttle.py`) · #4 backup (Render + pg_dump tay)
  · #5 uptime monitor · #6 không seed mật khẩu công khai trên Postgres (v120) · #7 Alembic
  (v121) · #8 chặn batch/request lớn (v122) · #9 chống trùng phiên (có sẵn từ trước) ·
  #10 ErrorBoundary (v120) · #11 E2E Playwright 3 luồng vàng (v123) · #14 mục này.
- **⏸ Hoãn — CHỈ nhắc lại khi bàn tới scale/nhiều trường** (user dặn rõ): #12 khóa scheduler
  phân tích nền khi chạy nhiều worker/instance · #13 chuyển ảnh upload sang cloud storage.
- **❌ BỎ HẲN, không nhắc lại** (quyết định user 2026-07-17): **Báo cáo phụ huynh Pha 2**
  (đưa kết quả đề thi thử vào báo cáo — từng ghi "để Pha 2" từ v106). Báo cáo phụ huynh giữ
  nguyên như hiện tại.
- **#2 model AI**: giữ `gemini-2.5-flash` theo quyết định user (model có lịch ngừng hỗ trợ
  16/10/2026 — fallback `gemini-flash-latest` đã có sẵn trong code, không cần nhắc lại).

**Đợt rà soát mới 2026-07-18** (đánh số tiếp #3, #4... không trùng bộ 14 mục trên):
- **✅ #3** nâng min mật khẩu 4→6 (v124) · **✅ #4** thực nghiệm người dùng thật C5 (user báo
  đã làm, không nhắc lại) · **✅ #5** nén PROGRESS.md → tách `PROGRESS_ARCHIVE.md` · **✅ #6**
  cập nhật `docs/TESTING.md`/`docs/ARCHITECTURE.md` cho Alembic + E2E.
- **✅ #7 Sentry — ĐÃ GẮN CODE, cần user tự đăng ký để BẬT THẬT**: `frontend/src/sentry.js`
  (`initSentry()` gọi ở `main.jsx`, `ErrorBoundary` tự báo lỗi qua `baoLoi()`) — an toàn mặc
  định, KHÔNG phát request nào ra ngoài nếu chưa cấu hình. Để bật: (1) đăng ký free tại
  sentry.io → New Project (React) → copy DSN; (2) local: tạo `frontend/.env` từ
  `.env.example`, dán DSN; (3) production: Render → service `mathtutor-1` → Environment →
  đặt `VITE_SENTRY_DSN` (đã khai trong `render.yaml`, `sync: false` nên phải tự điền tay).
- **✅ #8** `npm run e2e` vào CI (`.github/workflows/ci.yml`, job `e2e`).

Việc thường trực mỗi đợt:
- [ ] Cập nhật mục 1 (phiên bản) + mục này khi có thay đổi đáng kể.
- [ ] Chạy `pytest` + `npm run lint`/`build`/`test` trước mỗi commit; `npm run e2e` (frontend)
      trước các đợt sửa lớn chạm luồng HS/GV.
