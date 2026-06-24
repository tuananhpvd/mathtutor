# PROGRESS.md — Trạng thái & bàn giao (cập nhật để kế thừa giữa các phiên/máy)

> File này là "trí nhớ đi theo repo". Bộ nhớ tự động của Claude Code nằm trên máy local,
> KHÔNG lên GitHub — nên mọi quyết định/trạng thái cần nhớ hãy ghi vào đây hoặc vào `docs/`.
> Đọc cùng `CLAUDE.md` đầu mỗi phiên.

## 1. Trạng thái tổng quan (tính đến 2026-06-24)

- Backend (FastAPI + SQLAlchemy) và Frontend (React + Vite + Tailwind) đã chạy được end-to-end.
- **117/117 test backend xanh** (`pytest`). 2 lõi `core/matching` và `core/orchestrator` không phụ
  thuộc LLM/web (đúng nguyên tắc bất biến trong CLAUDE.md).
- Đã có đủ 3 vai trò (admin/gv/hs), 3 loại câu (TN4PA/TNDS/TLN), phân cấp Chuyên đề → Dạng,
  AI sinh câu (stub tất định), chốt chặn rò rỉ đáp án, tiến độ + làm tiếp bài dở.
- Phase 0–10 về cơ bản đã hiện thực; đang ở giai đoạn hoàn thiện trải nghiệm (Phase 11).

## 2. Việc vừa làm gần đây (chưa nằm trong PLAN/DoD)

- **Danh mục Chuyên đề → Dạng:** thêm model `ChuyenDe`/`Dang`, `Problem.dang_id`; API `/api/danh-muc`;
  frontend HS chọn bài phân cấp; GV quản lý danh mục.
- **Seed 12 bài test:** 2 chuyên đề × 2 dạng × 3 loại câu đủ mức độ (`backend/app/data/seed/problems.json`).
- **Sửa guard lọc nhầm** (`core/guard/leak.py`): chỉ chặn khi giá trị đáp án đứng SAU từ khoá lộ
  ("đáp án/kết quả là/bằng/="), tránh chặn nhầm số tự nhiên trong biểu thức toán.
- **Diễn đạt gợi ý tự nhiên hơn (stub):** `StubLLMClient.dien_dat` có lời dẫn riêng theo từng
  `y_dinh` (mở bài / gợi ý / hỏi ngược / xác nhận đúng / chuyển ý / kết thúc), nhiều biến thể,
  leo thang theo cấp gợi ý — vẫn TẤT ĐỊNH (chọn biến thể theo seed) nên test ổn định.
- **Viết lại toàn bộ `danh_sach_goi_y`** trong seed thành câu Socratic gợi mở, leo thang; gợi ý
  mạnh nhất chỉ đưa phương pháp, bắt HS tự tính bước cuối (không ghi sẵn đáp số).

## 3. Quyết định sản phẩm cần nhớ

- **UI hiện bỏ ô chat tự do của HS:** trong `frontend/src/pages/hs/PhongHoc.jsx` HS chỉ có nút
  "GỢI Ý CHO EM" + ô gửi đáp án. Tương tác gần như một chiều. Backend (`/api/sessions/{id}/message`)
  VẪN nhận `noi_dung` tự do — khả năng hội thoại 2 chiều chưa bị xoá, chỉ bị ẩn ở UI.
- **LLM thật (OpenAI/Gemini) tạm hoãn.** Đang dùng `LLM_PROVIDER=stub`. Khi nào khôi phục ô chat
  2 chiều thì bật LLM thật mới phát huy (xem `SYSTEM_DIEN_DAT` trong `backend/app/llm/prompts.py`).
  Hiện chỉ có `OpenAILLMClient`; muốn Gemini phải viết thêm `GeminiLLMClient` trong `llm/client.py`.

## 4. Chạy dự án

Backend:
```
cd backend
python -m venv .venv && .venv\Scripts\activate     # lần đầu
pip install -e .                                    # lần đầu
uvicorn app.main:app --reload --port 8000           # DB tự seed nếu chưa có user
```
Frontend:
```
cd frontend
npm install                                         # lần đầu
npm run dev                                          # http://localhost:5173 (proxy /api → :8000)
```
Tài khoản seed: `admin/admin123`, `gv1/gv123`, `hs1/hs123`.

> Lưu ý DB: `Base.metadata.create_all()` KHÔNG ALTER bảng cũ. Khi đổi model → xoá `backend/dev.db`
> rồi chạy lại để seed schema mới. `init_db` chỉ seed khi chưa có user nào.

## 5. Việc tiếp theo gợi ý

- [ ] (Tùy chọn) Khôi phục ô chat 2 chiều cho HS nếu muốn gia sư Socratic thật.
- [ ] (Tùy chọn) Bật LLM thật: cấu hình `.env` từ `.env.example`, hoặc viết `GeminiLLMClient`.
- [ ] Rà DoD toàn sản phẩm (Phase 11) theo `docs/PLAN.md`.
