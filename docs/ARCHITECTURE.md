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

## 4. Cây thư mục đích (D:\claude\mathtutor)

```
mathtutor/
├── CLAUDE.md
├── README.md
├── docs/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example          (DATABASE_URL, LLM_*, JWT_SECRET)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth/
│   │   │   ├── security.py    (hash mật khẩu, JWT)
│   │   │   └── deps.py        (require_role: admin/gv/hs)
│   │   ├── core/
│   │   │   ├── matching/ { cas.py, latex.py, scoring.py, matcher.py }
│   │   │   ├── orchestrator/ { state.py, rules.py, directive.py }
│   │   │   └── guard/ { scope.py, safety.py, answer_guard.py }
│   │   ├── llm/ { client.py, prompts.py, question_gen.py }
│   │   ├── models/ { user.py, lop.py, problem.py, solution_step.py,
│   │   │             session.py, turn.py, flag.py, progress.py }
│   │   ├── db/ { base.py, session.py, repositories/ }
│   │   ├── schemas/          (Pydantic)
│   │   ├── services/ { auth_service, tutor_service, session_service,
│   │   │               question_gen_service, progress_service, monitor_service }
│   │   ├── api/ { auth, problems, sessions, tutor, questions_ai,
│   │   │          students, progress, monitor, admin }
│   │   └── data/seed/ { problems.json, users.json }
│   └── tests/ { test_cas.py, test_latex.py, test_scoring.py, test_matcher.py,
│                test_orchestrator.py, test_orchestrator_tnds.py, test_answer_guard.py,
│                test_scope.py, test_safety.py, test_flag.py, test_auth.py, test_api_flow.py }
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx, api.js, auth.js
        ├── components/ { Formula.jsx, FormulaEditor.jsx (MathLive), ChatPanel.jsx,
        │                 AnswerInputTN4PA.jsx, AnswerInputTNDS.jsx, AnswerInputTLN.jsx,
        │                 ProgressChart.jsx, RoleLayout.jsx }
        ├── pages/
        │   ├── auth/ { Login.jsx }
        │   ├── hs/ { TrangChu.jsx, ChonBai.jsx, PhongHoc.jsx, KetThuc.jsx, TienDo.jsx }
        │   ├── gv/ { QuanLyCauHoi.jsx, SoanBai.jsx, AISinhCauHoi.jsx, QuanLyCo.jsx,
        │   │         QuanLyHocSinh.jsx, TheoDoiTienBo.jsx }
        │   └── admin/ { Dashboard.jsx, QuanLyTaiKhoan.jsx, CauHinh.jsx, NhatKy.jsx }
        └── styles/ (design tokens từ Phase 7)
```

## 5. Endpoint API (theo vai trò)

| Method | Path | Vai trò | Việc |
|--------|------|---------|------|
| POST | `/api/auth/login` | công khai | đăng nhập, trả JWT + vai trò |
| GET | `/api/problems` | hs/gv | danh sách bài (lọc); HS chỉ thấy đã duyệt, KHÔNG kèm đáp án |
| POST | `/api/sessions` | hs | tạo/khôi phục phiên, lời mở đầu gia sư |
| GET | `/api/sessions/dang-do` | hs | phiên đang làm dở để làm tiếp |
| POST | `/api/sessions/{id}/message` | hs | gửi lượt → phản hồi gia sư |
| POST | `/api/sessions/{id}/khong-hieu` | hs | nâng mức gợi ý |
| POST | `/api/sessions/{id}/answer` | hs | nộp đáp án theo loại (TNDS kèm bậc thang) |
| GET | `/api/progress/me` | hs | bảng tiến độ cá nhân |
| GET/POST/PUT/DELETE | `/api/questions...` | gv | quản lý câu hỏi/lời giải/gợi ý |
| POST | `/api/questions-ai/generate` | gv | AI sinh nháp câu hỏi theo mẫu |
| POST | `/api/questions-ai/{id}/duyet` | gv | duyệt/sửa/loại |
| GET | `/api/students` | gv | HS lớp mình |
| GET | `/api/progress/students` | gv | theo dõi tiến bộ HS lớp mình |
| GET | `/api/monitor/flags` | gv | hàng đợi cờ |
| GET | `/api/monitor/sessions/{id}` | gv | xem lại nhật ký |
| POST | `/api/monitor/flags/{id}/done` | gv | đánh dấu xử lý |
| GET | `/api/admin/overview` | admin | dashboard tổng |
| GET/POST | `/api/admin/users` | admin | quản lý tài khoản |
| GET/PUT | `/api/admin/config` | admin | cấu hình hệ thống |

`GET /api/problems/{id}` phải lọc bỏ mọi trường đáp án/lời giải trước khi trả cho frontend HS.
