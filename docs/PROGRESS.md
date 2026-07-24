# PROGRESS.md — Trạng thái & bàn giao (cập nhật để kế thừa giữa các phiên/máy)

> File này là "trí nhớ đi theo repo" (lên GitHub). Bộ nhớ tự động của Claude Code nằm trên máy
> local, KHÔNG lên GitHub — nên mọi quyết định/trạng thái cần nhớ hãy ghi vào đây hoặc vào `docs/`.
> **Đọc cùng `CLAUDE.md` đầu mỗi phiên. Mỗi lần làm xong việc đáng kể, CẬP NHẬT file này.**

## 1. Trạng thái tổng quan (cập nhật 2026-07-24, phiên bản **v146**)

- **🔧 (v146) chore: cổng chặn PUSH tự động — chạy đủ 3 job CI (backend/frontend/e2e) cục bộ
  TRƯỚC khi cho phép `git push`, không còn dựa vào việc tự nhớ chạy.** User phản ánh: gần đây
  hay bị CI đỏ sau khi push (v139 quên `eslint`, v143 quên `e2e`) mà chỉ biết qua ảnh chụp CI
  user tự gửi — yêu cầu khắc phục TRIỆT ĐỂ, "đã đưa lên github là không còn báo lỗi".
  - **Nguyên nhân gốc**: `CLAUDE.md` mục 2 (vòng lặp build-test-fix) trước đây KHÔNG liệt kê
    `eslint` lẫn `e2e` — chỉ nói "Backend: ruff+import+pytest" và "Frontend: npm run build".
    Quy trình ghi trong tài liệu tự nó đã THIẾU so với đúng những gì CI thật kiểm tra, nên dù
    làm đúng theo tài liệu vẫn lọt lỗi — không phải lỗi "quên", mà lỗi tài liệu.
  - **Sửa**: thêm `scripts/kiem-tra-truoc-khi-push.ps1` — chạy ĐÚNG cả 3 job của `ci.yml`
    (backend: ruff+import smoke+pytest; frontend: eslint+vitest+build; **e2e: Playwright 3
    luồng vàng** — job hay bị bỏ sót nhất, cần `.venv` backend + Chromium đã cài sẵn). Gắn
    `.git/hooks/pre-push` gọi script này và **CHẶN CỨNG** `git push` nếu còn lỗi (thoát mã
    khác 0) — không phải "nhắc", mà THẬT SỰ không cho push được nếu chưa sạch. Cập nhật
    `CLAUDE.md` mục 2 (thêm eslint/vitest vào checklist) + mục 2a mới (giải thích cơ chế
    cổng chặn, quy tắc đồng bộ khi `ci.yml` đổi, cảnh báo `.git/hooks/` KHÔNG được git theo
    dõi nên mất khi clone lại — cần tạo lại hook thủ công, logic thật nằm ở script có version
    control).
  - Test: chạy `scripts/kiem-tra-truoc-khi-push.ps1` độc lập (ngoài hook) xác nhận cả 3 job
    xanh, 437s — bao gồm e2e 3/3 pass. Đây CHÍNH LÀ phép thử "trung thực" cho thay đổi này:
    không chỉ đọc lại code, mà chạy thật đúng cơ chế vừa dựng lên.

## 1a. Trạng thái trước đó (v145)

- **ui: (v145) Màn làm bài "Thi thử" (HS) — thêm nhãn "Thời gian còn lại" ngay trước đồng hồ
  đếm ngược.** `frontend/src/pages/hs/ThiThu.jsx`: chèn `<span className="text-sm text-muted">`
  trước `<span>` đồng hồ hiện có (giữ nguyên icon ⏱ + logic đổi màu khi gấp giờ ≤5 phút,
  không đổi gì khác). Test: `eslint`/`vite build` sạch. Xác minh trực quan bằng Playwright
  thật (đăng nhập HS, vào "Thi thử", bấm "Vào thi" một đề thật, chụp ảnh xác nhận nhãn hiện
  đúng vị trí, đồng hồ vẫn chạy bình thường) — bài làm thi thử tạo ra lúc test đã bị XÓA khỏi
  `dev.db` sau khi xong (không để lại `BaiThi` dở dang giả).

- **🐞 (v145) fix: CI job `e2e` đỏ sau v143 — E2E test `luong-vang.spec.js` dùng CHỈ SỐ CỨNG
  (`select nth(2)`) để chọn ô lọc "Loại câu" ở màn Chọn bài, lệch vị trí khi v143 thêm ô lọc
  "Nhiệm vụ" và đặt LÊN ĐẦU lưới lọc.** GitHub Actions báo `e2e` fail sau push v143 (`backend`
  + `frontend` xanh, chỉ `e2e` đỏ) — phát hiện qua ảnh chụp CI của user.
  - **Nguyên nhân**: lưới lọc cũ (Chuyên đề, Dạng, Loại câu, Mức độ, Trạng thái) → `nth(2)` =
    đúng "Loại câu". v143 thêm "Nhiệm vụ" và đặt đầu tiên → lưới mới (Nhiệm vụ, Chuyên đề,
    Dạng, Loại câu, Mức độ, Trạng thái) → `nth(2)` giờ trỏ nhầm sang "Dạng".
  - **Sửa**: `frontend/e2e/luong-vang.spec.js` — đổi `nth(2)` → `nth(3)`, kèm comment liệt kê
    đúng thứ tự 6 ô lọc hiện tại để tránh lệch lại lần sau.
  - Test: chạy **e2e thật** tại local (`npx playwright test`, cặp server 18000/15173 tách
    biệt hoàn toàn `dev.db`, tự dọn) — cả 3 "luồng vàng" pass, xác nhận đúng nguyên nhân +
    đúng chỗ sửa (không chỉ đoán qua ảnh CI). `eslint`/`vite build`/`vitest` 23/23 cũng sạch.

## 1b. Trạng thái trước đó (v144)

- **ui: (v144) "Hỗ trợ học sinh" (phía GV) — nút "Gửi trả lời" chuyển lên NGAY DƯỚI ô nhập,
  TRƯỚC phần "Xem trước" — áp dụng lại đúng cách sửa v143 (phía HS) sang phía GV.**
  `frontend/src/pages/gv/HoTroHocSinh.jsx`: nút "Gửi trả lời" (+ dòng lỗi validate nếu có)
  trong modal "Chi tiết yêu cầu trợ giúp" chuyển vào prop `duoiO` sẵn có của
  `MixedChatInput` — trước đó nằm sau `<MixedChatInput>` (dưới cả phần xem trước). Test:
  `eslint`/`vite build`/`vitest` 23/23 sạch — xác minh trực quan bằng Playwright thật (HS gửi
  1 yêu cầu "Nhờ thầy/cô" thật → GV đăng nhập, mở modal "Xem chi tiết" → "Trả lời", gõ nội
  dung, chụp ảnh xác nhận nút đúng vị trí) — đã dọn sạch dữ liệu test (yêu cầu, turn, thông
  báo, cờ liên quan) sau khi xong.

## 1c. Trạng thái trước đó (v143)

- **✨ (v143) feat: màn "Chọn bài" (HS) thêm bộ lọc "Nhiệm vụ" — Tất cả / Sắp hết hạn / Mới
  nhất.** Dữ liệu lấy từ `api.hsNhiemVu()` (nhiệm vụ được giao), không cần API mới.
  - **Quyết định đã hỏi & chốt với user** (2026-07-24): "Mới nhất" = CHỈ hiện bài thuộc ĐÚNG
    1 nhiệm vụ được giao gần đây nhất (theo `tao_luc` lớn nhất) — không phải sắp xếp lại toàn
    bộ danh sách. Ngưỡng "Sắp hết hạn" = ≤2 ngày còn lại, DÙNG CHUNG ngưỡng cảnh báo vàng đã
    có sẵn ở `NhiemVu.jsx` (`hanInfo()`) để nhất quán 2 màn. Nhiệm vụ ĐÃ quá hạn KHÔNG tính là
    "sắp hết hạn" (đó là trạng thái khác — đã lỡ).
  - **`frontend/src/pages/hs/ChonBai.jsx`**: thêm `api.hsNhiemVu()` vào load ban đầu (song
    song, không chặn danh sách bài nếu lỗi — cùng pattern `Promise.allSettled` sẵn có); 2
    `useMemo` tính tập `problem_id` cho từng tiêu chí; thêm `<Select>` "Nhiệm vụ" vào lưới bộ
    lọc (grid 5→6 cột); lọc kết hợp AND với 5 bộ lọc cũ (vd chọn "Sắp hết hạn" + "Chưa làm"
    cùng lúc vẫn hoạt động, không cần code riêng vì các điều kiện độc lập).
  - **Vá lỗi ESLint cùng họ** đã gặp ở v140: gọi `Date.now()` trực tiếp trong `useMemo` bị
    `react-hooks/purity` chặn — tách thành hàm module-level `soNgayConLai()` (đúng pattern
    `hanInfo()` đã dùng ở `NhiemVu.jsx`, hàm đó không bị chặn vì định nghĩa ngoài component).
  - **Sửa theo yêu cầu user sau khi xem bản đầu**: (1) chuyển `<Select>` "Nhiệm vụ" lên ĐẦU
    TIÊN trong lưới bộ lọc (trước "Chuyên đề"); (2) tiêu chí "Mới nhất" giờ CHỈ hiện bài CHƯA
    hoàn thành trong nhiệm vụ mới nhất (thêm điều kiện `trangThaiBai[b.id]?.trang_thai !==
    'hoan_thanh'`) — "Sắp hết hạn" KHÔNG đổi (vẫn không loại bài đã xong, không nằm trong yêu
    cầu sửa).
  - Test: `eslint` sạch · `vite build` OK · `vitest` 23/23. **Xác minh trực quan bằng
    Playwright thật** (2 vòng — vòng 2 sau khi sửa theo yêu cầu trên): tạo nhiệm vụ test
    trong `dev.db` với 1 bài đã hoàn thành thật (`trang_thai` phiên gần nhất, KHÔNG suy từ
    phiên bất kỳ — dev.db có nhiều phiên/bài do lịch sử test cũ, phải lọc đúng phiên
    `cap_nhat_luc` mới nhất như backend `/sessions/cua-toi` làm) + 1 bài chưa làm, xác nhận
    "Mới nhất" chỉ hiện đúng bài chưa hoàn thành — đã dọn sạch dữ liệu test sau khi xong.
    **Lưu ý**: đã tạm đổi mật khẩu `a1hs1` trong `dev.db` local thành `test123` để đăng nhập
    test (không ảnh hưởng production, đã báo user).

- **ui: (v143) "Nhờ thầy/cô" — 2 nút "Hủy"/"Gửi yêu cầu" chuyển lên NGAY DƯỚI ô nhập, TRƯỚC
  phần "Xem trước" (trước đây nằm sau cả phần xem trước, HS dễ không thấy nút).**
  `frontend/src/pages/hs/PhongHoc.jsx`: dùng lại prop `duoiO` có sẵn của `MixedChatInput`
  (component tự expose đúng slot "nội dung ngay dưới ô nhập, trước phần xem trước/bảng công
  thức" — đã dùng cho nút "Gửi câu hỏi" ở ô "Trò chuyện với gia sư", giờ áp dụng thêm cho ô
  "Nhờ thầy/cô") thay vì render 2 nút RIÊNG sau `<MixedChatInput>` như cũ. Không cần sửa
  `MixedChatInput.jsx` (prop đã có sẵn, đúng thiết kế ban đầu, chỉ là ô "Nhờ thầy/cô" trước
  đây chưa dùng). Test: `eslint`/`vite build`/`vitest` 23/23 sạch — xác minh trực quan bằng
  Playwright thật (mở phòng học, bấm "Nhờ thầy/cô", gõ nội dung có công thức, chụp ảnh xác
  nhận 2 nút nằm đúng vị trí ngay dưới ô nhập, trên phần "Xem trước").
  - **Áp dụng thêm cho phía GV** (theo yêu cầu tiếp theo của user): `frontend/src/pages/gv/HoTroHocSinh.jsx`
    — nút "Gửi trả lời" (+ dòng lỗi validate nếu có) trong modal "Chi tiết yêu cầu trợ giúp"
    cũng chuyển vào `duoiO`, cùng cách làm với phía HS — trước đó nằm sau `<MixedChatInput>`
    (dưới cả phần xem trước). Test: `eslint`/`vite build`/`vitest` 23/23 sạch — xác minh trực
    quan bằng Playwright thật (HS gửi 1 yêu cầu "Nhờ thầy/cô" thật → GV đăng nhập, mở modal
    "Xem chi tiết" → "Trả lời", gõ nội dung, chụp ảnh xác nhận nút đúng vị trí) — đã dọn sạch
    dữ liệu test (yêu cầu, turn, thông báo, cờ liên quan) sau khi xong.

## 1d. Trạng thái trước đó (v142)

- **🐞 (v142) fix: TN4PA báo sai "nhập lại biểu thức hợp lệ" sau khi HS đã làm ĐÚNG và mở
  khóa đáp án — root cause thật của bug user báo qua ảnh chụp; + chặn LƯU khi
  "bieu_thuc_ket_qua" không parse được (bug thứ 2, tìm thấy khi quét production).**
  User báo: HS nhập đúng biểu thức đạo hàm, gia sư xác nhận đúng và mở khay đáp án A–D,
  nhưng nếu (vô tình) gửi lại đúng biểu thức đó lần nữa thì gia sư lại nói "nhập lại bằng
  một biểu thức toán hợp lệ nhé" — dù trước đó vừa xác nhận đúng.
  - **Chẩn đoán #1 (root cause thật, đã tái hiện 100% bằng test)**: tra trực tiếp bảng
    `turns` trên production (đã xin phép, dùng `DATABASE_URL` production tạm thời, chỉ đọc)
    tìm đúng session gây lỗi. Phát hiện: sau khi HS làm ĐÚNG bước bắt buộc (`bat_buoc_suy_luan`)
    và `buoc_hien_tai` chuyển sang bước KẾ TIẾP để mở khóa đáp án, bước kế đó **rỗng**
    (TN4PA thường chỉ cần đúng 1 bước để mở khóa, "bước 2" không có nội dung thật). Nếu HS
    gửi lại MỘT BIỂU THỨC (không bấm A–D) lúc này, `tutor_service.xu_ly_luot` vẫn so khớp
    CAS với `bieu_thuc_ket_qua` RỖNG của bước đó — `tuong_duong(HS, "")` luôn ra
    `KHONG_PHAN_TICH_DUOC` **bất kể HS nhập gì, kể cả gửi lại chính biểu thức vừa đúng.**
    Câu hỏi cụ thể trong ảnh (problem #1 production, "Hàm số $y=x^3-3x+3$ đồng biến...") xác
    nhận đúng cơ chế này qua log turn thật (turn 61 DUNG → turn 62 gửi lại y hệt → turn 63
    KHONG_PHAN_TICH_DUOC).
  - **Sửa #1**: `tutor_service.py` nhánh TN4PA pha suy luận — CHỈ gọi `so_khop` khi
    `bieu_thuc_ket_qua` của bước hiện tại KHÔNG rỗng; rỗng thì để `ket_qua=None` (rơi về
    nhánh "giai_thich_ngan", không còn báo sai "biểu thức không hợp lệ"). Đã xác nhận
    `danh_sach_goi_y` của bước rỗng đó không rỗng (không có nguy cơ crash `_lay_goi_y`
    index-out-of-range nếu list gợi ý rỗng — rủi ro riêng, chưa gặp thật, ngoài phạm vi sửa
    lần này).
  - **Chẩn đoán #2 (bug khác, tìm thấy khi viết script quét production)**: nếu
    `bieu_thuc_ket_qua` lỡ còn sót ký hiệu LaTeX thô (điển hình dấu `$` thừa do AI quên bỏ
    dù prompt đã cấm bọc `$` cho field này — cùng họ lỗi với sự cố v139/v141) thì CAS cũng
    luôn báo "không phân tích được" cho MỌI học sinh làm bài đó, vì bên không parse được là
    "chuẩn" chứ không phải bài làm HS. Quét production qua
    `backend/scripts/kiem_tra_bieu_thuc_ket_qua.py` (script mới, chỉ đọc) tìm thấy đúng 1 câu
    hỏng thật (problem #31, "$\vec{a}...$", bước có `bieu_thuc_ket_qua='(4; 4; -2)'` — cú
    pháp tuple không phải SymPy hợp lệ) — KHÔNG phải câu trong ảnh gốc (đã xác nhận qua log
    turn ở Chẩn đoán #1), là 1 sự cố độc lập cùng phát hiện trong đợt quét này.
  - **Vì sao bug #2 lọt được tới production**: `validate_cau_hoi()` ĐÃ CÓ cảnh báo
    `kiem_tra_bieu_thuc` cho trường hợp này — nhưng chỉ hiển thị cho GV xem, KHÔNG chặn lưu;
    GV duyệt vội bỏ qua cảnh báo → câu hỏng lên production.
  - **Sửa #2**: thêm `buoc_co_bieu_thuc_khong_hop_le()` (`core/matching/cas.py`, thuần,
    không phụ thuộc LLM/web) — gắn thành CHẶN LƯU thật (raise `ValueError` → HTTP 400) ở CẢ 3
    điểm ghi `SolutionStep` xuống DB: `problem_service.tao_problem`, `problem_service.sua_problem`
    (validate TRƯỚC khi xóa bước cũ, tránh mất dữ liệu tốt nếu bước mới hỏng), và
    `question_gen_service._luu_mot_cau` (dùng chung bởi AI sinh hàng loạt — câu hỏng bị ÂM
    THẦM BỎ QUA như câu rỗng khác — và "AI tạo bước và gợi ý" — GV thấy lỗi 400 rõ khi Lưu).
  - **Chẩn đoán #3 / Sửa #3 (theo yêu cầu user sau khi thấy câu #31)**: thay vì bắt GV đổi
    `bieu_thuc_ket_qua` sang cú pháp `Matrix([4,4,-2])` (không thân thiện), CAS được dạy hiểu
    LUÔN dạng tọa độ/vectơ kiểu SGK VN `"(a; b; c)"` (dấu `;` ngăn thành phần — cùng quy ước
    dấu `;` app đã dùng cho khoảng `"(-\infty; 1)"`; dấu `,` trong mỗi thành phần là thập
    phân kiểu VN, vd `"(1,5; 2; -3)"`). Thêm `_thu_parse_vecto()` (`core/matching/cas.py`) —
    tách theo `;`, chuẩn hóa `,`→`.`, sympify riêng từng thành phần, dựng `sympy.Matrix`.
    Áp dụng cho CẢ HS nhập lẫn "chuẩn" lưu trong DB (dùng chung `_parse_an_toan`) — HS gõ
    `(2+2; 4; -2)` vẫn được RÚT GỌN & so khớp đúng với chuẩn `(4; 4; -2)` (chế độ
    `tuong_duong`, mặc định); chế độ `dung_dang` so cấu trúc, không rút gọn. Sửa
    `tuong_duong()` dùng `is_zero_matrix` thay vì `diff == 0` (Matrix không bao giờ `==0`
    trực tiếp trong SymPy). **Hệ quả tốt bất ngờ**: câu #31 tự động HẾT bị coi là hỏng (đã
    chạy lại script chẩn đoán trên production: 0 lỗi) — KHÔNG cần GV sửa tay như dự kiến ban
    đầu, vì `"(4; 4; -2)"` giờ là cú pháp hợp lệ.
  - Test: 17 test mới — 8 cho fix TN4PA (kể cả `test_tn4pa_gui_lai_bieu_thuc_dung_sau_khi_da_mo_khoa_khong_bao_sai`,
    đã tự xác nhận: revert fix #1 → fail đúng KHONG_PHAN_TICH_DUOC, khôi phục → pass — chứng
    minh test bắt đúng lỗi thật) + 3 cho `buoc_co_bieu_thuc_khong_hop_le`/chặn lưu qua API +
    9 cho cú pháp vectơ (rút gọn từng thành phần, thập phân dấu phẩy, sai 1 thành phần, lệch
    số chiều → KHONG_PHAN_TICH_DUOC, dung_dang vs tuong_duong, hồi quy không phá bug gốc
    v142/biểu thức đại số thường). `ruff` sạch · `pytest` 617/617.

## 1e. Trạng thái trước đó (v141)

- **✨ (v141) feat: quy tắc LaTeX góc/vectơ/aligned/suy-ra cho AI sinh công thức.** Theo yêu cầu
  bổ sung định dạng: góc 1 đỉnh `$\widehat{A}$`, góc 3 điểm `$\widehat{ABC}$`, vectơ 1 chữ
  `$\vec{u}$`, vectơ 2 chữ `$\overrightarrow{AB}$`, cấm môi trường `\begin{aligned}...\end{aligned}`,
  mỗi biểu thức/bước xuống dòng riêng khi cần, không dùng ký hiệu suy ra (⇒) trong công thức mà
  viết chữ ("Suy ra $AB=CD$.").
  - **Gộp 1 chỗ dùng chung**: thêm hằng số `_QUY_TAC_LATEX` (`backend/app/llm/prompts.py`) chứa
    cả 6 quy tắc trên (kèm quy tắc $...$ có sẵn từ v139), nhúng vào CẢ 3 prompt sinh/trích công
    thức (`SYSTEM_SINH_CAU_HOI`, `SYSTEM_TAO_BUOC_GOI_Y`, `SYSTEM_DOC_DE_TU_ANH`) thay vì lặp lại
    rải rác — tránh tái diễn kiểu lệch nhau đã gây sự cố v139 (1 prompt quên nhắc 1 prompt có).
  - **Lưới an toàn**: thêm `canh_bao_dinh_dang_latex_khac()` (`question_gen.py`), gắn vào
    `validate_cau_hoi()` — dò 2 vi phạm dễ phát hiện bằng regex: dùng `\begin{aligned}`, hoặc
    dùng `⇒`/`=>`/`\Rightarrow`/`\implies` trong công thức. KHÔNG tự dò được quy tắc góc/vectơ
    (quá nhiều cách viết hợp lệ, dễ báo sai) — phần đó chỉ dựa vào prompt.
  - **Giới hạn đã biết**: local dùng `StubLLMClient` (không gọi mạng thật) nên KHÔNG thể xác
    nhận AI thật có tuân thủ 6 quy tắc hay không — chỉ kiểm chứng tĩnh (rule có trong prompt +
    hàm cảnh báo bắt đúng vi phạm giả lập). Muốn xác nhận AI thật tuân thủ, cần thử trên
    production hoặc bật `LLM_PROVIDER=gemini` với key thật.
  - Test: thêm 5 test mới (`canh_bao_dinh_dang_latex_khac` + khóa quy tắc đảm bảo cả 3 prompt
    đều chứa đủ 6 quy tắc), sửa 1 test cũ do đổi câu chữ diễn đạt (nội dung yêu cầu không đổi).
    `ruff` sạch · `pytest` 600/600.

## 1f. Trạng thái trước đó (v140)

- **🐞 (v140) fix: sửa CI đỏ do v139 — ESLint `react-hooks/refs` báo lỗi cả những chỗ
  `{...common}` có sẵn từ trước.** GitHub Actions báo job `frontend` fail ngay sau khi push
  v139 (`npm run lint`), phát hiện qua thông báo CI của user.
  - **Nguyên nhân**: `TexField.jsx` (`splitPreview`, thêm ở v139) đọc `common.className` —
    `common` là object chứa `ref` (dùng cho input/textarea), và rule `react-hooks/refs` coi
    MỌI truy cập property trên object mang `ref` là "đọc ref lúc render", dù property đó
    (`className`) không liên quan gì tới ref. Việc này khiến linter lây lan báo lỗi cả 2 chỗ
    `{...common}` cũ (dòng trước khi có `splitPreview`, không hề đổi) vì giờ bị xếp chung
    "object mang ref không an toàn".
  - **Sửa**: tách `baseClassName` thành biến riêng độc lập với `common`, không còn đọc lại
    `common.className` ở bất kỳ đâu — chỉ spread `{...common}` rồi override `className` bằng
    biến riêng.
  - Test: chạy lại đúng 3 bước CI job `frontend` tại local — `npm run lint` sạch (0 lỗi,
    trước đó 4 lỗi) · `npm run test` (vitest) 23/23 · `npm run build` OK.
  - **Bài học**: trước khi đề xuất "đưa lên github" cho thay đổi frontend, PHẢI chạy
    `npm run lint` (không chỉ `build`) — v139 bỏ sót bước này nên lỗi lọt qua tới CI.

## 1g. Trạng thái trước đó (v139)

- **🐞 (v139) fix: công thức trong "lời giải chi tiết" (AI sinh) không hiện KaTeX do prompt
  quên yêu cầu bọc $...$; ui: ô "Lời giải chi tiết" (form sửa câu hỏi) chia 2 cột nhập/xem
  trước, tự giãn chiều cao theo nội dung.** Phát hiện qua user: ảnh chụp phần xem trước có
  nhiều đoạn công thức hiện thô (`y' = ...`, `\frac{...}`) dù quy ước là mọi công thức phải
  bọc `$...$` để FE render qua KaTeX.
  - **Nguyên nhân gốc**: `SYSTEM_TAO_BUOC_GOI_Y` (`backend/app/llm/prompts.py`) liệt kê rõ
    "đề bài"/phương án/ý/gợi ý phải bọc `$...$` trong mục RÀNG BUỘC BẮT BUỘC nhưng KHÔNG hề
    nhắc `loi_giai_chi_tiet` — AI tuân thủ không nhất quán, đặc biệt bỏ sót công thức NGẮN
    giữa câu văn xuôi. Đã sửa cả `SYSTEM_TAO_BUOC_GOI_Y` lẫn `SYSTEM_SINH_CAU_HOI`, nêu rõ
    yêu cầu + ví dụ công thức ngắn giữa câu.
  - **Lưới an toàn**: thêm `canh_bao_cong_thuc_chua_boc_dollar()` (`question_gen.py`), gắn
    vào `validate_cau_hoi()` — dò ký hiệu LaTeX rơi ra ngoài mọi cặp `$...$` (`\frac`, `^`,
    `_`, dấu `'` kiểu đạo hàm) trong `loi_giai_chi_tiet`, cảnh báo GV tự kiểm trước khi lưu
    (không chặn lưu — chỉ là lỗi trình bày, không sai đáp án). Áp dụng cho cả 2 luồng AI sinh
    câu hỏi (`sinh_nhap` batch + `sinh_buoc_goi_y` — đúng luồng gây ra sự cố).
  - **UI đi kèm** (`TexField.jsx`/`ThanCauHoiForm.jsx`): ô "Lời giải chi tiết" thêm prop
    `splitPreview` — chia 2 cột (trái: textarea tự giãn `scrollHeight` khớp đúng nội dung,
    phải: xem trước KaTeX cao bằng cột trái qua `items-stretch`); các ô `TexField` khác (đề
    bài/phương án/ý — ngắn) giữ nguyên layout xếp chồng cũ.
  - Test: thêm 6 test cho `canh_bao_cong_thuc_chua_boc_dollar()` + test khóa quy tắc (đảm bảo
    `loi_giai_chi_tiet` luôn đi kèm yêu cầu `$...$` trong cả 2 prompt, tránh tái nhiễm bug).
    `ruff` sạch · `pytest` 595/595 · `vite build` sạch. Xác minh UI bằng Playwright thật (đăng
    nhập GV, mở form sửa câu hỏi, điền lời giải nhiều dòng công thức, chụp ảnh xác nhận 2 cột
    cao bằng nhau và công thức render đúng).

## 1h. Trạng thái trước đó (v138)

- **🎨 (v138) ui: redesign 3 màn HS (TrangChu/PhongHoc/ChonBai) theo handoff — bỏ emoji chức
  năng, gom màu nhấn, dọn hex hard-code.** Theo `design_handoff_ui_redesign/README.md` +
  `redesign.dc.html` (thiết kế tham khảo HTML, không phải code copy thẳng). Thuần
  frontend/CSS/icon — KHÔNG đổi logic nghiệp vụ/API/state.
  - **TrangChu.jsx**: 7 icon emoji → `lucide-react` (`ClipboardList`, `Target`, `FileText`,
    `Clock`, `Zap`, `Hourglass`, `GraduationCap`); thẻ "Thành tích" bỏ gradient riêng lẻ mỗi
    ô → nền `bg` phẳng; nút "Làm tiếp" (Bài đang làm dở) đổi `warning`→`primary` (CTA cam —
    đúng vai "hành động tiếp tục học chính", cùng nhóm với "Tiếp tục làm" ở hero).
  - **PhongHoc.jsx**: 8 icon/ký hiệu emoji → lucide (`ArrowLeft`, `BookOpen`, `Check`,
    `CircleHelp`, `Lightbulb`, `Lock`, `Send`, `X`); toolbar bỏ nền cam/vàng riêng cho từng
    nút; hàng hành động dưới chat CHỈ CÒN 1 màu nhấn (`indigo` cho "Gợi ý cho em", còn lại
    `secondary` đồng nhất — trước dùng warning/indigo/success lẫn lộn); bỏ chữ IN HOA cứng
    trong nhãn nút; "Khu vực trả lời" + "Trò chuyện với gia sư" đổi `bg-primary-soft/40` và
    hex `#2596be` → `bg-bg`/`border-border` đồng nhất, chỉ màu ở LABEL (primary/muted).
    2 emoji `🙋` trong NỘI DUNG TIN NHẮN chat (transcript, không phải nhãn nút) và `🌟` (câu
    chúc mừng) CỐ Ý giữ nguyên — đúng ngoại lệ "emoji trong lời chào/copy thân thiện".
  - **ChonBai.jsx**: `text-black`→`text-ink`; nút "Xem lại" dùng icon `BookOpen`; Badge
    chuyển sang preset `trang_thai="hoan_thanh"`/`"dang_lam"` (bỏ tự set `tone` + text hoa
    tay "ĐÃ LÀM XONG"/"ĐANG LÀM DỞ").
  - **`styles/README.md`** ghi đè bằng bản `styles-README-updated.md` trong gói handoff —
    đồng bộ đúng token `theme.css` thật (trước ghi giá trị CŨ, vd primary `#5B4BDA` trong khi
    code thực tế `#3b36cc`), bổ sung mục Icon + Màu sắc.
  - **Mục B — dọn hex hard-code ngoài token**: thêm `--color-primary-soft-2: #f2f1fd` vào
    `theme.css`, dùng ở `TrangChu.jsx` + `TongQuan.jsx` (trước mỗi nơi tự hard-code
    `to-[#f2f1fd]`) — đã build-verify class `to-primary-soft-2` sinh đúng CSS thật. Tạo
    `utils/chartColors.js` gộp thang màu tím dùng chung cho `BanDoNangLuc.jsx` +
    `HieuQuaPhuongPhap.jsx`. **Lệch nhẹ so với đề xuất gốc**: KHÔNG ép cả 2 nơi dùng chung
    đúng 1 mảng 5-phần-tử `THANG_TIM` như README gợi ý, mà tách 2 hằng số riêng (`THANG_TIM`
    5 bậc cho bản đồ năng lực, `THANG_TIM_MUC_GOI_Y` 4 bậc cho mức gợi ý) — vì comment gốc
    trong `HieuQuaPhuongPhap.jsx` ghi rõ 4 giá trị đó ĐÃ CHẠY `validate_palette` PASS (contrast
    + CVD) cho đúng 4 bậc; ép về chung 1 mảng sẽ đổi hex và có thể phá kết quả validate đã có.
    Cả hai vẫn gộp về 1 FILE dùng chung (mục tiêu chính: hết khai báo trùng lặp/dễ lệch nhau).
  - **Mục C — bỏ emoji tooltip GV/Admin**: `TongQuan.jsx` (🚩 cờ / 🙋 nhờ thầy cô) và
    `Dashboard.jsx` (💬 hội thoại / ✨ sinh câu hỏi / 📊 phân tích) → icon `Flag`/`LifeBuoy`/
    `MessageCircle`/`Sparkles`/`BarChart3` lồng trong JSX trả về từ prop `tach()` của
    `BieuDoVung` (component vốn render `{tach(...)}` trong `<span>` nên nhận JSX tự nhiên,
    không cần đổi kiểu dữ liệu `tach`).
  - Test: `eslint` 0 · `vite build` sạch (verify riêng class `to-primary-soft-2` có CSS thật,
    vì Tailwind không báo lỗi khi utility không hợp lệ, chỉ lặng lẽ bỏ qua) · `vitest` 23/23.
    **Xác minh trực quan bằng Playwright** trên cả 5 màn hình (đăng nhập bằng token sinh trực
    tiếp qua backend thay vì đoán mật khẩu thật của dev.db) — 0 lỗi console/runtime; hover
    tận nơi xác nhận tooltip GV render đúng icon (DOM check + screenshot).

## 1i. Trạng thái trước đó (v137)

- **🐞 (v137) fix: chặn AI CHÉP đáp án theo khuôn mẫu prompt (few-shot leakage) + bắt GV xác
  nhận trước khi duyệt câu AI sinh.** Phát hiện qua user: lời giải chi tiết AI viết đúng
  nhưng 4 ý Đúng/Sai TNDS lại sai lệch với chính lời giải đó.
  - **Nguyên nhân gốc**: 3 mẫu JSON gửi cho AI (`_MAU_TN4PA/_MAU_TNDS/_MAU_TLN`) có MỌI
    trường là placeholder TRỪ đáp án — `"dap_an": "Dung"/"Sai"/"Dung"/"Sai"` (xen kẽ),
    `"dap_an_dung": "A"`, `"dap_an_cuoi": "5"` là GIÁ TRỊ THẬT. Model (đặc biệt bản nhẹ như
    gemini-2.5-flash) có xu hướng CHÉP nguyên khuôn few-shot này thay vì tự giải độc lập từng
    ý, trong khi lời giải (văn xuôi tự do, không có mẫu để chép) vẫn được suy luận đúng.
  - **Sửa gốc**: bỏ mọi giá trị thật khỏi 3 mẫu, thay bằng placeholder hướng dẫn (vd
    `"<Dung hoặc Sai — TỰ GIẢI ý này, KHÔNG copy ví dụ>"`). Test khóa quy tắc
    `test_mau_prompt_khong_chua_dap_an_that` để không ai vô tình thêm lại.
  - Thêm ràng buộc **AI tự đối chiếu** trong cả 2 system prompt (`SYSTEM_TAO_BUOC_GOI_Y`,
    `SYSTEM_SINH_CAU_HOI`): đáp án phải là hệ quả trực tiếp của lời giải, 4 ý TNDS ĐỘC LẬP
    (không suy theo vị trí a/b/c/d), lệch thì sửa đáp án theo lời giải (lời giải là nguồn
    sự thật).
  - Hàm mới `canh_bao_khuon_mau_tnds`: cảnh báo (không chặn lưu) khi 4 ý ra đúng khuôn xen kẽ
    Đúng-Sai-Đúng-Sai hoặc ngược lại — dấu hiệu chép mẫu.
  - **GV phải tự xác nhận đã đối chiếu đáp án với lời giải trước khi duyệt câu AI sinh** — áp
    ở **3 đường Duyệt** (rà thêm sau khi làm xong đường đầu, phát hiện 2 đường còn lại bỏ qua
    hoàn toàn checkbox mới thêm):
    1. "Tạo bước và gợi ý" (xem trước 1 câu) — checkbox trong `ThanCauHoiForm` (slot mới
       `xacNhanDapAn` + prop `nutLuuDisabled`, mặc định tắt nên KHÔNG ảnh hưởng luồng GV tự
       soạn/sửa câu thủ công).
    2. "Sinh hàng loạt" + "Hàng đợi chờ duyệt" — checkbox riêng từng câu, khóa nút Duyệt.
    3. **Modal "Sửa" dùng chung** (mở từ cả 2 màn AI lẫn Quản lý câu hỏi) có hộp thoại "Duyệt
       luôn?" — TRƯỚC ĐÓ hoàn toàn bỏ qua checkbox. Sửa: chỉ hỏi "Duyệt luôn?" khi đã tích
       (câu AI sinh); câu GV tự nhập/import không cần vì GV tự viết đáp án.
    4. **Bảng "Quản lý câu hỏi"** có nút Duyệt 1 chạm ngay trên hàng tóm tắt (KHÔNG hiện đề
       bài/đáp án/lời giải) — lỗ nghiêm trọng nhất, GV duyệt được mà chưa từng thấy nội dung.
       Ẩn nút này khi `nguon === 'ai_sinh'` chưa duyệt, buộc qua "Xem/Sửa" (nơi có checkbox).
  - Test: `pytest` **588/588** (+5 `test_question_gen.py`), `ruff`/`eslint`/`vite build`
    sạch, `vitest` 23/23, E2E 3/3 (xác nhận luồng Duyệt câu `gv_nhap`/import KHÔNG bị ảnh
    hưởng — chỉ ẩn nút nhanh cho `ai_sinh`).
  - **Lưu ý**: đây là sửa PHÒNG NGỪA, chưa tái hiện trực tiếp trên dữ liệu thật (local không
    có câu TNDS nào do AI sinh để so sánh, đang chạy LLM stub). Nên kiểm chứng thêm khi có
    mạng thật: sinh vài câu TNDS xem 4 ý còn ra đúng khuôn xen kẽ không.

## 1j. Trạng thái trước đó (v136)

- **🐞 (v136) fix: GV không còn giao trùng bài HS đã hoàn thành khi giao nhiệm vụ.**
  Trước đây `tao_nhiem_vu` chỉ kiểm bài tồn tại/đã duyệt/thuộc GV — không kiểm hoàn thành, dù
  hàm `_hoan_thanh_set` đã có sẵn và đang dùng ở 2 luồng đề xuất + 2 luồng hiển thị tiến độ.
  - **Quyết định thiết kế then chốt**: chặn theo "MỌI HS được giao đều đã làm", KHÔNG phải
    "bất kỳ HS nào đã làm" — nếu chặn theo bất kỳ, giao cho cả lớp 40 em sẽ gần như không còn
    bài nào giao được (luôn có ai đó từng làm). Chọn đúng 1 HS thì hai luật trùng nhau, đúng
    ý gốc "không giao trùng bài em đó đã làm".
  - **Lỗ thứ hai phát hiện thêm**: `cap_nhat_nhiem_vu` (đường SỬA nhiệm vụ) không hề kiểm —
    GV tạo nhiệm vụ sạch rồi sửa để nhét bài đã hoàn thành vào vẫn lọt. Chặn ở CẢ HAI đường,
    đặt logic trong service (`_chan_bai_ca_nhom_da_lam`) để không phụ thuộc FE lọc đúng hay
    không.
  - Hàm mới `dem_hoan_thanh(gv_id, hoc_sinh_ids)` + `GET /nhiem-vu/da-hoan-thanh`: đếm mỗi bài
    có bao nhiêu em (trong tập đang chọn) đã hoàn thành, trả bảng thưa.
  - FE (`GiaoNhiemVu.jsx`): bài **cả nhóm đã làm** → mờ, checkbox khóa, badge xanh; bài **một
    phần** nhóm đã làm → vẫn chọn được, badge cam "N/M em đã làm" (GV tự quyết); "Chọn tất cả"
    bỏ qua bài bị khóa; đổi tập HS thì tự bỏ tích bài vừa bị khóa (tránh gửi đi bài đã ẩn khỏi
    màn hình); nhắc "chọn học sinh trước" khi chưa chọn ai.
  - Test: `pytest` **583/583** (+6 `test_nhiem_vu.py`: chặn 1 HS đã làm / KHÔNG chặn khi chỉ
    1-trong-nhiều em đã làm / chặn khi cả nhóm đã làm / chặn ở đường sửa / endpoint đếm /
    chặn xem HS lớp khác), `ruff`/`eslint`/`vite build` sạch, `vitest` 23/23. Xác minh route
    mới có thật trong app đang chạy qua `/openapi.json`.

## 1k. Trạng thái trước đó (v135)

- **✨ (v135) feat: HS TỰ đăng ký bằng MÃ LỚP — gỡ nút thắt "phải chờ GV nhập tay từng em".**
  Trước đây chỉ GV/Admin tạo được tài khoản HS, nên không GV nào triển khai thì không HS nào
  dùng được. Nay GV sinh mã, đọc cho cả lớp; HS tự tạo tài khoản và vào đúng lớp.
  **Chuỗi trách nhiệm giữ nguyên**: mọi HS tự đăng ký vẫn thuộc một lớp CÓ GV phụ trách.
  - **Pha A** — `lop.ma_lop` (unique index, nullable — **NULL = lớp ĐÓNG**, cố ý không thêm cờ
    riêng để tránh 2 nguồn sự thật) + `lop.ma_het_han`; migration `e2a75c1c5e82`.
    `core/ma_lop.py`: mã 8 ký tự từ bảng chữ 31 ký tự **bỏ `0/O`, `1/I/L`** (thầy cô đọc cho cả
    lớp chép), hiển thị `A7K3-QM9X`; `chuan_hoa` nhận mọi kiểu gõ (thường/gạch/khoảng trắng).
    Không gian mã 31⁸ ≈ 8,5×10¹¹ → dò mù bất khả thi.
  - **Pha B** — 4 endpoint: `GET /auth/lop-tu-ma` + `POST /auth/dang-ky` (**2 endpoint CÔNG
    KHAI đầu tiên của hệ thống**), `POST|DELETE /gv/lop/{id}/ma`. Quyết định nghiệp vụ đã chốt:
    HS vào lớp NGAY (trả token luôn) · HS tự đặt tên đăng nhập · CHẶN lớp chưa có GV.
    - **Throttle chỉ đếm lần nhập SAI mã**, khóa theo IP: cả lớp 40 em đăng ký cùng lúc qua
      NAT trường không sinh lần sai nào nên không bao giờ bị khóa oan; kẻ dò mã chỉ tạo lần
      sai nên bị chặn nhanh. (Cùng triết lý throttle login sẵn có.)
    - **Vai trò CỨNG `hs`, `lop_id` lấy từ MÃ** — client không được khai; có test gửi kèm
      `vai_tro:"admin"`, `la_quan_ly:true` và xác nhận bị bỏ qua.
    - Mã sai và mã hết hạn trả **cùng một thông điệp** → không lộ mã nào từng có thật.
    - Hai lớp trần chống spam: **60 đăng ký/lớp/ngày** (dựa `users.tao_luc`, migration
      `040595cbe601`) + **100 tổng sĩ số** (chặn kiểu nhỏ giọt nhiều ngày). GV nhận thông báo
      mỗi khi có HS tự vào lớp → luôn biết ai trong lớp mình và khóa được ngay.
  - **Pha C** — màn đăng ký **2 bước** (nhập mã → hiện TÊN LỚP + TÊN GV để xác nhận, chống vào
    nhầm lớp → nhập thông tin → vào thẳng phòng học); link "Đăng ký bằng mã lớp" ở trang đăng
    nhập; khu quản lý mã trong Quản lý lớp GV (Tạo mã / Sao chép / Đổi mã / Thu hồi + hạn).
  - **Dọn drift model vs dev.db (điều tra lật ngược kết luận ban đầu)**: `tom_tat_ly_thuyet.
    noi_dung` và FK `yeu_cau_tro_giup.turn_id` bị autogenerate báo lệch ở mọi lần chạy. Truy ra
    **BASELINE MIGRATION (= production Postgres) VỐN ĐÃ ĐÚNG**, chỉ `dev.db` local sai (di sản
    thời trước Alembic, `turn_id` thêm bằng `ALTER TABLE ADD COLUMN` nên không kèm FK). Nếu viết
    migration "sửa drift" như định ban đầu thì đã đi sửa thứ không hỏng và `create_foreign_key`
    sẽ lỗi trên Postgres. → Vá riêng `dev.db` bằng `PRAGMA writable_schema` (sửa văn bản DDL,
    không dời dữ liệu). Autogenerate nay sinh migration RỖNG.
  - `.gitignore` thêm `*.db.bak*` — bản sao CSDL trước migration **chứa dữ liệu học sinh**
    (họ tên, hash mật khẩu), `*.db` không khớp nên trước đó vẫn lọt ra untracked.
  - Test: `pytest` **577/577** (+8 `test_ma_lop.py`, +16 `test_dang_ky_ma_lop.py`),
    `ruff`/`eslint`/`vite build` sạch, `vitest` 23/23. Migration round-trip trên BẢN SAO trước
    khi áp `dev.db`. Xác minh thêm bằng HTTP thật trên server đang chạy.
  - **3 bài học ghi lại**: (a) autogenerate **luôn quên `import app.db.types`** với kiểu cột tùy
    biến → thiếu là NameError lúc chạy migration, phải kiểm tay mọi lần; (b) truyền
    `tao_luc=None` lúc khởi tạo **không** tạo NULL — SQLAlchemy vẫn áp `default=`, phải UPDATE
    sau insert (test đầu tiên của tôi sai vì điều này); (c) vá `sqlite_master` phải dùng THAM SỐ
    RÀNG BUỘC, dùng `repr()` sẽ sinh escape kiểu Python (`\t`) làm hỏng schema (đã xảy ra, khôi
    phục từ backup).

## 1l. Trạng thái trước đó (v134)

- **✨ (v134) feat: thống kê GV chuyển sang đơn vị LỚP (không còn gộp mọi lớp GV phụ trách).**
  Gộp nhiều lớp làm chìm khác biệt giữa các lớp và để lớp đông lấn át lớp nhỏ; đơn vị thống
  kê nay khớp đơn vị GV thực sự hành động (dạy lại một chuyên đề cho MỘT lớp).
  - **6 endpoint đổi sang lọc theo `lop_id`** (mặc định lớp đầu tiên ở FE, GV 1 lớp thì trong
    suốt): `/progress/students`, `/lop/tong-hop`, `/lop/nhip-ngay`, `/lop/kho-khan-ngay`,
    `/gv/tong-quan`, `/ban-do/lop`. Kiểm quyền dùng chung `_kiem_lop` (GV chỉ xem lớp mình,
    Admin xem mọi lớp).
  - **Ngoại lệ CỐ Ý theo yêu cầu nghiệp vụ**: Tổng quan GV — sĩ số HS / HS bị khóa / cờ theo
    dõi vẫn GỘP mọi lớp (GV 1 lớp thì trùng luôn lớp đó); *Hiệu quả phương pháp* giữ "Tất cả
    các lớp" làm mặc định — đo CÁCH DẠY chứ không đo lớp, gộp cho mẫu lớn hơn nên tín hiệu ổn
    định hơn.
  - **Sửa chỗ hiểu sai bản chất** (độc lập với việc tách lớp): thẻ "dạng/loại tốn nhiều thời
    gian" trước cộng dồn TỔNG thời gian → dạng được GIAO NHIỀU NHẤT luôn đứng đầu, không phải
    dạng KHÓ NHẤT. Nay dùng **thời gian TRUNG BÌNH mỗi lượt** kèm `so_luot`, chỉ xếp hạng
    nhóm ≥5 lượt.
  - **Chặn xếp hạng trên mẫu quá nhỏ**: `tong_hop_lop_gv` trả `du_mau`/`nguong_mau` (cần ≥5 HS
    có dữ liệu) — cắt theo lớp làm mẫu số tụt nhanh, vài lượt làm cũng ra con số "báo động"
    nhưng vô nghĩa thống kê. FE hiện "chưa đủ dữ liệu" thay vì vẽ xếp hạng khi dưới ngưỡng.
  - **Mới `/progress/lop/so-sanh`**: mỗi lớp một dòng trên cùng bộ chỉ số — thay cho số gộp,
    vẫn so sánh được lớp nào đang đuối mà không làm chìm khác biệt giữa các lớp.
  - **Digest nhắc GV** (`day_nhac_diem_yeu_tuan`) tách thành **1 thông báo/lớp** (tiêu đề kèm
    tên lớp, `lien_ket_id=lop_id`), dedup theo TỪNG lớp (trước dedup theo GV sẽ chặn mất lớp
    thứ 2 trong cùng tuần).
  - FE: component dùng chung `ChonLop` (tự chọn lớp đầu, ẩn khi GV chỉ 1 lớp); TheoDoiTienBo
    hợp nhất về **1 bộ lọc lớp cho cả trang** (trước Bản đồ năng lực có bộ chọn riêng → 2
    phạm vi dễ lệch nhau) + bảng "So sánh các lớp".
  - **2 lỗi phát hiện SAU khi test thủ công (không bắt được bằng test tự động)**, đã sửa ngay:
    (a) `Select` dùng chung của dự án render từ prop `options`, **bỏ qua children** — `ChonLop`
    ban đầu truyền `<option>` con nên dropdown rỗng; (b) card "Lớp của tôi" + nhãn Bản đồ năng
    lực suy lớp từ `students` — sau khi `students` lọc theo lớp thì suy ra chỉ còn 1 lớp. Bài
    học: MỌI danh sách lớp phải lấy từ API riêng (`/gv/lop`, `/lop/so-sanh`), không suy từ
    một danh sách đã bị lọc theo lớp khác.
  - Test: `pytest` **553/553** (+8 `test_thong_ke_theo_lop.py`), `ruff`/`eslint`/`vite build`
    sạch, `vitest` 23/23. Xác minh thêm bằng script đọc thẳng `dev.db` qua ORM (không chỉ tin
    HTTP 200) sau sự cố backend không nạp code mới do socket cổng 8000 bị treo.

## 1m. Trạng thái trước đó (v133)

- **🐞 (v133) fix: GV "Trả lời thêm" không còn làm MẤT các câu trả lời cũ.** Lỗi lộ ra sau khi
  v132 cho phép trả lời tiếp ở yêu cầu đã trả lời.
  - **Dữ liệu KHÔNG hề mất** — `tra_loi()` vẫn chèn một `Turn(vai_tro=giao_vien)` THẬT mỗi lần
    trả lời, nên HS luôn thấy đủ trong khung chat. Lỗi nằm ở **đường ĐỌC phía GV**, do 2 tầng
    cộng lại: (a) `yc.tra_loi = noi_dung` **ghi đè**, chỉ giữ câu cuối; (b)
    `chi_tiet_hoi_thoai()` lọc `Turn.id <= yc.turn_id` (cắt đúng mốc HS nhờ) nên **loại bỏ luôn
    các Turn trả lời thật**, rồi ghép lại đúng 1 turn tổng hợp từ `yc.tra_loi`.
  - **Sửa đường đọc, KHÔNG cần migration**: `chi_tiet_hoi_thoai()` lấy **toàn bộ Turn
    `giao_vien` nằm SAU mốc nhờ**, theo thứ tự. Có **chặn trên** theo `turn_id` của yêu cầu kế
    tiếp trong cùng phiên → trả lời của yêu cầu SAU không gộp nhầm vào yêu cầu TRƯỚC. Yêu cầu
    CŨ (chưa có `turn_id`) giữ fallback cũ (chỉ có câu gần nhất).
  - FE: card danh sách đổi nhãn `Trả lời:` → **`Trả lời gần nhất:`** cho trung thực (lịch sử
    đầy đủ nằm trong "Xem chi tiết") — tránh phải thêm truy vấn đếm cho từng dòng.
  - 2 test mới: `test_tra_loi_them_giu_du_lich_su` (2 lần trả lời → chi tiết đủ cả 2, đúng thứ
    tự) và `test_tra_loi_khong_lan_sang_yeu_cau_sau` (2 yêu cầu cùng phiên → không lẫn).
    `pytest` **545/545** (+2), `ruff`/`eslint`/`vite build` sạch, `vitest` 23/23.
  - **Bài học**: khi một trường bị ghi đè (`tra_loi`) được dùng làm nguồn hiển thị LỊCH SỬ thì
    sớm muộn sẽ mất dữ liệu hiển thị — nguồn lịch sử phải là bảng append-only (`Turn`).

## 1n. Trạng thái trước đó (v132)

- **✨ (v132) ui: gộp phòng học về MỘT khối soạn — khu vực trả lời & trò chuyện tách rõ, nhờ
  thầy/cô inline.** Thuần frontend, KHÔNG đụng backend/API/lõi/guard/nguyên tắc bất biến — hợp
  đồng `dap_an_nhap`/`noi_dung`/`yeu_cau_goi_y` giữ nguyên.
  - **Gộp 2 card** (hội thoại `lg:col-span-3` + trả lời `lg:col-span-2`) thành 1 Card. Helper
    mới `KhayDapAn` — "Khu vực trả lời" biến hình theo `loai_cau` + `cho_chon_dap_an`/
    `cho_chon_dung_sai`, **tái dùng nguyên** `AnswerInputTLN/TN4PA/TNDS`.
  - Bố cục khối soạn: dòng nhắc (khi hết gợi ý) → **hàng nút** (💡 gợi ý · 🙋 nhờ thầy/cô ·
    📖 lý thuyết khi hết gợi ý · ↩ quay lại) → nhờ-thầy-cô **inline** (bỏ modal toàn màn) →
    **2 cột: Khu vực trả lời (trái) · Trò chuyện với gia sư (phải)**. Khung hội thoại có viền.
  - **Bỏ khối "3 nút" khi hết gợi ý** (Xem lý thuyết/Nhờ thầy cô/Hỏi gia sư) — 2/3 chỉ là lối
    tắt tới thứ đã có sẵn trong khối; thay bằng 1 dòng nhắc + 💡 tự tắt · 🙋 nhấp nháy · 📖 chỉ
    hiện khi hết gợi ý.
  - **Bảng công thức (MathPalette) chỉ hiện khi focus vào ô** (ô đáp án lẫn ô trò chuyện), tự
    ẩn khi bấm/chuyển focus ra ngoài — dùng cả `mousedown` **và `focusin`** (MathLive không
    phát mousedown bubble nên trước đó 2 bảng hiện đồng thời).
  - **GV Hỗ trợ HS**: nút "Trả lời" nay hiện cả ở yêu cầu ĐÃ trả lời (nhãn "Trả lời thêm") để
    GV trả lời tiếp — backend `tro_giup_service.tra_loi` vốn không chặn theo trạng thái.
  - Button: thêm variant `indigo` (nền Indigo Học Đường) + `warningSoft` (cam nhạt). Màu nút
    theo yêu cầu: Gửi câu hỏi/Quay lại = indigo, Xem lý thuyết = success (bạc hà), Đã hết gợi
    ý = cam nhạt.
  - Test: `eslint` 0 · `vite build` sạch · `vitest` 23/23 · E2E 3 luồng vàng 3/3 (chạy trên
    bản tái cấu trúc; các chỉnh màu/bố cục sau đó không chạm đường E2E kiểm). Lưu ý: máy dev
    cạn RAM có lúc làm vite E2E OOM — không phải lỗi code.

## 1o. Trạng thái trước đó (v131)

- **✨ (v131) feat: mục tiêu HS nhiều dòng + nút admin "Nhắc GV ngay" + nút "Hủy" ở gợi ý.**
  - **#2b — Mục tiêu HS đa dạng (redesign)**: trước chỉ đặt theo tuần/chủ đề. Nay HS chọn
    số lượng câu cho TỪNG nhóm (chuyên đề/dạng + loại câu + mức độ) trong 1 mục tiêu — GIỐNG
    GV giao nhiệm vụ nhưng KHÔNG lộ nội dung câu. Model `MucTieu` thêm `loai='nhieu'` + cột JSON
    `muc_con` (danh sách dòng: `{dang_id?/chuyen_de?, loai_cau?, do_kho?, chi_tieu_so}`). Migration
    Alembic `0e5e53d3e3b3` (add column `muc_con`, nullable — an toàn Postgres). Tiến độ: mỗi dòng
    đếm độc lập theo bài ĐÃ hoàn thành khớp bộ lọc; mục tiêu `da_dat` khi MỌI dòng đạt (đảm bảo
    bởi `_tien_do = sum(min(prog_i, target_i))`, `chi_tieu_so = sum(target_i)`).
  - **FE `MucTieuPanel`** viết lại: form accordion (chip lọc loại câu/mức độ → nhóm chuyên đề →
    dạng → thêm dòng số lượng), dùng chung HS + GV. **Fix lọc bài**: HS `/problems` KHÔNG trả
    `trang_thai_duyet` → lọc `(trang_thai_duyet == null || === 'da_duyet') && !bi_an` (đúng cho
    cả HS lẫn GV). Thẻ mục tiêu render các dòng con khi `loai==='nhieu'`.
  - **#2a — nút "Hủy"** cạnh nút "+ Thêm" sau khi bấm Gợi ý: cùng hàng, cùng nền (`variant
    secondary`).
  - **#1 — nút admin "Nhắc GV ngay"**: endpoint `POST /api/admin/nhac-gv/chay` gọi
    `day_nhac_diem_yeu_tuan` (đẩy digest điểm yếu tức thì), + toggle `nhac_gv_diem_yeu` trong
    trang Cấu hình. Tương tự nút "quét phân tích ngay".
  - Test: `pytest` 543/543 (+6 mục tiêu nhiều dòng, +1 endpoint nhắc GV), `vitest` 23/23,
    `ruff`/`eslint`/`vite build` sạch; migration round-trip + chạy trên dev.db thật (data còn
    nguyên); Playwright xác minh HS tạo mục tiêu nhiều dòng qua accordion OK; E2E 3 luồng vàng 3/3.

## 1p. Trạng thái trước đó (v130)

- **✨ (v130) feat: chủ động nhắc GV mỗi tuần "N học sinh cần chú ý" (digest điểm yếu).**
  Trước đây phân tích điểm yếu là "kéo" (GV phải mở trang mới thấy) — giờ hệ thống CHỦ ĐỘNG
  đẩy vào chuông thông báo. Phương án đã được user duyệt trước khi code.
  - **Tái dùng gần hết code có sẵn**: `phan_tich_service.tong_hop_lop_gv` (đã tính "HS cần chú
    ý" + "dạng yếu chung") + `thong_bao_service.tao` + vòng lặp `lich_phan_tich`.
  - Hàm mới `phan_tich_service.day_nhac_diem_yeu_tuan(db)`: duyệt từng GV → nếu lớp CÓ HS cần
    chú ý thì tạo 1 thông báo "Học sinh cần chú ý tuần này" (nội dung: N em + tên, dạng cả lớp
    còn yếu; `lien_ket_loai='tien_bo'`). **Tất định — KHÔNG gọi LLM, không tốn quota**; dedup
    7 ngày/GV (mỗi GV chỉ nhận 1 lần/tuần); lỗi 1 GV không chặn GV khác.
  - Móc vào `lich_phan_tich._vong_lap` chạy MỖI vòng, **độc lập với `tu_dong_phan_tich`** (tắt
    AI vẫn nhắc GV được), gated bởi config mới `nhac_gv_diem_yeu` (mặc định BẬT, admin tắt được).
  - FE: `GiaoVienApp.moTuThongBao` thêm nhánh `tien_bo` → bấm thông báo mở trang Tiến bộ học sinh.
  - **Khoảng trống push-vs-pull đã nêu ở phân tích trước nay đã lấp.** Lưu ý scale: giống #12
    (hoãn) — nhiều worker có thể gửi trùng, nhưng dedup 7 ngày giảm nhẹ, hiện 1 tiến trình nên OK.
  - 4 test mới `test_nhac_gv.py` (gửi khi có HS yếu / dedup 7 ngày / gửi lại sau 7 ngày / không
    gửi khi lớp sạch). `pytest` 536/536 (+4), `ruff`/`eslint`/`vite build` sạch.

## 1q. Trạng thái trước đó (v129)

- **✨ (v129) ui: fix DỨT ĐIỂM cả lớp lỗi tràn ngang mobile — kẹp mọi grid card về 1 cột.**
  Thuần frontend/CSS.
  - **User báo thẻ "mất nhiều thời gian" ở HS Tiến độ VẪN tràn** dù v127 đã "fix". Nguyên nhân:
    grid đó (`ThongKeTienDo.jsx:225`) BỊ SÓT ở v127 vì `replace_all` khớp theo chuỗi có 10
    dấu cách thụt lề (dòng khác), còn dòng này thụt 8 dấu cách → không đổi.
  - **Fix cả lớp lỗi (không vá lẻ nữa)**: rà toàn frontend, thêm `grid-cols-1` base cho **60
    grid** ở 28 file đang thiếu (grid dùng `sm|md|lg|xl:grid-cols` mà không có base) — mobile
    kẹp cột về `minmax(0,1fr)` thay vì `auto` (nở theo nội dung). Desktop KHÔNG đổi (breakpoint
    vẫn override). Grid CỐ Ý nhiều cột mobile (`grid-cols-2`/`grid-cols-5` base cho ô số/đáp án)
    giữ nguyên.
  - **Bài học verify**: v127 test HS Tiến độ nhưng tài khoản CHƯA hoàn thành bài nào → 2 thẻ
    (chỉ hiện khi có dữ liệu hoàn thành) KHÔNG render → test "pass giả". v129 xác minh ĐÚNG:
    hoàn thành 1 bài TLN trước để thẻ có dữ liệu, RỒI đo ở 375px → `scrollWidth ≤ clientWidth`,
    không tràn. Verify UI phải đảm bảo thành phần cần kiểm THỰC SỰ render với dữ liệu.
  - `eslint`/`vite build` sạch, E2E 3 luồng vàng 3/3 — không hồi quy.

## 1r. Trạng thái trước đó (v128)

- **✨ (v128) ui: thêm nút "Giao bài nhanh" nổi bật ở header GV, đặt TRƯỚC chuông thông báo.**
  Thuần frontend.
  - `RoleLayout.jsx::UserMenu` thêm prop `onGiaoBai` — nếu có thì render nút màu CTA (cam,
    icon `ClipboardList` + chữ "Giao bài nhanh", ẩn chữ trên màn rất hẹp giữ icon) NGAY TRƯỚC
    `ChuongThongBao`. `SidebarLayout` truyền `onGiaoBai` = điều hướng `nhiem_vu` **chỉ khi
    `vai_tro === 'gv'`** → Admin (cũng dùng SidebarLayout) và HS KHÔNG có nút.
  - Bấm nút → mở trang "Giao bài / nhiệm vụ" (GiaoNhiemVu) — lối tắt 1 chạm từ mọi trang GV.
  - **Xác minh khách quan Playwright**: GV thấy nút + nút đứng trước chuông (so `boundingBox().x`)
    + bấm điều hướng đúng trang; HS không có nút. `eslint`/`vite build` sạch, E2E 3 luồng 3/3
    (lần fail giữa chừng do kẹt port tiến trình sót — kill port chạy lại sạch, không phải lỗi code).

## 1s. Trạng thái trước đó (v127)

- **✨ (v127) ui: fix 5 thẻ tràn ngang trên điện thoại (Bài đang làm dở, Theo dạng bài/Theo
  loại câu hỏi, Dạng bài/Loại câu hỏi mất nhiều thời gian).** Thuần frontend/CSS.
  - **Nguyên nhân GỐC (tìm ra nhờ xác minh khách quan, sâu hơn chẩn đoán ban đầu)**: các grid
    dùng `grid lg:grid-cols-2` **thiếu `grid-cols-1` ở base** → trên mobile cột là `auto`
    (nở theo max-content) thay vì `minmax(0,1fr)` (kẹp về viewport) → card rộng hơn ô chứa →
    tràn ngang cả trang. Fix: thêm `grid-cols-1` vào base các grid card (TrangChu, TongQuan,
    PhanTichNangLuc, ThongKeTienDo) — desktop không đổi (`lg:grid-cols-2` vẫn override).
  - **Fix bổ trợ (cho nội dung dài co được bên trong card đã kẹp)**: `truncate` trên flex item
    thiếu `min-w-0` (BangXepHangThoiGian, HangNhom) → thêm `min-w-0`; dòng meta "Bài đang làm
    dở" thiếu `flex-wrap` → thêm.
  - **Xác minh KHÁCH QUAN bằng Playwright 375px** (không chỉ suy luận): assert
    `document.scrollWidth <= clientWidth` + chẩn đoán phần tử "lá" tràn. Lần đầu chẩn đoán
    (min-w-0/flex-wrap) CHƯA đủ — test vẫn báo tràn 6px → truy ra grid mới là gốc, fix tiếp,
    test PASS (scrollW 375 = viewport). TrangChu + Tiến độ HS đều sạch.
  - `eslint`/`vite build`/`vitest` 23/23, `playwright` 3 luồng vàng 3/3 — không hồi quy.

## 1t. Trạng thái trước đó (v126)

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

## 1u. Trạng thái trước đó (v125)

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

## 1v. Trạng thái trước đó (v124)

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

## 1w. Trạng thái trước đó (v123)

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

## 1x. Trạng thái trước đó (v122)

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

## 1y. Trạng thái trước đó (v121)

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
