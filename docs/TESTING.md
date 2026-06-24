# TESTING.md — Chiến lược & ca test bắt buộc (v3)

Hai lõi tự viết (matching, orchestrator) và lớp guard phải có test mạnh. LLM không assert nội
dung sinh ra, chỉ test luồng và xử lý lỗi. Mỗi phase TỰ build-test-fix đến xanh (CLAUDE.md mục 2).

Công cụ: `pytest`. DB test SQLite in-memory. LLM test `StubLLMClient`. Không gọi mạng.

## Cấu hình vòng lặp tự động (Claude tự chạy)

Sau mỗi thay đổi code:
1. `ruff check .` (sửa lỗi lint) → `python -c "import app.main"` (import smoke).
2. `pytest -q`.
3. Frontend (nếu có đụng): `cd frontend && npm run build`.
4. Còn lỗi → đọc log, sửa, lặp (tối đa 5 vòng cùng nguyên nhân rồi báo).
5. Báo cáo: build OK?, test X passed/Y failed, lỗi đã gặp, cách xử lý, DoD.

## Phase 0 — auth/phân quyền
`tests/test_auth.py`: login đúng/sai mật khẩu; JWT chứa vai trò; `require_role` chặn sai vai trò
(403); 3 tài khoản seed đăng nhập được.

## Phase 1 — core/matching (BẮT BUỘC)
`test_cas.py`: `x^2-1`=`-1+x^2`=`(x-1)(x+1)` → DUNG; `1/2`=`0.5`=`2/4` → DUNG; `pi/6` ok;
`che_do=dung_dang` phân biệt `(x-1)(x+1)` vs `x^2-1`; cú pháp hỏng → KHONG_PHAN_TICH_DUOC;
input nguy hiểm (`__import__`) bị chặn; `2`≠`3` → SAI.
`test_latex.py`: `\frac{x^2-1}{2}` → `(x**2-1)/2`; `\sqrt{2}` → `sqrt(2)`; LaTeX hỏng báo lỗi rõ.
`test_scoring.py`: bậc thang 0→0.0,1→0.1,2→0.25,3→0.5,4→1.0.
`test_matcher.py`: TN4PA đúng/sai; TNDS bài 10.3 [Dung,Dung,Dung,Sai]→4 ý đúng,1.0;
[Dung,Sai,Dung,Sai]→3 ý,0.5; TLN bài 10.1 `20`/`20.0` đúng, `19` sai, `hai mươi`→KHONG_PHAN_TICH_DUOC.
Smoke kiến trúc: `import app.core.matching` không kéo fastapi/llm/db.

## Phase 2 — core/orchestrator (BẮT BUỘC)
`test_orchestrator.py` (bài TLN): chỉ thị đầu có y_dinh định hướng, cap_goi_y=0, không lộ đáp án;
HS đúng bước 1 → sang bước 2 (xac_nhan_dung); HS sai → hoi_nguoc, so_lan_sai tăng, không sang bước;
xin gợi ý tới hết danh sách của bước → cap_goi_y tăng dần, y_goi_y lấy đúng phần tử
danh_sach_goi_y[cap_goi_y], cap_goi_y dừng nâng khi đạt len(danh_sach_goi_y), gợi ý cuối KHÔNG
chứa bieu_thuc_ket_qua; với bài tb là 3 gợi ý, kiểm thêm 1 bước cấu hình 2 và 4 gợi ý dừng đúng;
mọi ChiThi có rang_buoc. Smoke: `import app.core.orchestrator` không kéo llm.

## Phase 3 — orchestrator 3 loại
`test_orchestrator_tnds.py`: dẫn lần lượt a→d; trước khi HS kết luận 1 ý, chỉ thị KHÔNG lộ
đúng/sai ý; sau 4 ý tổng hợp điểm bậc thang khớp scoring; y_hien_tai chuyển đúng thứ tự.
`test_orchestrator_tn4pa.py`: không chỉ thị nào gợi chọn thẳng phương án; chọn bừa → yêu cầu loại trừ.

## Phase 4 — guard (BẮT BUỘC, bộ ca bẫy)
`test_answer_guard.py`: stub trả câu CHỨA đáp án từng loại (TLN chứa "20"; TN4PA "đáp án là B";
TNDS "ý d sai") → chốt kích hoạt; câu gợi mở hợp lệ KHÔNG bị chặn; `2*10` khi đáp án `20` cũng bị
phát hiện qua CAS; Turn ghi co_bi_chot_chan=True khi chốt.
`test_scope.py`: câu lạc đề → kéo về bài. `test_safety.py`: dấu hiệu khó khăn tâm lý → thông điệp
hỗ trợ, không dẫn toán; nội dung không phù hợp bị lọc. `test_flag.py`: nhiều "không hiểu" → cờ
khong_hieu_nhieu; chốt nhiều lần → cờ chot_chan_nhieu.

## Phase 5 — AI sinh câu hỏi
`test_question_gen.py`: stub trả JSON mẫu hợp lệ 3 loại → nạp được; câu chưa duyệt KHÔNG xuất hiện
trong GET /api/problems của HS; bieu_thuc_ket_qua không parse được → đánh dấu cần sửa;
số gợi ý theo độ khó: câu `de` sinh 2 gợi ý, `tb` 3, `kho` 4 (theo bảng cấu hình); mọi phần tử
`danh_sach_goi_y` KHÔNG chứa `bieu_thuc_ket_qua`/`dap_an_cuoi` (ràng buộc gợi ý không lộ đáp án).

## Phase 6 — tiến độ + làm tiếp
`test_progress.py`: xong bài cập nhật progress đúng. `test_resume.py`: phiên dang_lam khôi phục
đúng buoc_hien_tai/y_hien_tai/bộ đếm.

## Tích hợp API (chạy từ Phase 2, mở rộng dần)
`test_api_flow.py` (TestClient + Stub + JWT): HS login → tạo phiên TLN → message vài lượt →
answer → kết quả đúng; phiên TNDS → 4 ý → answer kèm bậc thang; GET /problems/{id} KHÔNG chứa
trường đáp án; endpoint admin chặn vai trò hs/gv.

## Quy ước
- Mỗi phase xanh test trước commit. Seed cố định cho phần ngẫu nhiên (tái lập).
- Một test "smoke phụ thuộc": dùng importlib xác nhận 2 lõi không import llm/web.
- Frontend tối thiểu: `npm run build` phải pass ở các phase đụng frontend.
