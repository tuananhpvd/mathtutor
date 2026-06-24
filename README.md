# MathTutor — Bộ kế hoạch triển khai v3 (cho Claude Code)

Gia sư Toán lớp 12 theo phương pháp Socratic. Hội thoại tự nhiên (mô hình "kịch bản mềm"),
3 loại câu hỏi (TN4PA, TNDS, TLN), editor công thức bắt buộc, phân quyền 3 vai trò
(Quản trị / Giáo viên / Học sinh), AI sinh câu hỏi cho GV duyệt. Số gợi ý mỗi bước LINH HOẠT
(mặc định theo độ khó: Dễ 2, TB 3, Khó 4; GV chỉnh được). Khung 6 tuần.

> Đây là **kế hoạch**, không phải code. Mở thư mục `D:\claude\mathtutor` bằng Claude Code,
> để Claude đọc `CLAUDE.md` + `docs/` rồi chạy từng phase bằng prompt trong `docs/PHASE_PROMPTS.md`.

## Thư mục dự án

`D:\claude\mathtutor` (Windows). Mọi đường dẫn trong tài liệu dùng dạng này.

## Bộ tài liệu

| File | Vai trò |
|------|---------|
| `CLAUDE.md` | Hướng dẫn thường trực + **vòng lặp tự động build-test-fix bắt buộc** ở mỗi bước. Claude đọc đầu mỗi phiên. |
| `docs/ARCHITECTURE.md` | Kiến trúc, cây thư mục, luồng một lượt hội thoại, phân quyền. |
| `docs/DATA_MODEL.md` | Schema chi tiết + dữ liệu mẫu (1 bài mỗi loại) + tài khoản seed 3 vai trò. |
| `docs/PLAN.md` | 12 phase, mỗi phase có mục tiêu + Definition of Done + lệnh build/test. |
| `docs/PHASE_PROMPTS.md` | **Prompt copy-paste** cho từng phase. |
| `docs/PROMPTS_LLM.md` | Prompt cho LLM trong sản phẩm: diễn đạt (kịch bản mềm), sinh câu hỏi, viết lại khi chốt chặn. |
| `docs/UIUX_DESIGN.md` | Hướng dẫn thiết kế UI/UX + quy trình dùng Claude Design cho frontend. |
| `docs/TESTING.md` | Chiến lược test + ca test bắt buộc + cấu hình auto build-test-fix. |

## Cách dùng

1. Tạo thư mục `D:\claude\mathtutor`, copy toàn bộ file `.md` này vào (giữ cấu trúc `docs/`).
2. Mở bằng Claude Code tại `D:\claude\mathtutor`.
3. Dán **Prompt khởi động** (trong `PHASE_PROMPTS.md`) để Claude đọc hiểu và xác nhận kế hoạch.
4. Chạy lần lượt Phase 0 → Phase 11 bằng prompt copy-paste. Mỗi phase Claude TỰ build-test-fix
   đến khi xanh rồi báo cáo lỗi đã gặp + cách xử lý, sau đó dừng chờ bạn xác nhận.
5. Phase thiết kế UI (Phase 7) có thể dùng Claude Design — xem `UIUX_DESIGN.md`.

## Stack đã chốt

- Backend: Python 3.11+, FastAPI, SQLAlchemy, SymPy (+ antlr4 cho parse_latex), pytest, JWT
- Frontend: React + Vite, KaTeX (render), MathLive (editor công thức), TailwindCSS
- CSDL: PostgreSQL (dev có thể SQLite — xem CLAUDE.md)
- LLM: gọi qua service riêng, có Stub tất định để test/demo

## Nguyên tắc bất biến (chi tiết trong CLAUDE.md)

- LLM KHÔNG tự giải toán, KHÔNG quyết đúng/sai. Đúng/sai do CAS hoặc dữ liệu chuẩn.
- KHÔNG bao giờ lộ đáp án cho học sinh.
- Hai lõi tự viết (matching CAS, orchestrator) tách module, không import LLM.
- Mỗi bước: TỰ ĐỘNG build → test → fix đến hết lỗi → báo cáo. Không bỏ qua test.
