# ARCHITECTURE.md — Kiến trúc MathTutor v3

## 1. Tổng thể

Web app 2 tầng. Frontend React (3 khu vực theo vai trò) gọi REST API FastAPI có xác thực JWT.
Backend chứa hai lõi tự viết (so khớp CAS, điều phối sư phạm), lớp guard kiểm soát, service
LLM tách rời, và phân quyền theo vai trò.

```
React (Vite + Tailwind + KaTeX + MathLive)
   │  REST/JWT
   ▼
FastAPI
   ├── auth/            (JWT, phân quyền admin/gv/hs)
   ├── core/matching    (SymPy CAS + parse_latex + bậc thang) — thuần Python
   ├── core/orchestrator(máy trạng thái dẫn dắt, kịch bản mềm) — thuần Python
   ├── core/guard       (chốt lộ đáp án, khóa phạm vi, an toàn)
   ├── llm/             (LLMClient + Stub + prompts: diễn đạt & sinh câu hỏi)
   ├── services/        (tutor, session, question_gen, progress, monitor)
   ├── api/             (routes theo vai trò)
   ├── models/ + db/    (SQLAlchemy + repository)
   ├── alembic/         (migration schema — xem mục 6)
   └── data/seed/       (bài mẫu + tài khoản 3 vai trò)
```

## 2. Phân tầng (giữ nguyên nguyên tắc)

- `core/matching`, `core/orchestrator`: thuần Python, KHÔNG import FastAPI/LLM.
- `core/guard`: chốt chặn, khóa phạm vi, lọc an toàn — thuần Python.
- `llm/`: nhận chỉ thị có cấu trúc → trả câu chữ (diễn đạt); và sinh câu hỏi theo mẫu JSON.
  Có Stub tất định.
- `auth/` + `api/`: xác thực, phân quyền, ghép luồng, đọc/ghi DB.

## 3. Luồng một lượt hội thoại (kịch bản mềm)

```
1. api nhận (session_id, nội dung, dap_an_nhap?) — đã xác thực vai trò hs
2. guard.khoa_pham_vi(nội dung)        -> lạc đề: kéo về bài, kết thúc lượt
3. guard.loc_an_toan_dau_vao(nội dung) -> vi phạm: phản hồi an toàn, kết thúc lượt
4. Nếu có dap_an_nhap:
     matching.so_khop(loai_cau, dap_an_nhap, du_lieu_chuan, che_do_so_khop) -> ket_qua
5. orchestrator.xu_ly_luot(trang_thai, ket_qua, cau_hoi_phu?) -> ChiThi (JSON)
     ChiThi gồm: y_dinh, buoc/y_dang_xet, cap_goi_y, y_goi_y (Ý CHÍNH), ngu_canh_hs, rang_buoc
6. llm.dien_dat(ChiThi)  -> van_ban  (diễn đạt TỰ NHIÊN quanh y_goi_y, bám ngu_canh_hs)
7. guard.chot_chong_lo_dap_an(van_ban, du_lieu_chuan)
     -> nếu lộ: yêu cầu LLM viết lại 1 lần; vẫn lộ -> thay bằng câu an toàn từ y_goi_y
8. guard.loc_an_toan_dau_ra(van_ban)
9. Lưu Turn; cập nhật Session (cho phép khôi phục); cập nhật Progress khi xong bài
10. flag.kiem_tra(trang_thai) -> gắn cờ nếu bất thường
11. Trả van_ban + trạng thái hiển thị (bước/ý, có cho nhập đáp án không)
```

Khác v2: bước 5–6 hỗ trợ "kịch bản mềm" — `y_goi_y` là ý chính, LLM diễn đạt tự nhiên và có
thể trả lời `cau_hoi_phu` của HS trong phạm vi bài; bước 7 (chốt chặn) vì thế quan trọng hơn.

## 4. Bố cục thư mục (vai trò từng lớp + quy ước)

Doc này mô tả *ý nghĩa* mỗi thư mục (thứ ít đổi), KHÔNG liệt kê từng file — chạy `ls` là thấy
file thật, luôn đúng. Quy ước đặt tên giúp suy ra nội dung mà không cần doc cập nhật tay.

**Backend** (`backend/app/`):

| Thư mục | Vai trò | Quy ước |
|---|---|---|
| `main.py`, `config.py` | Khởi tạo FastAPI + middleware + lifespan; đọc env | — |
| `auth/` | JWT (`security.py`), phân quyền (`deps.py::require_role`), chống dò mật khẩu (`throttle.py`) | — |
| `core/matching/` | SymPy CAS + parse LaTeX + bậc thang — **thuần Python, KHÔNG import FastAPI/LLM/DB** | `cas.py, latex.py, scoring.py, matcher.py` |
| `core/orchestrator/` | Máy trạng thái dẫn dắt (kịch bản mềm) — **thuần Python** | `state.py, rules.py, directive.py` |
| `core/guard/` | Chốt lộ đáp án (`leak.py`), khóa phạm vi (`scope.py`), lọc an toàn (`safety.py`) — **thuần Python** | — |
| `core/` (khác) | `uploads.py` (lưu ảnh), `ve_hinh.py` (CAS dựng đồ thị/BBT) | — |
| `llm/` | `LLMClient` + `StubLLMClient` + `prompts.py` + sinh câu hỏi | — |
| `models/` | SQLAlchemy models | **1 file = 1 nhóm bảng, tên file ≈ tên bảng** (`user.py`→`users`, `nhiem_vu.py`→`nhiem_vu*`) |
| `schemas/` | Pydantic request/response | 1 file theo vai trò/nghiệp vụ (`admin.py`, `gv.py`, `hs.py`, `problem.py`...) |
| `db/` | `base.py` (engine/Base), `session.py` (get_db), `init_db.py` (seed), `migrate.py` (Alembic), `types.py` (UTCDateTime) | KHÔNG có repositories/ — service gọi ORM trực tiếp |
| `services/` | Logic nghiệp vụ + truy cập DB | **1 file/nghiệp vụ**, đuôi `_service.py` (`tutor_service`, `de_thi_service`...) |
| `api/` | Routes REST, kiểm vai trò từng endpoint | **1 file/nhóm nghiệp vụ**, prefix `/api/<tên>` (`gv.py`→`/api/gv`, `tro_giup.py`→`/api/tro-giup`) |
| `data/seed/` | `problems.json`, `users.json` (dữ liệu mẫu) | — |
| `alembic/` | Migration schema (xem mục 6) | — |

**Frontend** (`frontend/src/`):

| Thư mục | Vai trò | Quy ước |
|---|---|---|
| `main.jsx`, `api.js`, `auth.js` | Entry + Sentry; client API; session (sessionStorage) | — |
| `pages/{auth,hs,gv,admin}/` | Trang theo vai trò; mỗi vai trò có 1 `*App.jsx` (shell + nav hash) | code-split lazy theo trang |
| `components/` | Component dùng chung; `ui/` = primitive (Button, Card, Input...); `answer/` = ô nhập đáp án 3 loại | — |
| `e2e/` | Spec Playwright 3 luồng vàng (xem `docs/TESTING.md`) | — |

## 5. Endpoint API

Toàn bộ endpoint (154 route, đủ method/path/schema request-response) được **FastAPI tự sinh**
và LUÔN khớp code — xem tại `/docs` (Swagger UI) hoặc `/openapi.json` khi chạy backend. KHÔNG
liệt kê tay ở đây để tránh lỗi thời (bài học: bảng endpoint cũ từng dẫn sai ~90% sau 40 phiên).

Router tổ chức theo prefix vai trò/nghiệp vụ: `/api/auth`, `/api/hs`, `/api/gv`, `/api/admin`,
`/api/problems`, `/api/sessions`, `/api/questions-ai`, `/api/monitor`, `/api/progress`,
`/api/nhiem-vu`, `/api/muc-tieu`, `/api/de-thi`, `/api/thong-bao`, `/api/tro-giup`,
`/api/danh-muc`, `/api/ly-thuyet`, `/api/gv/dat-lai`.

**Nguyên tắc bất biến (KHÔNG được vi phạm, không phụ thuộc vào việc doc có cập nhật hay không):**
- `GET /api/problems` + `/api/problems/{id}` cho HS phải lọc bỏ MỌI trường đáp án/lời giải
  (`dap_an_dung`, `dap_an` ý, `dap_an_cuoi`, `bieu_thuc_ket_qua`) trước khi trả.
- Mỗi endpoint kiểm vai trò (`require_role`); HS không thấy đáp án/quản trị; GV chỉ thấy lớp
  mình; chỉ Admin quản trị hệ thống.

## 6. Migration schema — Alembic (từ v121)

DB không còn dùng `Base.metadata.create_all()` + ALTER TABLE thủ công. Toàn bộ thay đổi schema
đi qua **Alembic** (`backend/alembic/`, script trong `alembic/versions/`):

- App tự chạy `alembic upgrade head` lúc khởi động qua `app/db/migrate.py::chay_migration()`
  (gọi từ `init_db()` trong `lifespan`).
- CSDL đã có bảng `users` nhưng chưa có `alembic_version` (production cũ trước khi có Alembic,
  hoặc `dev.db` có sẵn dữ liệu) → tự **stamp** vào baseline thay vì chạy lại DDL tạo bảng.
- Quy trình đổi schema: sửa model → `alembic revision --autogenerate -m "..."` → review kỹ
  file sinh ra (đặc biệt FK vòng tròn, kiểu cột tùy biến) → test `upgrade`/`downgrade` trên
  bản sao dữ liệu thật. Chi tiết đầy đủ ở `docs/PROGRESS.md` mục 5.
