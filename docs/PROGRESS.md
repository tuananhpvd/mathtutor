# PROGRESS.md — Trạng thái & bàn giao (cập nhật để kế thừa giữa các phiên/máy)

> File này là "trí nhớ đi theo repo" (lên GitHub). Bộ nhớ tự động của Claude Code nằm trên máy
> local, KHÔNG lên GitHub — nên mọi quyết định/trạng thái cần nhớ hãy ghi vào đây hoặc vào `docs/`.
> **Đọc cùng `CLAUDE.md` đầu mỗi phiên. Mỗi lần làm xong việc đáng kể, CẬP NHẬT file này.**

## 1. Trạng thái tổng quan (cập nhật 2026-07-08, phiên bản **v67**)

- Backend (FastAPI + SQLAlchemy, SQLite `dev.db` / đích PostgreSQL) + Frontend (React + Vite +
  Tailwind) chạy end-to-end. **359/359 test backend xanh** (`pytest`).
- **✅ Fix lỗi AI tự bịa gợi ý lạc đề (v67):** GV báo AI diễn đạt gợi ý cho câu hỏi cực trị lại
  tự chêm "tìm giá trị lớn nhất/nhỏ nhất trên đoạn" — nội dung KHÔNG có trong
  `danh_sach_goi_y` đã lưu. Điều tra bằng dữ liệu production thật (Problem 35): xác nhận gợi ý
  lưu trong DB hoàn toàn đúng chủ đề, lỗi hoàn toàn ở khâu AI diễn đạt. 2 nguyên nhân cộng dồn:
  (1) `ChiThi` gửi cho AI **chưa từng có đề bài** — orchestrator/state.py không mang `de_bai`;
  (2) lỗi truyền sai tham số ở CẢ 3 client thật (`client.py`): `user_prompt_dien_dat()` bị gán
  nhầm `ngu_canh_hs` vào đúng chỗ đáng lẽ là đề bài, khiến AI hoàn toàn không biết ngữ cảnh câu
  hỏi, chỉ có mỗi gợi ý cụt → tự bịa khung quen thuộc (dễ lẫn dạng bài liền kề cùng chuyên đề).
  Sửa: thêm `de_bai` xuyên suốt `TrangThaiPhien` → `ChiThi` → LLM (lõi `core/orchestrator` vẫn
  KHÔNG import LLM/web — đã quét xác nhận, giữ đúng nguyên tắc bất biến #4); sửa tham số sai ở
  cả 3 client; siết `SYSTEM_DIEN_DAT` cấm AI tự chêm phương pháp/khung giải ngoài "y_goi_y".
  **Đã xác minh thật**: gọi Gemini thật 5/5 lần với đúng dữ liệu câu hỏi gây lỗi — không còn
  lần nào lạc đề. 6 test mới (`test_de_bai_ngu_canh.py`).
- **✅ Fix lệch múi giờ 7 tiếng toàn hệ thống (v66):** xác nhận qua gọi API thật — mọi mốc thời
  gian gửi cho frontend thiếu hậu tố múi giờ (vd `"2026-07-07T16:25:54"` thay vì cần
  `"...+00:00"`). Giá trị lưu trong DB đúng là UTC (code đã dùng
  `datetime.now(timezone.utc)` nhất quán từ trước), nhưng cột `DateTime` trơn (không
  `timezone=True`) làm SQLAlchemy/SQLite/Postgres bỏ mất tzinfo khi đọc lại → JSON thiếu hậu
  tố → frontend (`new Date(...)`) hiểu nhầm thành giờ local trình duyệt → hiển thị lệch đúng 7
  tiếng ở VN. Phát hiện thêm: có 1 chỗ (`QuanLyDeThi.jsx` cột "Nộp lúc") từng tự vá bằng nối
  thêm `'Z'`, chỉ đúng 1 nơi, hàng chục nơi khác (thông báo, mục tiêu, phân tích, nhiệm vụ,
  trang chủ HS...) vẫn lệch.
  - **Sửa tận gốc, không vá từng chỗ**: kiểu cột dùng chung `UTCDateTime`
    (`backend/app/db/types.py`) — tự gắn lại tzinfo=UTC khi đọc từ DB. Áp dụng cho **toàn bộ 14
    model** có mốc thời gian (đã quét xác nhận không sót). Gỡ chỗ vá `+ 'Z'` cũ ở
    `QuanLyDeThi.jsx` (nếu để nguyên sẽ hóa "Invalid Date" vì backend giờ đã tự thêm hậu tố,
    nối thêm sẽ thành chuỗi kép).
  - **⚠️ KHÔNG cần chạy migration DB, KHÔNG đổi dữ liệu đã lưu trên production** — chỉ đổi cách
    Python đọc dữ liệu (giá trị lưu vốn đã đúng UTC từ trước). An toàn tuyệt đối với dữ liệu
    GV/HS thật đã có trên Render (theo đúng yêu cầu user: chỉ đưa code, không ảnh hưởng dữ
    liệu).
  - 4 test mới khóa hành vi (`test_utc_datetime.py`).
- **✅ Fix ảnh câu hỏi không hiện ở phòng học HS (v65):** HS báo câu hỏi có hình không thấy ảnh
  khi làm bài. Điều tra xác nhận backend KHÔNG lỗi — cả `GET /sessions/{id}` (làm tiếp bài dở,
  `ChiTietPhienResponse`) lẫn `GET /problems/{id}` (bắt đầu bài mới, `_strip_answers`) đều đã
  trả đúng `hinh_anh` (xác minh trực tiếp bằng gọi hàm thật với dữ liệu thật, không chỉ đọc
  code). Lỗi nằm ở `frontend/src/pages/hs/PhongHoc.jsx`: khi nhận dữ liệu về, code liệt kê tay
  từng trường để lưu vào state `problem` nhưng bỏ sót `hinh_anh` ở CẢ 2 nhánh (bắt đầu bài mới
  dòng ~180, làm tiếp bài dở dòng ~158) — dữ liệu server gửi đúng nhưng bị rơi mất trước khi
  render. Thêm `hinh_anh` vào cả 2 object literal.
- **✅ Thống kê ngân hàng câu hỏi cho GV (v64):** trang "Quản lý câu hỏi" (GV), phía trên "Lọc
  trạng thái duyệt" — thêm panel `ThongKeChuyenDe` (`QuanLyCauHoi.jsx`), qua vài vòng chỉnh theo
  ảnh mẫu user gửi:
  - Đầu panel: `TomTatTongQuan` — tổng câu hỏi + tổng theo Dễ/TB/Khó toàn bộ chuyên đề, luôn hiện.
  - Mỗi chuyên đề (accordion, bấm mới mở): `TongQuanChuyenDe` (4 thẻ tổng+mức độ kèm % trong
    chuyên đề đó, rồi 3 thẻ theo loại câu TN4PA/TNDS/TLN kèm số Dễ/TB/Khó) → sau đó lưới 2 cột
    `TheDangChiTiet` theo từng dạng, mỗi thẻ có bảng chéo loại câu × mức độ (`BangChiTietChuyenDe`)
    + thanh tỉ lệ mức độ.
  - Màu: tái dùng đúng token màu trạng thái sẵn có của app (`success/warning/danger` cho Dễ/TB/
    Khó, nhất quán với `ThongKeTienDo.jsx`) — không tự bịa hex mới, theo đúng quy tắc
    `styles/README.md` mục "Nguyên tắc khi dựng trang mới".
  - Đếm TẤT CẢ trạng thái duyệt, không phụ thuộc bộ lọc "Lọc trạng thái duyệt" bên dưới.
  - Phân trang 20 câu/trang ở bảng danh sách bên dưới **đã có sẵn từ trước** (`MOI_TRANG_CH`),
    không cần thêm việc gì.
  - ⚠️ **5 lỗi lint có sẵn từ trước** trong `QuanLyCauHoi.jsx` (không phải do đợt sửa này gây
    ra, đã xác nhận qua `git stash`): 3 hàm tiện ích export chung file component
    (`kiemTraDapAnTLN`/`dungDangOptions`/`chuanHoaSteps` — bị `AISinhCauHoi.jsx` import dùng
    chung, muốn sửa cần tách file riêng), 1 hàm chết `dinhDangNgay` không nơi nào gọi, 1
    `setState` gọi trực tiếp trong `useEffect`. Chưa sửa — đang chờ user quyết định.
- **✅ Ô xem trước hiện cả khi không có công thức toán (v63):** `TexField` (`QuanLyCauHoi.jsx`)
  — trước đây chỉ hiện ô xem trước khi nội dung có chứa `$...$`, khiến GV thấy không đồng bộ
  (ô có công thức thì có khung xem trước, ô toàn chữ thì không). Bỏ điều kiện bắt buộc có
  `$...$`, giờ chỉ cần có giá trị là hiện khung xem trước — `renderTex` không đổi nên vẫn nhận
  diện đúng công thức khi có, chữ thường thì hiện y nguyên. Đồng bộ với v61-v62 (tô màu nền
  xanh cho khung này).
- **✅ Tô màu nền ô xem trước công thức (v61-v62):** `TexField` (`QuanLyCauHoi.jsx`) — ô xem
  trước render KaTeX bên dưới mỗi input giờ có nền + viền + bo góc thay vì chỉ chữ trơn, giúp GV
  phân biệt rõ ô nhập vs ô xem trước. Sửa 1 chỗ dùng chung cho toàn bộ đề bài/phương án A–D/ý
  a–d/mô tả bước/gợi ý, ở cả 3 nơi: Tạo câu hỏi, Sửa câu hỏi, panel "AI tạo bước và gợi ý" (kể
  cả nhánh từ ảnh). v62: theo mẫu ảnh user gửi, đổi từ nền xám trung tính (`bg-surface-2` +
  viền xám) sang nền xanh dương nhạt theo màu chủ đạo hệ thống (`bg-primary-soft` + viền
  `border-primary/30`, bo góc lớn hơn `rounded-lg`) — rõ ràng/dễ phân biệt hơn.
- **✅ Fix lỗi thêm câu hỏi bị trùng ID (v60):** GV báo lỗi lưu câu hỏi mới:
  `UniqueViolation ... solution_steps_pkey ... Key (id)=(44) already exists`. Nguyên nhân: hậu
  quả sót lại từ lần migrate dữ liệu local→production (v54) — script chèn thẳng "id" có sẵn từ
  SQLite (không qua `nextval()`), khiến sequence tự tăng của Postgres KHÔNG biết mà cập nhật
  theo, bị kẹt ở giá trị thấp trong khi dữ liệu thật đã có ID cao hơn nhiều. Kiểm tra xác nhận
  **6/7 bảng migrate lần đó đều bị lệch** (`users, lop, chuyen_de, dang, solution_steps,
  thong_bao` — riêng `problems` tình cờ đã tự đồng bộ nhờ các lần tôi tạo/xóa câu hỏi test khi
  điều tra lỗi AI trước đó). **Đã sửa NGAY trên production** (chạy `setval()` đồng bộ lại cả 7
  sequence về đúng `MAX(id)` — không cần chờ deploy) + xác minh thật bằng tạo 1 câu hỏi qua đúng
  luồng ORM (id cấp đúng, không trùng) rồi xóa dữ liệu test. **Sửa gốc trong code**:
  `backend/scripts/migrate_local_to_prod.py` thêm bước tự động `setval()` sau khi chèn dữ liệu —
  nếu sau này dùng lại script này (môi trường khác) sẽ không lặp lại lỗi này.
- **✅ Fix model dự phòng Gemini bị hỏng (v59):** GV báo lỗi đọc ảnh "404 NOT_FOUND ...
  gemini-2.0-flash is no longer available". Xác nhận bằng gọi API thật: Google ĐÃ khai tử model
  `gemini-2.0-flash` (dù vẫn còn hiện trong `models.list()` — không tin danh sách, phải gọi thật
  mới biết chắc), model này nằm trong `_DU_PHONG` (danh sách dự phòng khi model chính lỗi).
  2 lỗi cộng dồn: (1) danh sách dự phòng có model đã chết, (2) code cũ chỉ coi mã lỗi **429**
  (hết quota) là lý do thử model kế tiếp — **404** (model không tồn tại) bị `raise` ngay, không
  thử các model dự phòng còn lại dù chúng vẫn hoạt động tốt. Sửa: bỏ `gemini-2.0-flash` khỏi
  `_DU_PHONG`, thay bằng `gemini-flash-latest` (alias Google luôn trỏ model flash hiện hành);
  coi 404 giống 429 (đều thử model kế tiếp), 400/401/403 vẫn dừng ngay (không liên quan tới việc
  đổi model). Thứ tự gọi hiện tại (Admin để trống ô Model): `gemini-2.5-flash` →
  `gemini-2.5-flash-lite` → `gemini-flash-latest`. **Đã xác minh 2 lần bằng gọi Gemini thật**:
  ép model chính = model đã chết → xác nhận tự chuyển sang model dự phòng thành công, kiểm tra
  cả đường `_call` (hội thoại) lẫn `_call_voi_anh` (đọc ảnh — đúng nơi lỗi xảy ra ban đầu). 4
  test mới khóa hành vi (404/429 đều chuyển model, 400 dừng ngay, không còn model chết trong
  danh sách).
- **✅ Fix câu diễn đạt gửi HS bị cắt cụt giữa chừng (v58):** GV báo câu chat với HS kiểu
  "...tính đạo" (thiếu "hàm"). Điều tra bằng gọi Gemini thật với đúng config production → xác
  nhận nguyên nhân: Admin bật "Chế độ suy luận (thinking)" cho Gemini (`llm_thinking_gemini=True`)
  khiến `dien_dat()` (max_tokens=512, câu ngắn) bị suy luận nội bộ ăn hết ngân sách token, chỉ
  còn ít token cho câu trả lời thật → cắt giữa từ. Gemini's `phan_tich()` đã có sẵn cơ chế tắt
  thinking đúng, nhưng `dien_dat()` bị bỏ sót; `AnthropicLLMClient` thiếu ở CẢ `dien_dat` VÀ
  `phan_tich` (không nhất quán). Sửa: cả 2 phương thức ở cả 2 provider giờ LUÔN
  `suy_nghi=False` — không phụ thuộc ô Admin (ô đó chỉ nên ảnh hưởng sinh câu hỏi/tạo bước gợi ý,
  việc thật sự cần suy luận sâu). **Đã xác minh 2 lần bằng gọi Gemini thật** (trước sửa: tái
  hiện đúng lỗi cắt cụt; sau sửa: gọi qua `dien_dat()` công khai dù client vẫn suy_nghi=True vẫn
  ra câu đầy đủ). 4 test mới khóa hành vi.
- **✅ "AI tạo bước và gợi ý từ hình ảnh" (v57):** mở rộng panel "AI tạo bước và gợi ý" (v50) —
  GV vẫn chọn chuyên đề/dạng/loại câu/độ khó/số bước/số gợi ý như cũ, nhưng có thể **dán ảnh
  chụp đề (Ctrl+V)** thay vì gõ tay. AI (chỉ Gemini, theo quyết định user) đọc ảnh, đối chiếu
  với "Loại câu" GV đã chọn: khớp → tự điền đề bài/phương án/ý vào đúng ô chữ để GV kiểm tra lại
  trước khi bấm "Tạo" như luồng cũ; KHÔNG khớp → báo lỗi rõ, KHÔNG tự sinh bừa. Ảnh CHỈ dùng để
  đọc, không lưu vào DB — giữ nguyên hiển thị cho GV đối chiếu tới khi bấm "Xóa ảnh" hoặc bấm
  "Tạo bước và gợi ý" (theo yêu cầu UX của user, sửa sau khi code xong bản đầu).
  - Backend: `LLMClient.doc_de_tu_anh()` (mặc định báo lỗi rõ "chưa hỗ trợ", chỉ
    `GeminiLLMClient` override thật qua `_call_voi_anh` — gọi Gemini multimodal thật). Endpoint
    `POST /questions-ai/doc-de-tu-anh`. Giới hạn ảnh 5MB, chỉ PNG/JPEG/WEBP. 16 test mới
    (`test_doc_de_tu_anh.py`) — **đã xác minh THẬT bằng cách gọi qua HTTP thật tới Gemini thật**
    (không chỉ mock), theo đúng bài học rút ra từ sự cố Stub-fallback (v56): luôn kiểm tra đúng
    môi trường/luồng thật trước khi báo đã xong.
  - Frontend: `AISinhCauHoi.jsx` thêm `ODanAnh` (ô dán ảnh clipboard).
- **✅ Bổ sung ký hiệu Bảng công thức toán (v57):** cả 2 phía —
  - GV (`QuanLyCauHoi.jsx` → `NHOM_CONG_THUC`, dùng chung Tạo/Sửa câu hỏi + panel AI): thêm nhóm
    "Hàm sơ cấp" (sin/cos/tan/cot/ln/log_a/eˣ/|x|), "Tập hợp - Logic" (∈∉⊂∅∩∪∀∃), "Tổ hợp - Xác
    suất" (C_n^k/A_n^k/n!/P(A)/|/Σ). **Phát hiện + fix thêm 6 nút CŨ bị sai vị trí con trỏ**
    (x^n, dfrac, int_a^b, f'(x), f''(x), F(x) — bấm xong con trỏ nằm lệch ra ngoài dấu ngoặc
    thay vì nằm gọn bên trong) — lỗi có từ trước, phát hiện khi rà cơ chế `back` offset lúc thêm
    nút mới; đã mô phỏng xác minh lại toàn bộ ~30 nút trước khi báo xong.
  - HS (`components/answer/MathPalette.jsx`, dùng MathLive `\placeholder{}` nên không có rủi ro
    lệch con trỏ như bên GV): thêm nhóm "Tổ hợp · Vectơ · Số phức" (C_n^k, A_n^k, P(A), P(A|B),
    ∈∪∩, vectơ, số ảo i, liên hợp z̄, |z|, ⟂).
- **🐞 Phát hiện lớn — production CHƯA TỪNG gọi Gemini thật (v56):** GV báo "AI sinh câu hỏi sai
  chuyên đề, trùng lặp" — điều tra ban đầu (v55) chẩn đoán SAI là do AI không ổn định (test bằng
  máy local có sẵn `google-genai` nên không lộ ra lỗi thật). Nguyên nhân THẬT: `pyproject.toml`
  khai `google-genai/anthropic/openai` ở nhóm **optional** `[project.optional-dependencies] llm`,
  nhưng Build Command hướng dẫn lúc deploy Render chỉ là `pip install -e .` (KHÔNG cài extra này)
  → thiếu thư viện → `get_llm_client()` bắt `ImportError` rồi ÂM THẦM rơi về `StubLLMClient`,
  không log gì. Vì `get_llm_client` dùng CHUNG cho 5 nơi (`sessions.py` hội thoại HS,
  `questions_ai.py` sinh câu hỏi, `progress.py` phân tích, `lich_phan_tich.py` quét nền,
  `admin.py` dashboard) → **toàn bộ tính năng AI trên production đều chạy Stub (mẫu cố định) kể
  từ lúc deploy**, dù Admin đã cấu hình đúng Gemini + API key. Dấu hiệu nhận biết: nội dung AI
  sinh giống hệt nhau dù đổi input (khớp nguyên văn template cứng trong `StubLLMClient`).
  - **Fix Render (user tự làm, KHÔNG phải code)**: đổi Build Command service `mathtutor` từ
    `pip install -e .` → `pip install -e ".[llm,dev]"` (hoặc `.[llm]` nếu không cần dev tools).
  - **Fix code (v56)**: `get_llm_client()` giờ **log CẢNH BÁO rõ nguyên nhân** mỗi lần rơi về
    Stub (thiếu thư viện / thiếu API key / provider không hỗ trợ) — trước đây im lặng hoàn toàn.
    `tests/test_llm_client.py` (5 test mới, dùng `caplog`) khóa lại đúng hành vi log này.
  - **Bài học ghi nhớ**: khi debug lỗi có 2 môi trường (local/production), PHẢI xác minh đúng
    môi trường user thực sự gặp lỗi (đọc DB production qua `PROD_DATABASE_URL` nếu cần), không
    suy ra từ kết quả test ở local. Chi tiết ghi trong bộ nhớ tự động phiên `feedback-rigor-...`.
- **✅ Fix lỗi AI sinh câu hỏi rỗng không rõ nguyên nhân (v55):** `sinh_va_luu` giờ tự thử sinh
  lại tối đa `SO_LAN_THU`=3 lần nếu lần trước AI trả về nhưng không câu nào hợp lệ (JSON sai cấu
  trúc/thiếu đề bài/không qua CAS) — trước đây báo lỗi ngay lần đầu, không thử lại, không log lý
  do loại từng câu. Vẫn có ích cho trường hợp AI thật thỉnh thoảng trả JSON hỏng, dù không phải
  nguyên nhân chính của lỗi GV gặp lần này (xem mục Stub-fallback ở trên).
- **🚀 B1 — Deploy lên Render THÀNH CÔNG (v52-v55):** đã lên production thật, không còn "user tự
  lo" như dự kiến ban đầu. Hạ tầng: `mathtutor` (Web Service Python, Starter, có Persistent Disk
  cho `backend/uploads/`) + `mathtutor-1` (Static Site frontend, free, rewrite `/api/*` +
  `/uploads/*` → backend để tránh CORS) + `mathtutor-db` (Postgres, Basic). Workspace Hobby
  (free), chi phí ước tính ~$14-15/tháng (Web Service + Postgres trả phí, Static Site luôn free).
  - **v52 fix:** thiếu driver `psycopg2-binary` (chỉ test SQLite trước giờ) + setuptools tưởng
    `uploads/` là package thứ 2 (local có ảnh test, không nằm trong Git) → thêm
    `[tool.setuptools.packages.find] include = ["app*"]`.
  - **v53 fix:** CORS hardcode localhost → thêm `CORS_EXTRA_ORIGINS` (env, danh sách phẩy) đọc
    từ `config.py`, giữ localhost mặc định cho dev.
  - **v54 fix quan trọng — đã KIỂM CHỨNG TRỰC TIẾP trên Postgres production (bảng tạm)**:
    `_migrate_them_cot` dùng cú pháp SQLite `BOOLEAN DEFAULT 0/1` → Postgres báo lỗi thật
    (`DatatypeMismatch`) khi thêm cột boolean mới. Sửa toàn bộ sang `DEFAULT false/true` (hợp lệ
    cả 2 CSDL). ⚠️ Cột hiện có không sao (đã tạo đúng kiểu từ model lúc `create_all`), NHƯNG mọi
    cột boolean thêm SAU NÀY phải qua đúng cú pháp mới này, không thì vỡ deploy trên production
    thật (có dữ liệu GV/HS thật, không còn là dev.db bỏ được).
  - **Di chuyển dữ liệu local → production (1 lần, `backend/scripts/migrate_local_to_prod.py`)**:
    TRUNCATE rồi nạp lại 7 bảng (`users, lop, chuyen_de, dang, problems, solution_steps,
    thong_bao`) theo đúng thứ tự phụ thuộc khóa ngoại (users↔lop có phụ thuộc vòng → chèn
    users với `lop_id=NULL` trước, cập nhật sau). ⚠️ **KHÔNG chạy lại theo chiều này nữa** — từ
    khi GV/HS bắt đầu dùng thật trên Render, production là nơi giữ dữ liệu thật DUY NHẤT, chạy
    lại sẽ xóa sạch dữ liệu thật. Muốn đồng bộ ngược (prod→local) cần script khác (chưa viết).
  - **Quy trình vận hành đã thống nhất với user:** (1) GV/HS dùng thật trên Render để thêm dữ
    liệu; (2) code tiếp tục sửa ở local → push GitHub → Render tự deploy (auto-deploy). Lưu ý:
    có gắn Persistent Disk nên **mỗi lần deploy có gián đoạn ngắn** (không zero-downtime) — nên
    deploy ngoài giờ HS/GV đang dùng. Luôn chạy build-test-fix xanh trước khi push (giờ ảnh
    hưởng người dùng thật, không chỉ dev.db).
  - **Dọn lịch sử Git**: xóa 2 tác giả thừa trên GitHub Contributors (`tailieuvipabc` — email cũ
    của chính user, và `claude` — từ dòng `Co-Authored-By` sót lại ở 2 commit rất cũ) bằng
    `git filter-repo` (mailmap chuẩn hoá email + message-callback xoá dòng Co-Authored-By), rewrite
    toàn bộ 54 tag để vẫn `git checkout v23` được như cũ (chỉ đổi hash ẩn, không đổi nội dung).
    Có backup bundle trước khi rewrite. Xác nhận sau cùng: lịch sử ĐÃ SẠCH từ trước (rewrite lần
    này no-op) — cái GitHub hiện "3 Contributors" chỉ là cache hiển thị, dữ liệu thật đã đúng.
  - **✅ Fix lỗi AI sinh câu hỏi không ổn định (v55):** GV báo lỗi "Mô hình AI không tạo được câu
    hỏi hợp lệ" trên production. Điều tra bằng cách gọi TRỰC TIẾP đúng API key/model Gemini thật
    lưu trên Postgres production (đọc-only, dọn dữ liệu test ngay sau) → xác nhận key/model/kết
    nối đều ổn, KHÔNG phải lỗi Render hay cấu hình — mà do nhiệt độ sinh > 0 khiến AI thỉnh
    thoảng (đo được ~1/10 lần) trả nội dung không đúng cấu trúc, bị lọc âm thầm không log, không
    thử lại (khác cơ chế thử-lại-3-lần đã có cho lỗi mạng/JSON ở `_goi_va_parse`). Sửa
    `question_gen_service.sinh_va_luu`: tách lọc+lưu ra `_loc_va_luu_nhap` (có log lý do loại mỗi
    câu), bọc trong vòng lặp tự thử sinh lại tối đa `SO_LAN_THU` (=3) lần nếu lần trước không có
    câu nào hợp lệ.
  - **Quy tắc làm việc mới user yêu cầu (2026-07-06)**: mọi yêu cầu code/fix phải phân tích +
    **đánh giá rủi ro cụ thể** + đề xuất + chờ xác nhận trước khi code (đặc biệt liên quan
    DB/production); sau khi test xanh → tóm tắt + nhắc đưa GitHub (không tự push). Cú pháp
    `đưa lên github, ghi chú "..."` → dùng NGUYÊN VĂN phần ngoặc kép làm commit message.
- **✅ Bảng công thức cho panel "AI tạo bước và gợi ý" (v51):** export thêm `BangCongThuc` +
  `TexField` từ `QuanLyCauHoi.jsx`; đề bài/phương án A-D/ý a-d trong panel mới đổi sang
  `TexField` (xem trước công thức + đăng ký làm ô đang focus), thêm cột phải hiện
  `<BangCongThuc>` để chèn ký hiệu LaTeX — giống hệt cơ chế màn Sửa câu hỏi.
- **✅ Fix nghiêm trọng: chèn công thức xóa mất chữ đã gõ (v51)** — lỗi ở `TexField` (dùng
  chung Tạo/Sửa câu hỏi + panel mới), KHÔNG phải lỗi riêng panel mới. Gốc: `focusSelf` chỉ
  đăng ký hàm chèn 1 lần lúc `onFocus`, closure "chốt cứng" `value`/`onChange` tại thời điểm
  đó; gõ thêm chữ sau focus không đăng ký lại → bấm chèn công thức dùng giá trị CŨ (thường
  rỗng) → ghi đè mất hết chữ vừa gõ. Sửa: `useRef` giữ giá trị mới nhất, cập nhật qua
  `useEffect` không dependency (chạy sau mỗi lần render) — đọc tại đúng thời điểm bấm chèn.
  Vòng đầu gán ref trực tiếp trong thân render bị chặn bởi rule mới `react-hooks/refs`
  ("Cannot access refs during render") → chuyển vào `useEffect`. Sửa 1 chỗ tự fix cho cả 3
  nơi dùng chung (Tạo câu hỏi, Sửa câu hỏi, panel AI tạo bước và gợi ý).
- **✅ "AI tạo bước và gợi ý" (v50)** — GV viết đề bài (+ phương án/ý), AI CHỈ giải + chia bước
  + viết gợi ý (không tự bịa đề — khác "Sinh hàng loạt"). `LLMClient` thêm phương thức
  `tao_buoc_goi_y()` (interface + Stub/OpenAI/Anthropic/Gemini, cùng khuôn `sinh_cau_hoi`).
  `prompts.py`: `SYSTEM_TAO_BUOC_GOI_Y` + `user_prompt_tao_buoc_goi_y()` — nhồi đúng nội dung
  GV viết, liệt kê cấu trúc bước + số gợi ý bắt buộc. `question_gen.py.sinh_buoc_goi_y()`: ÉP
  lại mọi trường GV cung cấp đè lên AI trả về (đề bài/phương án/ý không đổi dù AI viết gì), đối
  chiếu số bước/gợi ý thực trả vs yêu cầu → cảnh báo (không chặn). `question_gen_service.py`:
  `tao_nhap_buoc_goi_y()` (validate cấu trúc theo loại câu: TNDS bắt buộc đúng 4 bước a→d,
  TN4PA/TLN chỉ `ca_bai`) + `luu_cau_nhap()` (nguon=ai_sinh, cho_duyet). 2 endpoint:
  `/questions-ai/tao-buoc-goi-y` (preview, quota-gated, KHÔNG lưu DB) + `.../luu`. Frontend:
  panel mới đầu trang "AI sinh câu hỏi" — nhập đề/phương án/ý + số bước/số gợi ý mỗi bước →
  Tạo → xem trước tái dùng nguyên `ThanCauHoiForm` (export từ `QuanLyCauHoi.jsx`, sửa được)
  → Lưu. 15 test mới.
- **✅ Fix sửa chuyên đề cho phép sửa kèm mô tả (v49):** backend (model/schema/service) đã hỗ
  trợ `mo_ta` từ trước — lỗ hổng chỉ ở frontend: form sửa tên (`TenChuyenDe` trong
  `QuanLyDanhMuc.jsx`) không có ô mô tả nên không bao giờ gửi lên. Thêm textarea mô tả vào
  khung sửa; sửa điều kiện "không đổi thì bỏ qua" để so cả tên lẫn mô tả (trước chỉ so tên,
  sửa mỗi mô tả bị bỏ qua không lưu); dời preview mô tả vào trong component để tự ẩn lúc đang
  sửa. 4 test mới (sửa tên+mô tả cùng lúc, chỉ sửa mô tả giữ nguyên tên, xóa mô tả về rỗng).
- **✅ Fix badge "Nhà cung cấp LLM" sai nguồn ở Admin Dashboard (v48):** `admin_service.thong_ke()`
  từng đọc `settings.llm_provider` (env, mặc định "stub") thay vì cấu hình Admin lưu trong DB —
  lệch với `get_llm_client()` (nơi thật sự quyết định provider chạy hội thoại, ưu tiên đọc DB).
  Sửa: `lay_cau_hinh(db).get("llm_provider", settings.llm_provider)`. 1 test khóa hành vi.
- **✅ Topbar HS chuyên nghiệp/hiện đại hơn, không cuộn ngang (v48):** gộp "Tài khoản" +
  "Đăng xuất" vào 1 menu avatar (dropdown, mẫu SaaS hiện đại) — nhường chỗ, giảm menu chính từ
  7 còn 6 mục; đổi thanh điều hướng sang dạng segmented-control (track bo tròn, mục chọn nổi
  nền trắng + bóng đổ); logo topbar thu gọn 64→36px (sidebar GV/Admin giữ nguyên); khung nội
  dung nới `max-w-5xl`→`max-w-6xl`. ⚠️ Đổi ngưỡng hiện menu ngang từ `md`(768px)→`lg`(1024px)
  để đảm bảo không tràn/cuộn — mở rộng vùng "chưa có nav mobile/tablet" đã ghi nhận thuộc B2.
  Đổi tên trang "Thi thử THPT" → "Thi thử theo đề hoàn chỉnh".
- **✅ 3 fix lỗi AI sinh câu hỏi (v47), phát hiện qua GV dùng thật:**
  1. **CAS không hiểu ký hiệu tổ hợp/chỉnh hợp** (`cas.py`): AI viết `combinations(5,3)` (không
     phải hàm SymPy thật, hàm đúng là `binomial`) → bước lời giải báo "SymPy không parse được".
     Thêm chuẩn hóa alias trước khi parse: `combinations/comb/nCr/C(n,k)` → `binomial(n,k)`;
     `permutations/perm/nPr/A(n,k)` → `ff(n,k)` (falling factorial = chỉnh hợp). Lợi ích kép:
     câu cũ trong hàng chờ tự parse được, HS gõ `C(5,3)` kiểu SGK khi làm bài cũng chấm đúng.
  2. **Đáp án TLN do AI sinh không đúng định dạng thi thật** (`question_gen.py`): thêm
     `dap_an_tln_hop_le()` — bắt buộc số thập phân, TỐI ĐA 4 ký tự tính cả dấu `-`/`.` (đúng
     quy chế THPT phần III). Hợp lệ: "125", "-125", "3.12", "-3.1"; sai: "-3.124" (6 ký tự).
  3. **Biểu thức kết quả để dạng hàm chưa tính** (vd `binomial(15, 3)` thay vì `455`): tuy CAS
     vẫn chấm đúng (sympify tự eager-evaluate), nhưng hiển thị ở "Xem lại bài" (`XemLaiBai.jsx`
     render thẳng qua KaTeX) ra chữ thô xấu vì không phải LaTeX hợp lệ. Thêm
     `bieu_thuc_trung_gian_chua_tinh()`: cảnh báo kèm giá trị đã tính sẵn khi biểu thức KHÔNG
     còn biến tự do mà vẫn còn `binomial/factorial/ff/combinations/permutations/comb/perm(...)`
     — biểu thức còn biến (đạo hàm theo x) thì không bị cảnh báo.
  - Cả 3 fix đều cập nhật `prompts.py` để giảm tái diễn từ nguồn (chỉ thị tường minh cho AI).
    6 test mới, tổng backend 303/303.
- **✅ C1-GĐ2 — Trộn đề tự động theo ma trận (v46):** service `tron_de()` — ma trận (số câu/
  phần + tỉ lệ % Dễ/TB/Khó mặc định 30/40/30 + giới hạn chuyên đề) → bốc ngẫu nhiên từ ngân
  hàng ĐÃ DUYỆT của GV, đúng loại theo phần, RẢI ĐỀU chuyên đề (round-robin trên danh sách
  xáo trộn từng chuyên đề). Không chặn GV: thiếu mức khó → bù mức khác, thiếu tổng → lấy tối
  đa, mọi trường hợp kèm cảnh báo rõ. `POST /de-thi/tron` chỉ trả ĐỀ XUẤT (không lưu) — UI
  khối gập/mở "🎲 Trộn đề tự động" trong form Tạo đề đổ kết quả vào 3 tab chọn câu để GV
  chỉnh tay rồi mới tạo. 1 test tổng hợp (round-trip trộn → tạo đề).
  → **HOÀN TẤT toàn bộ lộ trình code dự thi B4→B3→C2→C3→C1**; còn C5 (user thực nghiệm theo
  docs/THUC_NGHIEM.md) và B2 mobile (cân nhắc sau nếu còn thời gian).
- **✅ C1-GĐ1 — Chế độ đề ôn thi THPT (v45):** 3 bảng mới `de_thi`/`de_thi_cau`/`bai_thi`
  (create_all tự tạo, không cần migration tay). Chấm đúng quy chế 2025 tái dùng nguyên vẹn
  `core/matching.so_khop`: Phần I TN4PA 0,25đ/câu · Phần II TNDS bậc thang 0,1/0,25/0,5/1,0 ·
  Phần III TLN 0,5đ/câu (CAS so khớp). Đồng hồ SERVER làm trọng tài (hết giờ +30s grace →
  chạm vào bài là tự chốt; đáp án autosave trước hạn vẫn tính). Chốt chặn: đang thi KHÔNG trả
  trường đáp án nào (test khóa quét cả response text); HS chỉ thấy đề PHÁT HÀNH của GV chủ
  nhiệm; GV chỉ ghép câu của mình + đã duyệt + đúng loại theo phần. GV: trang "Đề thi thử"
  (tab 3 phần đếm câu so chuẩn 12/4/6, phát hành/thu hồi, kết quả lớp, chỉ xóa đề chưa ai làm).
  HS: trang "Thi thử" (đếm ngược đỏ <5', lưới câu, autosave khi đổi đáp án + 20s/lần, hết giờ
  tự nộp; kết quả từng câu + nút "Luyện lại với gia sư" mở phiên Socratic câu sai — khép vòng
  thi thử → chữa bài gợi mở). 4 test mới. ⚠️ Bug đã sửa khi code: so sánh `ket_qua.value ==
  "dung"` sai vì enum `KetQuaSoKhop.DUNG` value là "DUNG" in hoa → so sánh enum trực tiếp.
  📌 Còn lại GĐ2: trộn đề TỰ ĐỘNG theo ma trận (chuyên đề × số câu × tỉ lệ Dễ/TB/Khó).
- ⚠️ Phát hiện lệch tài liệu: PROGRESS từng ghi "pham_vi rieng_tu/chung (v22)" nhưng model
  Problem hiện KHÔNG có cột này — quy tắc thật: HS thấy bài `da_duyet` của GV chủ nhiệm.
- **✅ C3 — Bản đồ năng lực heatmap (v44):** `ban_do_nang_luc()` trong phan_tich_service — ô =
  chuyên đề × độ khó, giá trị = điểm thành thạo 0–100 (cùng công thức `_diem_thanh_thao`);
  1 HS = bản đồ cá nhân, nhiều HS = bản đồ lớp DỒN CHUNG phiên (không TB của TB). Phân biệt
  3 trạng thái ô: điểm / "chưa đủ dữ liệu" (xám viền đứt) / chưa làm. 3 endpoint:
  `/progress/me/ban-do`, `/progress/ban-do/lop`, `/progress/students/{id}/ban-do`. Component
  `BanDoNangLuc.jsx` dùng chung (5 bậc tím, số trong ô, prop `khoa` tránh vòng refetch) gắn
  3 nơi: Tiến độ HS, Theo dõi tiến bộ GV (lớp + HS đang chọn). 3 test mới.
- **✅ C5 — Kế hoạch thực nghiệm (v44):** `docs/THUC_NGHIEM.md` — thiết kế trước–sau 3–4 tuần,
  lịch từng tuần, checklist kỹ thuật (bật gemini/phanh B4/ngân hàng câu/backup dev.db), bảng
  chỉ số (đa số tự động từ C2/C3), phiếu khảo sát 10 Likert + 2 mở, mẫu xin phép BGH/PH, quy
  tắc ẩn danh + danh mục minh chứng. Phần thực hiện thuộc về GV (user).
- **✅ C2 — Số liệu chứng minh hiệu quả phương pháp (v43):** `hieu_qua_service.py` tất định
  (không LLM, tính ngược được dữ liệu cũ): phân bố mức gợi ý khi hoàn thành (mức 0 = tự làm /
  1 / 2 / 3+, tỉ lệ tự làm + tối đa mức 1), xu hướng phụ thuộc gợi ý từng HS (TB 5 bài đầu vs
  5 gần nhất, ≥10 bài; giảm = tiến bộ), chuỗi 8 tuần (bài/điểm TB/gợi ý TB). Loại phiên đang
  làm + bi_an. 3 endpoint: `/progress/hieu-qua/lop`, `.../lop/csv` (BOM UTF-8 cho Excel),
  `/progress/students/{id}/hieu-qua` (chặn GV khác lớp). Panel GV `HieuQuaPhuongPhap.jsx` đầu
  trang Theo dõi tiến bộ: 3 stat tile + thanh phân bố sequential tím (palette đã validate
  CVD-safe qua dataviz validator, khe trắng 2px + nhãn trực tiếp + bảng kèm) + bảng xu hướng
  từng HS (icon+nhãn) + mini cột tuần + nút Xuất CSV. Ghi chú trung thực "thống kê mô tả".
  5 test mới.
- **✅ B3 — Xem lại bài sau hoàn thành (v42):** endpoint `GET /api/sessions/{id}/xem-lai` — trả
  đáp án chuẩn theo loại câu (TN4PA/TNDS/TLN), lời giải chuẩn từng bước, hành trình hội thoại
  (mức gợi ý từng lượt, đáp án nhập, thời điểm), thống kê (điểm, gợi ý max, số lượt, thời gian).
  Chốt chặn TẠI BACKEND: phiên chưa hoàn thành → 403 (test khóa "đáp án không lộ lúc đang học");
  HS khác → 404; GV chỉ xem HS lớp mình. Nguyên tắc "không lộ đáp án" chỉ áp dụng LÚC ĐANG HỌC
  (tiền lệ `_dap_an_y_neu_xong` có sẵn). Frontend: `XemLaiBai.jsx` overlay (đề + đáp án + lời
  giải + hành trình dạng chat có nhãn gợi ý mức N + huy hiệu "tự làm không cần gợi ý"); 2 lối
  vào: nút Xem lại ở ChonBai (bài xong) + banner hoàn thành PhongHoc. 4 test mới.
- **🎯 LỘ TRÌNH CẢI TIẾN DỰ THI (chốt 2026-07-04):** B4 phanh chi phí LLM → B3 xem lại bài sau
  hoàn thành → C2 số liệu chứng minh phương pháp → C5 thực nghiệm lớp thật → C3 heatmap năng lực
  → C1 chế độ đề ôn thi THPT. (B2 mobile để cân nhắc sau; B1 deploy/B5 bảo mật/C4 PDF/C6 demo
  user tự lo.) Chi tiết phân tích từng mục nằm trong hội thoại 2026-07-04 — tóm tắt: C5 cần bắt
  đầu sớm nhất vì cần thời gian thật; C1 lớn nhất (3 model mới) chia 2 giai đoạn.
- **✅ B4 — Phanh chi phí LLM (v41):** bảng `llm_su_dung` đếm lượt gọi LLM THẬT theo (ngày UTC,
  user, loại: hoi_thoai/sinh_cau_hoi/phan_tich); 2 khóa cấu hình Admin `gioi_han_llm_hs_ngay`
  (mặc định 30) + `gioi_han_llm_he_thong_ngay` (mặc định 500), 0 = không giới hạn. Hội thoại
  vượt ngưỡng → tự rơi về lời diễn đạt mẫu (StubLLMClient), HS học bình thường vì CAS/orchestrator
  không phụ thuộc LLM; sinh câu hỏi/phân tích thủ công vượt ngưỡng → 429 tiếng Việt rõ; quét nền
  tự bỏ qua vòng khi chạm ngưỡng. UI Admin→Cấu hình hiện "Hôm nay đã dùng X/Y" + cảnh báo ≥80%.
  Service: `llm_quota_service.py` (`ap_quota_hoi_thoai`/`ap_quota_tac_vu`). 13 test mới.
- **✅ Thương hiệu (v40):** gắn 3 ảnh do user cung cấp vào `frontend/public/`: `logomt.png` (logo
  trang login), `icon.png` (icon sidebar góc trên-trái, thay ô chữ "M" cũ), `favicon.png` (tab
  trình duyệt, thay `favicon.svg`). Lưu ý: 2 file đầu user gửi ban đầu không có kênh alpha (PNG
  color type 2 = truecolor không trong suốt) dù trông "nền trong suốt" trên máy họ — đã phát hiện
  bằng cách tự viết decoder PNG (Node, không cần lib ngoài) đọc IHDR + giải nén IDAT, KHÔNG tự động
  tách nền (rủi ro răng cưa/mất chi tiết) mà để user xuất lại file đúng alpha. Trang login cũng bỏ
  chữ "MathTutor"/mô tả dài, logo phóng to (48→72, tỉ lệ so gốc x4.5), đổi layout từ canh giữa tuyệt
  đối (`items-center`) sang canh từ trên (`items-start pt-12`) vì logo lớn đẩy khối nội dung sát
  đáy màn hình.
- **✅ Fix khung Sửa/Tạo câu hỏi tự đóng khi lỡ bấm ra ngoài (v40):** `KhungModal` có `onClick`
  đóng modal gắn trên lớp overlay nền — bấm nhầm ngoài khung là mất dữ liệu đang sửa. Đã gỡ, giờ
  chỉ đóng qua nút X / Lưu / Hủy.
- **✅ Đồ thị/BBT vẽ lại theo style SGK Việt Nam, đen trắng thuần (v38 + v39):** sau khi so sánh
  với ảnh SGK thật, nhận thấy hình CAS vẽ đúng nhưng chưa quen mắt HS. Đã quyết định KHÔNG dùng
  TikZ/LaTeX (phân tích chi phí hạ tầng — cần cài LaTeX engine + sandbox riêng, không đáng so với
  giá trị) — vẫn dùng SVG thuần, chỉ sửa lớp vẽ (`VeDoThiDialog.jsx`/`VeBBTDialog.jsx`), **không
  đụng `ve_hinh.py`** (CAS/dữ liệu không đổi) trong suốt cả quá trình tinh chỉnh.
  - **v38 — bản vẽ lại đầu tiên:** đồ thị bỏ lưới đầy + khung bao ngoài, thêm trục Ox/Oy có mũi
    tên (SVG `<marker>`) + nhãn "O", đường nét đứt chiếu cực trị xuống Ox/sang Oy. BBT: khung bảng
    thật (viền ngoài + kẻ dọc từng cột), đường nối hàng y có mũi tên. Toàn bộ đen/trắng thuần.
  - **v39 — tinh chỉnh qua nhiều vòng test thực tế của user (nhiều lỗi hiển thị chỉ lộ ra khi xem
    ảnh chụp màn hình thật, không phát hiện được qua truy vết tọa độ tay):**
    - BBT: điểm gián đoạn (hàm không xác định) đổi từ 1 nét đứt che số → **2 nét dọc song song**
      thật (đúng quy ước SGK), số trái/phải dịch ra 2 bên (không đè lên nét); mũi tên rút ngắn
      (GAP=5) để không chạm 2 nét song song; bỏ hết nét đơn dư thừa ở mốc cực trị (cả hàng x lẫn
      y') — chỉ giữ lại đường ngăn cột nhãn "x"/"y'"/"y" theo yêu cầu; cỡ chữ/số +1 (13→14), dấu
      +/− to hẳn (15→19).
    - Đồ thị: nhãn "x"/"y"/"O" từng bị đường cong vẽ đè (do vẽ TRƯỚC đường cong trong thứ tự SVG)
      → dời ra vẽ **sau cùng** + thêm **viền trắng (halo)** quanh mọi chữ/số (`paint-order:stroke`
      + viền trắng 3px) — kỹ thuật chuẩn để chữ luôn đọc rõ dù đường vẽ đi ngang qua bên dưới.
  - ⚠️ Việc CAS toán học được test tự động đầy đủ (`pytest`), nhưng phần TRÌNH BÀY (bố cục, va
    chạm chữ/nét) chỉ phát hiện được qua ảnh chụp màn hình user gửi — môi trường này không có
    Playwright/rsvg để tự render-kiểm-tra hình ảnh trước khi báo cáo.
- **🔧 Hoàn thiện sau GĐ3B (v37, đã push):**
  1. **GV list thiếu `hinh_anh`:** endpoint `danh_sach_bai` (vai GV) dùng dict riêng, không qua
     `_problem_full` như màn sửa → thiếu trường `hinh_anh`. Đã thêm; frontend hiện icon 🖼️ cạnh
     tên chuyên đề trong bảng câu hỏi để GV biết ngay câu nào đã có ảnh.
  2. **Test khóa hành vi:** sửa câu hỏi mà KHÔNG gửi `hinh_anh` (vd chỉ đổi độ khó) phải GIỮ
     NGUYÊN ảnh cũ (khác gửi `null` = gỡ ảnh) — logic đã đúng từ trước nhưng chưa có test chốt.
  3. `docs/DATA_MODEL.md` cập nhật cột `hinh_anh` + `meta.hinh_spec` cho khớp code.
  - Đã rà soát `monitor.py`/`nhiem_vu_service.py` (list HS/cờ/nhiệm vụ) — CHỦ Ý không thêm ảnh vào
    đó vì đây là màn danh sách/dashboard tổng quan (monitor còn không hiện `de_bai`), không phải
    màn "làm bài" — nằm ngoài phạm vi yêu cầu ban đầu (chỉ áp dụng `PhongHoc.jsx`).
- **✅ Ảnh minh họa câu hỏi — GĐ1 (v33) + GĐ2 (v34) HOÀN THÀNH:** mỗi câu tối đa 1 ảnh
  (`problems.hinh_anh`).
  - **GĐ1 (v33):** module `app/core/uploads.py` (validate magic bytes PNG/JPG/WebP ≤ 3MB), endpoint
    `POST /api/problems/upload-hinh` (GV/Admin), mount `/uploads` (StaticFiles); `hinh_anh` qua
    `_problem_full`/`_strip_answers`/`ChiTietPhienResponse` (HS xem, không lộ đáp án). Frontend: ô
    upload + **dán clipboard Ctrl+V** ở form GV (`ThanCauHoiForm`), HS xem **2 cột** khi có ảnh
    (`PhongHoc`, bấm phóng to), proxy Vite `/uploads`. Đã `ALTER TABLE problems ADD COLUMN hinh_anh`.
  - **GĐ2 (v34):** import hàng loạt có ảnh (`ImportCauHoiDialog`): cột **"Hình" = tên file** trong
    mẫu Excel; GV **upload nhiều ảnh** trước → map `{tên file → URL}`; parser đọc `hinh_ten`, preview
    có cột Hình (✓ khớp / ⚠ chưa upload), khi xác nhận khớp tên→URL rồi gửi `hinh_anh`. Backend
    `ImportCauHoiItem.hinh_anh` + `import_batch` gán ảnh.
- **✅ GĐ3A — Vẽ đồ thị từ hàm số (CAS, v35):** GV chỉ nhập f(x) — KHÔNG dùng LLM.
  - `app/core/ve_hinh.py`: `phan_tich_ham_so()` (TXĐ, tiệm cận đứng/ngang/xiên, cực trị, khoảng
    dấu f′ — dùng SymPy `solveset`/`limit`/`diff`, JSON-safe, chuẩn bị sẵn cho GĐ3B bảng biến
    thiên) + `du_lieu_do_thi()` (lấy điểm mẫu, TÁCH đoạn tại tiệm cận đứng, khung y ưu tiên
    cực trị/tiệm cận thay vì điểm mẫu thô — tránh khung "nổ" theo điểm sát tiệm cận).
    Phạm vi: hàm hữu tỉ 1 biến x bậc ≤4 (đúng khảo sát hàm số lớp 12); ngoài phạm vi (căn/log/
    lượng giác/tham số) → lỗi rõ ràng, gợi ý chuyển sang upload ảnh.
  - Endpoint `POST /api/problems/ve-do-thi` (GV/Admin, không lưu DB — chỉ xem trước).
  - `app/core/matching/cas.py` thêm `parse_bieu_thuc_an_toan()` (public wrapper của
    `_parse_an_toan`) để `ve_hinh.py` tái dùng cơ chế parse an toàn có sẵn.
  - Frontend `VeDoThiDialog.jsx`: GV nhập f(x) (+ x_min/x_max tùy chọn) → SVG (trục, lưới, tiệm
    cận nét đứt, cực trị đánh dấu) → "Dùng hình này" chuyển SVG→canvas→PNG→upload qua
    `/upload-hinh` có sẵn (tái dùng nguyên vẹn hạ tầng GĐ1). Spec (hàm + cửa sổ) lưu vào
    `meta.hinh_spec` (KHÔNG đổi schema — `meta` vốn là JSON tự do) để "Vẽ lại" mở ra sửa tiếp.
  - ⚠️ Bug đã sửa lúc code: `Symbol("x", real=True)` ≠ `Symbol("x")` mà `sympify()` tạo ra (SymPy
    coi 2 symbol khác nhau dù cùng tên) → mọi hàm hợp lệ bị báo nhầm "chứa tham số". Sửa bỏ
    `real=True` để khớp đúng loại symbol parser thực sự tạo ra.
- **✅ GĐ3B — Vẽ bảng biến thiên từ hàm số (CAS, v36):** cùng ý tưởng GĐ3A — GV chỉ nhập f(x).
  - `phan_tich_ham_so()` (GĐ3A) mở rộng thêm `gia_tri_bien`: giá trị hàm tại 2 đầu ±∞ và tại từng
    mốc — mốc là cực trị → 1 giá trị đúng tại đó; mốc là điểm gián đoạn (tiệm cận đứng) → giới hạn
    TRÁI/PHẢI tách riêng (`limit(expr, X, x0, "-"/"+" )`) vì hàm không xác định đúng tại đó.
  - Endpoint `POST /api/problems/ve-bbt` (GV/Admin) — gọi thẳng `phan_tich_ham_so()`, KHÔNG lấy
    điểm mẫu (khác `/ve-do-thi`) vì bảng biến thiên không cần sampling.
  - Frontend `VeBBTDialog.jsx`: dựng SVG bảng 3 hàng (x / y′ / y) kiểu SGK — cột cách đều (KHÔNG
    scale theo giá trị x thực, khác đồ thị). Thuật toán `xepMuc()`: mỗi mốc được xếp mức "trên"/
    "dưới" — giá trị ±∞ biết ngay; giá trị hữu hạn suy qua DẤU khoảng liền kề (hàm tăng vào 1 điểm
    → điểm đó cao hơn khoảng đó, và ngược lại). Đã đối chiếu tay 2 ca (đa thức bậc 3, phân thức có
    tiệm cận đứng) — mọi đoạn nối khớp 100% với hướng mũi tên dấu y′. Điểm gián đoạn: 2 giá trị
    trái/phải KHÔNG nối với nhau (vạch đứt nét), đúng quy ước SGK.
  - `frontend/src/utils/svgSangPng.js`: tách hàm SVG→canvas→PNG dùng chung cho cả 2 dialog
    (trước đó trùng lặp trong `VeDoThiDialog.jsx`).
  - ⚠️ **Chưa tự kiểm chứng bằng trình duyệt thật** (như GĐ3A) — luồng SVG→canvas→PNG mới qua
    compile-check + test toán CAS, CHƯA xác nhận bằng mắt trong trình duyệt.
- ⚠️ Bài học tái diễn: uvicorn `--reload` trên Windows để lại tiến trình con `multiprocessing.spawn`
  giữ port khi kill parent → phải kill cả tiến trình con; và đổi `vite.config.js` phải RESTART Vite.
- **Thay đổi trong v32 (đã push):**
  1. **Tên chuyên đề luôn LIVE:** API `problems.py` + `sessions.py` suy tên chuyên đề qua
     `_lay_dang_cd_map(db)` (raw SQL JOIN `dang→chuyen_de`) thay vì đọc cột denormalized
     `problems.chuyen_de`. Cộng cascade trong `danh_muc_service.sua_chuyen_de` (đổi tên chuyên đề →
     UPDATE cột text ở mọi câu hỏi). Đã đồng bộ toàn bộ dữ liệu `dev.db` cho khớp.
     ⚠️ Bug gốc từng gặp: **backend chạy KHÔNG `--reload`** nên các bản sửa không có hiệu lực → giờ
     luôn chạy uvicorn `--reload` ở chế độ dev.
  2. **Streak (`chuoi_ngay_service`) fix múi giờ:** `hom_nay` tính theo `datetime.now(timezone.utc)`
     cho khớp `cap_nhat_luc` (UTC); trước dùng `date.today()` (giờ địa phương) → streak sai vào
     rạng sáng.
- 2 lõi `core/matching` (CAS + bậc thang) và `core/orchestrator` (máy trạng thái) KHÔNG phụ thuộc
  LLM/web — đúng nguyên tắc bất biến CLAUDE.md.
- Đủ 3 vai trò (admin/gv/hs), 3 loại câu (TN4PA/TNDS/TLN), phân cấp Chuyên đề → Dạng.
- Versioning: tag `v1`…`v51` trên GitHub (`github.com/tuananhpvd/mathtutor`). "Đưa lên github" =
  commit + push + tạo tag phiên bản kế tiếp (kế: **v52**); tác giả Tuan Anh, KHÔNG thêm Co-Authored-By.

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
Tài khoản seed: `admin/admin123`, `gv1/gv123`, `hs1/hs123`.
Build-test trước khi commit: backend `ruff check app/` + `pytest`; frontend `npm run build`.

> DB: `create_all()` KHÔNG ALTER bảng cũ — đã có migration nhẹ `init_db._migrate_them_cot` (thêm
> cột `problems.tao_luc`, `sessions.thoi_gian_hoat_dong_giay`, `phan_tich_hs.nguon`,
> `problems.pham_vi`). Đổi model lớn → cân nhắc xoá `backend/dev.db` rồi chạy lại để seed schema mới.

## 6. Đồng hành GV↔HS (A1–B1, C1) — triển khai tháng 2026-06

| Phase | Mô tả | Trạng thái |
|---|---|---|
| A1 | Thông báo (chuông) + GV nhận xét HS (AI gợi ý nhận xét sẵn) | ✅ Done |
| A2 | HS nhờ thầy/cô trong bài, GV trả lời inline | ✅ Done |
| A3 | GV giao nhiệm vụ/bài tập theo lớp/từng HS/theo điểm yếu | ✅ Done |
| A4 | Khép vòng cờ: GV xử lý cờ kèm nhắn HS (trung tính/minh bạch) | ✅ Done |
| B1 | Mục tiêu học tập: HS tự đặt / GV đặt / hệ thống gợi ý theo điểm yếu | ✅ Done |
| C1 | Chuỗi ngày học (streak) + 8 cột mốc nhẹ (bài/chuỗi ngày) | ✅ Done |

## 7. Việc tiếp theo gợi ý

- [ ] Đưa lên GitHub (commit + push + tag v32) khi muốn.
- [ ] (Khi chạy thật/dự thi) thực hiện checklist mục 2.
- [ ] Rà DoD toàn sản phẩm theo `docs/PLAN.md`.
