# CLAUDE.md — Hướng dẫn thường trực cho Claude Code (MathTutor v3)

Đọc file này đầu mỗi phiên, cùng toàn bộ `docs/`. Dự án **MathTutor**: gia sư Toán lớp 12
theo phương pháp Socratic, hội thoại tự nhiên, 3 loại câu hỏi, editor công thức, phân quyền
3 vai trò. Thư mục dự án: `D:\claude\mathtutor`.

## 1. Bản chất sản phẩm

- Gia sư DẪN DẮT học sinh tự tìm đáp án bằng câu hỏi gợi mở. KHÔNG đưa lời giải.
- Hội thoại theo mô hình **"kịch bản mềm"**: giữ rào chắn (CAS, lời giải chuẩn, chốt chặn)
  nhưng LLM diễn đạt tự nhiên, bám câu trả lời học sinh; gợi ý là Ý CHÍNH (la bàn), số gợi ý mỗi
  bước LINH HOẠT (mặc định theo độ khó: Dễ 2, TB 3, Khó 4; GV chỉnh được), không cố định 3.
  không phải lời thoại cứng.
- 3 loại câu: `TN4PA` (chọn A/B/C/D), `TNDS` (4 ý a/b/c/d Đúng/Sai, điểm bậc thang),
  `TLN` (tự tìm 1 giá trị cuối).
- 3 vai trò: `admin` (dashboard toàn hệ thống), `gv` (quản lý câu hỏi/gợi ý/cờ/HS, theo dõi
  tiến bộ, AI sinh câu hỏi + duyệt), `hs` (chọn & luyện, làm tiếp bài dở, bảng tiến độ).

## 2. ⚙️ VÒNG LẶP TỰ ĐỘNG BUILD–TEST–FIX (bắt buộc mỗi bước)

Sau MỖI lần viết hoặc sửa code trong một phase, TỰ ĐỘNG thực hiện, KHÔNG chờ tôi nhắc:

```
1. BUILD lại:
   - Backend: cài deps nếu cần; chạy `ruff check` + `python -c "import app.main"` (import smoke).
   - Frontend: `npm run build` (hoặc `npm run dev` smoke nếu chưa có build).
2. TEST: chạy `pytest` (backend) và test frontend nếu có.
3. NẾU CÒN LỖI: tự đọc log, sửa, rồi quay lại bước 1. Lặp đến khi BUILD và TEST đều xanh.
   - Giới hạn an toàn: nếu sau 5 vòng vẫn lỗi cùng nguyên nhân, DỪNG và báo tôi (đừng lặp vô hạn).
4. BÁO CÁO cho tôi, ngắn gọn, theo mẫu:
   - ✅ Build: OK/Fail
   - ✅ Test: X passed / Y failed
   - 🐞 Lỗi đã gặp: <liệt kê từng lỗi>
   - 🔧 Đã xử lý: <cách sửa từng lỗi>
   - 📋 DoD phase: <mục nào đạt/chưa>
5. Đề xuất 1 commit message. DỪNG, chờ tôi xác nhận sang phase kế.
```

Quy ước báo lỗi: luôn nói RÕ lỗi gì, nguyên nhân, sửa thế nào — kể cả lỗi nhỏ. Đây là yêu cầu
bắt buộc của tôi để theo dõi.

## 3. NGUYÊN TẮC BẤT BIẾN — vi phạm là lỗi nghiêm trọng

1. **LLM không tự giải toán.** Mỗi bài có lời giải chuẩn trong CSDL. LLM chỉ diễn đạt gợi ý
   và trò chuyện quanh bước/ý đã biết, theo chỉ thị có cấu trúc từ lớp điều phối.
2. **LLM không quyết đúng/sai.** Đúng/sai biểu thức/giá trị do CAS (SymPy); đúng/sai ý TNDS và
   phương án TN4PA do dữ liệu chuẩn.
3. **Không bao giờ lộ đáp án.** `dap_an_dung`, `dap_an` (ý), `dap_an_cuoi`, `bieu_thuc_ket_qua`
   CHỈ để máy đối chiếu, KHÔNG xuất hiện trong văn bản gửi HS. Lớp chốt chặn (Phase 5) rà mọi
   phản hồi trước khi gửi. Càng nới hội thoại tự nhiên, chốt này càng phải kỹ.
4. **Hai lõi tự viết tách module, có test:** `core/matching` (CAS + bậc thang) và
   `core/orchestrator` (máy trạng thái). KHÔNG import LLM, KHÔNG import web framework.
5. **An toàn HS là mặc định.** Có lọc nội dung lứa tuổi và khóa phạm vi.
6. **Phân quyền chặt.** Mỗi endpoint kiểm vai trò; HS không thấy đáp án/quản trị; GV chỉ thấy
   lớp mình; chỉ Admin quản trị hệ thống.

## 4. Quy trình mỗi phase

1. Đọc mục phase trong `docs/PLAN.md` + prompt trong `docs/PHASE_PROMPTS.md`.
2. Nêu ngắn các file sẽ tạo/sửa, rồi thực thi.
3. Viết test cho phần lõi của phase.
4. Chạy vòng lặp build-test-fix (mục 2).
5. Kiểm theo Definition of Done của phase.
6. Báo cáo theo mẫu mục 2 + commit message. DỪNG.
- KHÔNG nhảy phase. Phát hiện đặc tả thiếu/mâu thuẫn → DỪNG, hỏi, đừng tự bịa nghiệp vụ.

## 5. Quy ước code

- Python 3.11+, type hints ở hàm public, `ruff` lint, `black` format.
- Tên biến nghiệp vụ giữ tiếng Việt không dấu như đặc tả: `loai_cau`, `buoc_hien_tai`,
  `cap_goi_y`, `dap_an_cuoi`, `bieu_thuc_ket_qua`, `che_do_so_khop`...
- API REST prefix `/api`, JSON, lỗi nghiệp vụ trả message tiếng Việt rõ ràng.
- Xác thực JWT; middleware kiểm vai trò.
- Frontend React function components + hooks + TailwindCSS. KHÔNG dùng localStorage cho state lõi.
- Mọi prompt LLM ở `backend/app/llm/prompts.py` (theo `docs/PROMPTS_LLM.md`). Không rải rác.
- Commit nhỏ, dạng `feat:`/`test:`/`fix:`/`chore:`/`ui:`.
- **Đồng bộ tài liệu**: `docs/ARCHITECTURE.md` + `docs/DATA_MODEL.md` (từ v126) CỐ TÌNH chỉ giữ
  phần kiến trúc/lõi ỔN ĐỊNH và trỏ tới nguồn tự-đúng (endpoint→`/docs` FastAPI; cột đầy đủ→
  `models/*.py` + Alembic baseline). Đổi endpoint/model KHÔNG cần cập nhật 2 file này TRỪ KHI
  chạm phần cốt lõi/nguyên tắc bất biến (vd thêm ràng buộc "không lộ đáp án"). Đừng chép lại
  chi tiết từng file/cột/endpoint vào doc — đó là thứ đã khiến chúng lỗi thời (xem
  `docs/PROGRESS.md` v126).

## 6. CSDL & môi trường (Windows, D:\claude\mathtutor)

- Đích PostgreSQL; dev/test dùng SQLAlchemy với env `DATABASE_URL` (mặc định SQLite `dev.db`).
  Test dùng SQLite in-memory.
- Lệnh chạy giả định Windows; dùng `python -m venv .venv` và `.venv\Scripts\activate`.
- Mọi truy cập DB qua repository/service, không query thẳng trong route.
- Đổi schema DB: dùng **Alembic** (`backend/alembic/`) — sửa model → `alembic revision
  --autogenerate -m "..."` → đọc kỹ file sinh ra (đặc biệt FK vòng tròn, kiểu cột tùy biến) →
  test `upgrade head`/`downgrade -1` trên bản sao dữ liệu thật trước khi push. App tự
  `alembic upgrade head` lúc khởi động (`app/db/migrate.py`), không cần bước deploy riêng.
  Chi tiết đầy đủ ở `docs/PROGRESS.md` mục 5.

## 7. LLM

- Lời gọi LLM sau interface `LLMClient` ở `backend/app/llm/client.py`. Có `StubLLMClient`
  tất định để test/demo không cần mạng.
- Env: `LLM_PROVIDER` (`stub`|`openai`|`gemini`), `LLM_API_KEY`, `LLM_MODEL`,
  `LLM_TEMPERATURE` (mặc định thấp ~0.2). Cấm hard-code key.
- API lỗi → trả gợi ý mặc định từ ý gợi ý, không sập.

## 8. Điều CẤM

- Cấm LLM tự sinh lời giải/tự chấm đúng/sai LÚC HS ĐANG HỌC.
- Cấm in bất kỳ trường đáp án ra response người dùng.
- Cấm bỏ qua build-test-fix của một phase.
- Cấm hard-code key; chỉ đọc env.
- Cấm 2 lõi (`matching`, `orchestrator`) phụ thuộc LLM/web.

## 9. Tham chiếu

Kiến trúc `docs/ARCHITECTURE.md` · Schema `docs/DATA_MODEL.md` · Kế hoạch `docs/PLAN.md` ·
Prompt phase `docs/PHASE_PROMPTS.md` · Prompt LLM `docs/PROMPTS_LLM.md` ·
Thiết kế UI `docs/UIUX_DESIGN.md` · Test `docs/TESTING.md`.
