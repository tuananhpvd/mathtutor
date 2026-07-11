# REVIEW.md — Rà soát toàn diện dự án MathTutor

> Thực hiện theo yêu cầu review 5 bước. Ngày rà soát: 2026-07-10 (sau tag **v87**).
>
> **✅ CẬP NHẬT 2026-07-11 — ĐÃ SỬA XONG TOÀN BỘ**, trừ 2 mục chủ động chấp nhận rủi ro
> (đã trao đổi và được xác nhận): lỗ hổng `xlsx` (#4 phần frontend — không có bản vá chính
> thức) và bundle chưa code-split (🟢 #6 — cảnh báo hiệu năng, không phải lỗi). Chi tiết
> trạng thái từng mục đánh dấu ngay dưới tiêu đề. Kiểm chứng cuối: backend **421/421 test
> pass**, `ruff` 0 lỗi, `pip-audit` 0 lỗ hổng; frontend **eslint 0 lỗi**, `npm run build`
> thành công; đăng nhập + gọi API qua token thực tế trên dev server đã xác nhận hoạt động
> đúng sau khi đổi thư viện JWT.

---

## BƯỚC 1 — Hiểu dự án

**MathTutor**: gia sư Toán lớp 12 theo phương pháp Socratic (dẫn dắt học sinh tự tìm đáp án
bằng câu hỏi gợi mở, không đưa lời giải trực tiếp). 3 loại câu hỏi (TN4PA trắc nghiệm ABCD,
TNDS đúng/sai 4 ý, TLN trả lời ngắn), editor công thức LaTeX, phân quyền 3 vai trò
(Admin/GV/HS), AI hỗ trợ soạn câu hỏi cho GV duyệt.

**Công nghệ:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, SymPy (+ antlr4 cho parse LaTeX), JWT
  (PyJWT — đổi từ python-jose lúc xử lý báo cáo này, xem 🟡 #4), pytest. CSDL: PostgreSQL
  (production) / SQLite (dev, `dev.db`).
- Frontend: React 19 + Vite, TailwindCSS v4, KaTeX (hiển thị công thức), MathLive (nhập công
  thức), xlsx (import Excel). Không dùng TypeScript (JSX thuần).
- LLM: Gemini (khuyến nghị) / Anthropic / OpenAI, qua interface `LLMClient` chung, có
  `StubLLMClient` tất định cho test.

**Module chính (backend `app/`):** `api/` (17 router REST), `auth/` (JWT + throttle chống
brute-force), `core/matching/` (CAS chấm đáp án — thuần, không phụ thuộc LLM/web),
`core/orchestrator/` (máy trạng thái hội thoại — thuần), `core/guard/` (lọc an toàn + chốt
chặn rò rỉ đáp án), `llm/` (client + prompt tập trung), `models/`+`schemas/`+`services/`
(ORM, validate, business logic), `db/` (session + migration nhẹ tự động).

**Quy mô:** ~11.6k dòng Python (backend `app/`), ~14k dòng JS/JSX (frontend `src/`), 421 test
backend (`pytest`).

---

## BƯỚC 2 & 3 — Kết quả kiểm tra tĩnh + chạy thử thực tế (tóm tắt)

| Hạng mục | Kết quả lúc rà soát (2026-07-10) | Sau khi sửa (2026-07-11) |
|---|---|---|
| `ruff check app/` (E/F/I) | ✅ 0 lỗi | ✅ 0 lỗi (kể cả mở rộng B/C4/SIM) |
| `ruff check tests/` | 4 lỗi (style) | ✅ 0 lỗi |
| Import smoke `python -c "import app.main"` | ✅ OK | ✅ OK |
| `pytest` (421 test) | ✅ 421 passed | ✅ 421 passed |
| `npm run build` (frontend, Vite) | ✅ OK (cảnh báo chunk lớn) | ✅ OK (cảnh báo chunk lớn — giữ nguyên có chủ đích) |
| `npx eslint .` (frontend, toàn bộ) | 20 lỗi | ✅ **0 lỗi** |
| Dev server backend (`:8000`) | ✅ Sạch | ✅ Sạch + xác nhận login/token thật hoạt động sau đổi PyJWT |
| Dev server frontend (`:5173`) | ✅ HTTP 200 | ✅ HTTP 200 |
| `pip-audit` | 2 lỗ hổng | ✅ **0 lỗ hổng** |
| `npm audit` | 1 lỗi (high) | 1 lỗi (`xlsx`, chấp nhận rủi ro) |

---

## BƯỚC 4 — Bảo mật & cấu hình

| Hạng mục | Kết quả |
|---|---|
| API key/secret/password hardcode trong source | ✅ Không có |
| `.env` có bị commit nhầm | ✅ Không (gitignore đúng, chỉ có `.env.example` với placeholder giả) |
| `.gitignore` | ✅ Đầy đủ (`.env`, `*.db`, `node_modules/`, `dist/`, log dev server, `uploads/`...) |
| Fail-fast JWT_SECRET mặc định trên CSDL production | ✅ Đã có (`kiem_tra_an_toan_khoi_dong()`, chặn khi `DATABASE_URL` chứa "postgres" mà secret vẫn là giá trị mẫu) |
| `pip-audit` (backend) | ✅ ĐÃ SỬA — 2 lỗi (`ecdsa`, `pip`) → 0 lỗi, xem 🟡 #4 |
| `npm audit` (frontend) | ⏭ 1 lỗi mức **high** (`xlsx`) — chấp nhận rủi ro, xem 🟡 #4 |

---

## BƯỚC 5 — Danh sách vấn đề

### 🔴 Critical (chắc chắn gây lỗi/crash)

**Không tìm thấy vấn đề nào ở mức Critical.** Đã rà: cú pháp (ruff/eslint parse toàn bộ file
thành công), import thừa/thiếu, `except:` trần, chia cho 0 ở các chỗ tính trung bình/tỉ lệ,
build, toàn bộ test suite, khởi động thực tế 2 server — không phát hiện lỗi chắc chắn gây crash
tại thời điểm rà soát này.

---

### 🟡 Warning (có khả năng gây lỗi hoặc code xấu)

**1. ✅ ĐÃ SỬA — `frontend/src/components/FormulaEditor.jsx`** — thiếu `.catch()` khi
   `import('mathlive')` thất bại. Đã thêm `.catch()` + state `loiTai` hiển thị thông báo lỗi
   kèm nút "Thử lại" (gọi lại `import()` qua counter `thuLai`), thay vì đứng im vô thời hạn.

**2. ✅ ĐÃ SỬA — `frontend/src/pages/admin/CauHinh.jsx`** — thiếu `.catch()` khi tải cấu hình.
   Đã thêm `.catch((e) => setError(e.message))`; khi `!cfg && error` hiển thị thông báo lỗi +
   nút "Thử lại" gọi lại `nap()`, thay vì kẹt vĩnh viễn ở "Đang tải cấu hình...".

**3. ✅ ĐÃ SỬA — `frontend/src/components/MixedChatInput.jsx`** — `valueRef.current = value`
   đã chuyển vào `useEffect(() => { valueRef.current = value }, [value])` thay vì gán trực
   tiếp trong thân render.

**4. Dependency có lỗ hổng bảo mật đã biết:**
   - **`xlsx` (frontend, mức HIGH)** — ⏭ **CHẤP NHẬN RỦI RO** (theo xác nhận của bạn) —
     không có bản vá qua npm (SheetJS ngừng phát hành lên registry công khai); phạm vi thực tế
     hẹp (chỉ GV/Admin tự tải file của mình, có preview trước khi import). Không đổi thư viện.
   - **`ecdsa` (backend, transitive qua `python-jose`)** — ✅ **ĐÃ SỬA**: đổi toàn bộ JWT từ
     `python-jose` sang `PyJWT` (API tương thích gần như 1:1 — `security.py`: `from jose import
     jwt` → `import jwt`; `deps.py`: `from jose import JWTError` → `from jwt import PyJWTError
     as JWTError`). Gỡ `python-jose`/`ecdsa`/`rsa`/`pyasn1` khỏi venv, cập nhật
     `pyproject.toml`. `pip-audit` giờ **0 lỗ hổng**. Xác nhận bằng test thật: đăng nhập +
     gọi API có token qua dev server sau khi đổi thư viện vẫn hoạt động đúng. Phát hiện thêm
     lúc sửa: PyJWT cảnh báo `InsecureKeyLengthWarning` cho `JWT_SECRET` mẫu quá ngắn (<32 ký
     tự, khuyến nghị RFC 7518 §3.2) mà `python-jose` cũ không cảnh báo — đã kéo dài secret mẫu
     trong `config.py`/`.env.example`, giữ cả giá trị ngắn cũ trong danh sách "không an toàn"
     để không phá cơ chế fail-fast production hiện có.

**5. ✅ ĐÃ SỬA — `ruff` B904 (78 chỗ)** — toàn bộ `except ... as e: raise ... ` trong
   `app/api/*.py`, `app/services/*.py`, `app/llm/client.py`, `app/auth/deps.py` giờ đều có
   `from e` (hoặc `as e`/`from e` được thêm mới nếu trước đó không bắt biến). 64/78 áp dụng
   bằng script tự động (đã soát diff từng dòng qua `git diff` trước khi tin), 14 chỗ còn lại
   (raise nhiều dòng, hoặc `except` không có sẵn `as e`) sửa tay. `ruff --select B904` giờ
   **0 lỗi** trên `app/`.

**6. ✅ ĐÃ SỬA — Trùng logic validate `kiemTraDapAnTLN`** giữa `QuanLyCauHoi.jsx` và
   `ImportCauHoiDialog.jsx`. Gom về `frontend/src/utils/cauHoi.js` (kèm `dungDangOptions`,
   `chuanHoaSteps` — cũng từng bị trộn export component/hàm gây lỗi react-refresh, xem 🟢 #2).
   Cả 3 nơi dùng (`QuanLyCauHoi.jsx`, `AISinhCauHoi.jsx`, `ImportCauHoiDialog.jsx`) giờ import
   từ 1 nguồn duy nhất.

---

### 🟢 Minor (style, tối ưu, không ảnh hưởng chức năng)

1. **✅ ĐÃ SỬA — `react-hooks/set-state-in-effect`** — 6 file (`BanDoNangLuc.jsx`,
   `XemLaiBai.jsx`, `HoTroHocSinh.jsx`, `QuanLyCauHoi.jsx`, `QuanLyDanhMuc.jsx`, `ChonBai.jsx`)
   giờ đều đưa `setState` vào callback bất đồng bộ (`setTimeout(..., 0)`, khớp pattern đã dùng
   sẵn trong code mới của phiên trước) thay vì gọi đồng bộ đầu `useEffect`.

2. **✅ ĐÃ SỬA — `react-refresh/only-export-components`** — `QuanLyCauHoi.jsx` hết mixed-export
   nhờ chuyển 3 hàm (`kiemTraDapAnTLN`, `dungDangOptions`, `chuanHoaSteps`) sang
   `utils/cauHoi.js` (xem 🟡 #6). `ConfirmDialog.jsx` tách `useConfirm` sang `useConfirm.js` +
   `ConfirmContext.js` riêng — `components/ui/index.js` (barrel) cập nhật đường import, **không
   phải sửa** ở 11 file đang dùng `useConfirm` vì tất cả đều import qua barrel.

3. **✅ ĐÃ SỬA — `CauHinh.jsx`** — component `KhoaApi` chuyển ra module-level (nhận `provider`
   qua prop thay vì đọc từ closure), không còn bị định nghĩa lại mỗi lần render.

4. **✅ ĐÃ SỬA — `TrangChu.jsx`** — `Date.now()` chuyển vào `useEffect` (qua state
   `bayNgayTruoc`, cũng bọc `setTimeout` để tránh dính luôn lỗi set-state-in-effect), không
   còn gọi trực tiếp trong thân render/`useMemo` (bản thân `useMemo` KHÔNG được coi là "an
   toàn" cho hàm impure theo rule mới, đã thử và vẫn bị báo lỗi).

5. **✅ ĐÃ SỬA — `ImportCauHoiDialog.jsx`** — xóa key `'khó'` trùng trong `DO_KHO_MAP`.

6. **⏭ GIỮ NGUYÊN (đã đánh giá, quyết định có chủ đích)** — Frontend bundle chưa code-split
   thêm. MathLive vốn đã tách chunk riêng qua `import()` động (801kB) sẵn từ trước. Phần
   `index.js` còn lại (~1.24MB, gzip ~365kB) gộp cả 3 ứng dụng vai trò — tách bằng
   `React.lazy()` sẽ giảm tải ban đầu nhưng cần thêm `Suspense` + kiểm thử lại cả 3 luồng
   đăng nhập, rủi ro không tương xứng với việc đây chỉ là gợi ý build của Vite, không phải lỗi.

7. **✅ ĐÃ SỬA — `app/api/routes/`** — đã xóa thư mục package rỗng.

8. **✅ ĐÃ SỬA — `ruff` style nits (10 chỗ)** — `SIM910`, `SIM114`, `C416`, `B905`
   (`zip(..., strict=True)`), `C408` × 4, `SIM105` × 2 (chuyển sang `contextlib.suppress`) đều
   đã sửa. `ruff check app/` giờ **0 lỗi** kể cả với các rule mở rộng này.

9. **✅ ĐÃ SỬA — `ruff` trong `tests/`** — `conftest.py`/`test_chuoi_ngay.py` (import sort tự
   động qua `ruff --fix`), `test_danh_muc.py` (tách 3 câu lệnh chung dòng semicolon).

10. **✅ ĐÃ SỬA — `HieuQuaPhuongPhap.jsx`** (xóa import `Badge` không dùng),
    **`QuanLyCauHoi.jsx`** (xóa hàm chết `dinhDangNgay`),
    **`ImportCauHoiDialog.jsx`** (thêm comment `eslint-disable-next-line no-unused-vars` cho
    destructure cố ý loại `dong`/`ly_do` khỏi payload).

11. **✅ ĐÃ SỬA — `pip` nâng cấp 26.1.1 → 26.1.2** (PYSEC-2026-196).

12. **⏭ GIỮ NGUYÊN (đã cân nhắc, quyết định có chủ đích)** — `tests/conftest.py` `SAWarning`
    (khóa ngoại vòng giữa `lop`/`users` lúc `drop_all()` trong test teardown). Sửa đòi hỏi thêm
    `use_alter=True` vào định nghĩa `ForeignKey` — đây là thay đổi ở tầng schema-metadata, dù
    về lý thuyết an toàn cho CSDL production hiện có (chỉ ảnh hưởng câu lệnh `create_all()`
    sinh ra cho DB MỚI, không retroactively đổi bảng đã tồn tại), nhưng lợi ích chỉ là dọn 1
    dòng cảnh báo lúc test teardown — không tương xứng với việc động vào định nghĩa khóa ngoại
    của 2 bảng lõi (`users`, `lop`) trên dự án đã có dữ liệu thật. Test vẫn chạy đúng, chỉ có
    cảnh báo.

---

## Tổng kết

| Mức | Số lượng | Trạng thái |
|---|---|---|
| 🔴 Critical | 0 | — |
| 🟡 Warning | 6 (nhóm) | 5 đã sửa, 1 chấp nhận rủi ro có chủ đích (`xlsx`) |
| 🟢 Minor | 12 (nhóm) | 10 đã sửa, 2 giữ nguyên có chủ đích (bundle size, FK-cycle warning) |

**Kiểm chứng cuối cùng (2026-07-11):**
- Backend: `ruff check app/ tests/` → 0 lỗi. `pytest` → **421/421 passed**. `pip-audit` →
  **0 lỗ hổng** (trước đó 2: `ecdsa`, `pip`).
- Frontend: `npx eslint .` (toàn bộ) → **0 lỗi** (trước đó 20). `npm run build` → thành công.
  `npm audit` → 1 lỗi (`xlsx`, chấp nhận rủi ro theo quyết định của bạn).
- Dev server thực tế: đăng nhập (`POST /api/auth/login`) + gọi API có xác thực token
  (`GET /api/admin/config`) qua PyJWT mới đều trả đúng kết quả — xác nhận thay đổi lớn nhất
  (đổi thư viện JWT) không ảnh hưởng chức năng đăng nhập/phân quyền đang chạy tốt.
- Không phát hiện quy trình/chức năng nào bị ảnh hưởng ngoài ý muốn trong suốt quá trình sửa.
