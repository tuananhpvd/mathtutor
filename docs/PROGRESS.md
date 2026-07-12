# PROGRESS.md — Trạng thái & bàn giao (cập nhật để kế thừa giữa các phiên/máy)

> File này là "trí nhớ đi theo repo" (lên GitHub). Bộ nhớ tự động của Claude Code nằm trên máy
> local, KHÔNG lên GitHub — nên mọi quyết định/trạng thái cần nhớ hãy ghi vào đây hoặc vào `docs/`.
> **Đọc cùng `CLAUDE.md` đầu mỗi phiên. Mỗi lần làm xong việc đáng kể, CẬP NHẬT file này.**

## 1. Trạng thái tổng quan (cập nhật 2026-07-12, phiên bản **v95**)

- **✨ (v95) Tái thiết giao diện responsive + bảng màu mới — toàn bộ frontend, KHÔNG đụng
  logic/backend.** Làm theo 6 bậc trên nhánh riêng `giao-dien-moi` (đã merge `--no-ff` vào
  `main`, xóa nhánh sau khi merge sạch):
  - **Bậc 1 — vỏ layout responsive** (`RoleLayout.jsx`): HS dùng thanh tab cố định đáy màn
    hình dưới `lg` (thay vì menu ẩn tịt không có lối vào); GV/Admin sidebar 3 mốc — đầy đủ
    chữ (`≥1024px`) → thu gọn icon (`768–1023px`, tooltip) → ẩn hẳn + drawer trượt qua nút ☰
    (`<768px`). Thêm dependency `lucide-react` (icon menu). Bề rộng nội dung HS nới
    `1152px→1400px`. Rà thêm & sửa 2 bug vỡ mobile cụ thể phát hiện qua ảnh chụp thật của
    user: vòng tròn SVG kích thước pixel cứng trong lưới 3 cột (`ThongKeTienDo.jsx`) và
    khung sửa câu hỏi ép cứng `min-width:620px` (`QuanLyCauHoi.jsx`).
  - **Bậc 2 — bảng màu mới** (`theme.css`): user tự thiết kế bảng màu đầy đủ (Indigo #3B36CC
    chủ đạo/điều hướng, Cam #FF5A1F CTA, Tím #8B5CF6 điểm nhấn AI, 3 màu trạng thái riêng
    Đúng/Sai/Chưa-chắc, chữ #181430 nền #F6F6FC). Trước khi áp dụng, đã build 1 Artifact
    mockup áp màu lên đúng component thật (nút/badge/nav/chat) + tính tương phản WCAG thật
    (không áng chừng) cho user duyệt — phát hiện chữ trắng trên nút "Chưa chắc" vàng cam chỉ
    đạt 2.2:1 (gần như không đọc được), đã sửa dùng `--color-warning-ink` (#7A4E06, đạt
    8.3:1). Button "primary" (Lưu/Gửi/Đăng nhập...) tách riêng dùng token `--color-cta`,
    không dùng chung `--color-primary` (giờ chỉ còn cho điều hướng/nhận diện) — quyết định
    kiến trúc quan trọng để nút hành động và menu không cùng 1 màu.
  - **Bậc 3 — 6 primitive UI** (`components/ui/*`): bo góc mềm hơn, vùng chạm to hơn cho
    mobile, hover/focus mượt hơn — giữ nguyên props API, không trang nào cần sửa theo.
  - **Bậc 4 — chuẩn hóa modal**: 19 modal/dialog rà lại — thêm giới hạn chiều cao + cuộn
    riêng cho các modal chưa có, bỏ hết `bg-white` hardcode sang token `bg-surface`. Rà ra
    thêm 3 nút tự ghi đè `className` bỏ qua hệ thống `variant` của Button (1 trong đó dính
    đúng lỗi tương phản vàng cam ở Bậc 2 vì không đi qua token trung tâm) — chuyển hết sang
    dùng `variant` chuẩn.
  - **Bậc 5 — rà lưới responsive toàn repo**: quét toàn bộ `grid-cols` cứng, SVG kích thước
    cố định, `min-width` pixel ép cứng, bảng rộng không cuộn ngang — thêm `overflow-x-auto`
    cho 4 bảng còn thiếu (Import tài khoản/học sinh/từ khóa, Kết quả nộp đề thi).
  - **Bậc 6**: xóa `App.css` (rác template Vite, không nơi nào import).
  - Build-test-fix xanh sau mỗi bậc (`eslint` + `vite build`); môi trường dev nhiều lần OOM
    (máy còn <150MB RAM trống) khi build — không phải lỗi code, đã retry qua khi RAM hồi.

## 1b. Trạng thái trước đó (v94)

- **✨ (v94) Admin tự quản lý từ khóa lọc an toàn (3 tầng) — không cần sửa code.**
  - Tận dụng cơ chế cấu hình key-value có sẵn (`CauHinh`) — KHÔNG bảng mới, KHÔNG migration.
    3 khóa mới `tu_khoa_khan_cap`/`tu_khoa_khong_phu_hop`/`tu_khoa_ngoai_pham_vi`, mỗi khóa là
    mảng `{tu_khoa, kich_hoat, la_mac_dinh}`. Chưa từng chỉnh → dùng đúng danh sách mặc định
    trong code làm nền.
  - `core/guard/safety.py`: `kiem_tra_an_toan()` nhận danh sách từ khóa làm tham số (vẫn thuần
    khiết, không đụng DB) + `bo_dau()` chuẩn hóa bỏ dấu (bắt được "tu tu" không dấu) + tự thêm
    ranh giới `\b` cho từ đơn (tránh "kill" khớp nhầm "skill").
  - `admin_service._chuan_hoa_danh_sach_tu_khoa()`: Admin **chỉ tắt được** từ khóa mặc định,
    không xóa được; thiếu 1 từ mặc định trong request → server tự thêm lại ở trạng thái BẬT
    (fail-safe, không để mất nền an toàn dù thao tác nhầm/gọi API tay).
  - API mới `POST /api/admin/tu-khoa-thu` ("thử trước", admin-only) — chạy kiểm tra thật với
    đúng danh sách đang lưu, không tạo phiên học.
  - UI **Admin → Cấu hình → Từ khóa lọc an toàn**: mỗi tầng là accordion (đóng mặc định, đếm
    số lượng) → mở ra có ô tìm kiếm + bảng (Từ khóa/Loại/Trạng thái bật-tắt/Xóa) — tránh rối khi
    danh sách dài. Nút **Import từ file mẫu (.xlsx)** — tải mẫu, chọn file, xem trước (dòng lỗi/
    trùng tự động bỏ qua), xác nhận thêm hàng loạt cho cả 3 tầng cùng lúc (dùng lại thư viện
    `xlsx` + pattern "file mẫu" đã có ở Import tài khoản/Import câu hỏi, không cần API mới).
  - Nối dây `sessions.py` (chat AI) và `tro_giup_service.py` ("Nhờ thầy/cô") dùng danh sách
    admin đang lưu thay vì hard-code. Test mới: bỏ dấu, ghi đè danh sách, ranh giới từ, thêm từ
    mới → chat AI bắt được ngay không cần deploy, không xóa được từ mặc định, tắt mặc định vẫn
    còn trong danh sách. `pytest` 462/462, `ruff`/`eslint`/`vite build` sạch.

- **✨ (v93) Ô chat tự do "Hỏi gia sư" trong Phòng học + nâng cấp an toàn nội dung.**
  - Orchestrator: HS gõ câu hỏi tự do (không phải đáp án) → `y_dinh="giai_thich_ngan"` (có ngữ
    cảnh) hoặc `"dinh_huong"` (rỗng); sai liên tiếp ≥2 lần tự leo cấp gợi ý
    (`NGUONG_SAI_TU_DONG_GOI_Y`); hết gợi ý → `y_dinh="het_goi_y"`, nút gợi ý khoá lại, nút
    "Nhờ thầy/cô" nổi bật (`ring-warning animate-pulse`) — bỏ trùng lặp 2 nút "Nhờ thầy/cô"
    trước đây (mỗi nút 1 vai trò riêng). Thêm `tong_so_lan_sai` (cộng dồn, không reset) +
    `diem_qua_trinh` (chỉ GV/Admin thấy) để kể "câu chuyện hành trình" làm bài, không chỉ
    đúng/sai cuối.
  - **An toàn 2 tầng** (`core/guard/safety.py`): tầng `khan_cap` (tự tử/tự hại/muốn chết — mở
    rộng nhiều từ khoá, ưu tiên cao nhất, thà bắt nhầm còn hơn bỏ sót) và tầng thường
    (`noi_dung_khong_phu_hop`/`ngoai_pham_vi`). CẢ 2 tầng KHÔNG còn chặn bằng HTTP 400 lộ từ
    khoá gốc — luôn trả 200 với câu trả lời thân thiện, chèn thẳng vào luồng chat, hướng HS
    quay lại bài học. Tầng khẩn cấp + không phù hợp vẫn tự động gắn cờ + báo GV (tiêu đề phân
    theo mức độ 🆘/⚠️); tầng ngoài phạm vi thì không gắn cờ. "Nhờ thầy/cô" có nội dung nhạy
    cảm: KHÔNG chặn, luôn tới GV, chỉ gắn cờ khẩn cấp (quyết định sản phẩm — xem mục 4).
  - Cờ theo dõi: thêm gắn cờ thủ công (`thu_cong`) từ trang Theo dõi tiến bộ; rò rỉ đáp án gắn
    cờ theo từng lượt chốt chặn cụ thể (`Flag.turn_id`), không chỉ đếm gộp; thông báo GV bấm
    vào cờ mở thẳng đúng dòng trong "Cờ theo dõi" (`lien_ket_loai="co"`, tái dùng enum `co`).
  - `MixedChatInput.jsx`: hỗ trợ nhập công thức Toán (bảng ký hiệu hiện khi focus), nút gửi nằm
    ngay dưới ô (không bị đẩy khi bảng công thức mở).
  - Test mới: `test_chat_tu_do.py`, `test_gan_co_tu_dong.py` + mở rộng `test_orchestrator.py`,
    `test_tn4pa_tnds.py`, `test_guard.py`, `test_de_bai_ngu_canh.py`. `pytest` 452/452,
    `ruff` sạch, frontend build+lint sạch.

> Lưu ý số phiên bản: 3 mục dưới đây (chuông thông báo GV, chuông thông báo HS, fix mất focus
> ô trả lời) ban đầu dự tính tách thành v89/v90/v91 riêng, nhưng thực tế được gộp chung 1 lần
> "đưa lên github" — tag thật trên GitHub là **v89** cho cả 3. Đánh số lại cho khớp thực tế.

- **🔧 (v90) Giảm chu kỳ polling chuông thông báo 60s → 8s** — `ChuongThongBao.jsx`. HS/GV
  thấy số thông báo mới trong tối đa 8s, không cần F5. Không dùng WebSocket/SSE (đã cân nhắc,
  chọn polling nhanh hơn cho đơn giản/rủi ro thấp, phù hợp quy mô lớp học hiện tại).

- **✨ (v91) Bấm thông báo "Nhiệm vụ mới" / "Đề thi mới" → chuyển thẳng tới đúng mục.**
  - `nhiem_vu_service.py` đã sẵn `lien_ket_loai="nhiem_vu"` từ trước — chỉ nối dây frontend.
  - `de_thi_service.py` (`dat_phat_hanh`) TRƯỚC ĐÂY không hề gửi thông báo khi GV phát hành đề
    — thêm mới: gửi cho đúng tập HS trong phạm vi (tất cả lớp GV hoặc tuỳ chọn đã giao),
    `lien_ket_loai="de_thi"`. Tái dùng `LoaiThongBao.nhiem_vu` (không thêm enum mới) để tránh
    `ALTER TYPE` trên Postgres production.
  - `HocSinhApp.jsx`/`NhiemVu.jsx`/`ThiThu.jsx`: nhận `focusId` từ chuông, cuộn tới + làm nổi
    bật (ring 3s), tương tự cơ chế `focusYc` đã làm ở v89.
  - Test mới `test_phat_hanh_gui_thong_bao` (backend, đã xác nhận fail trên code cũ qua
    `git stash`). `pytest` 422/422.

- **✨ (v92) Trang chủ HS luôn hiện 2 thẻ "Nhận xét"/"Thầy·cô đã trả lời"** (trước đây ẩn hẳn
  khi rỗng) — rỗng thì hiện dòng trạng thái rõ ràng thay vì biến mất. **Phân trang**:
  `ChonBai.jsx` (chọn bài, 20/trang), `NhiemVu.jsx` (10/trang), `ThiThu.jsx` danh sách đề
  (10/trang) — đổi bộ lọc tự quay về trang 1; hiệu ứng focus-từ-thông-báo (v91) tự tính đúng
  trang chứa mục cần cuộn tới.

- **✨ TÍNH NĂNG (v89): bấm thông báo "Học sinh nhờ trợ giúp" (bên GV) → chuyển
  thẳng đến đúng yêu cầu ở "Hỗ trợ học sinh".** Đối xứng với tính năng HS bấm thông báo "Thầy/
  cô trả lời" (mục kế dưới). Vì cần dùng chung cho cả 2 vai trò, đã TỔNG QUÁT HÓA cơ chế thay
  vì làm riêng: `ChuongThongBao.jsx` đổi từ prop `onMoPhongHoc` (chỉ HS) sang `onMoLienKet(tb)`
  tổng quát — mỗi app (HS/GV) tự quyết định điều hướng theo `tb.lien_ket_loai`, không cần
  `ChuongThongBao` biết trước có bao nhiêu loại liên kết. `RoleLayout.jsx` xuyên prop này qua
  CẢ `HSLayout` LẪN `SidebarLayout` (mới thêm, GV/Admin dùng — Admin không
  truyền `onMoLienKet` nên hành vi giữ nguyên, không đổi).
  - **Backend** (`tro_giup_service.tao_yeu_cau()`): thông báo cho GV trước đây trỏ
    `lien_ket_loai="session", lien_ket_id=session_id` — ĐỔI sang
    `lien_ket_loai="yeu_cau_tro_giup", lien_ket_id=yc.id` để trỏ ĐÚNG yêu cầu cụ thể (1 session
    có thể có nhiều yêu cầu "Nhờ thầy/cô" nếu HS hỏi nhiều lần, trỏ theo session sẽ mơ hồ).
    Thông báo "Thầy/cô trả lời" (phía HS) giữ nguyên `lien_ket_loai="session"` — không đổi.
  - **`HoTroHocSinh.jsx`**: nhận prop `focusYc` (`{id, ts}`) — tự tìm đúng yêu cầu trong danh
    sách (kể cả phải đổi trang phân trang giữa "chờ xử lý"/"đã trả lời"), cuộn tới
    (`scrollIntoView`) và làm nổi bật viền 3 giây (`ring-2 ring-primary`). `ts` đổi mỗi lần
    bấm để ép hiệu ứng chạy lại kể cả bấm trùng đúng yêu cầu đã focus trước đó.
  - **`GiaoVienApp.jsx`**: state `focusYc`, hàm `moTuThongBao(tb)` chỉ xử lý
    `lien_ket_loai === "yeu_cau_tro_giup"` (bỏ qua loại khác), điều hướng sang trang `ho_tro`.
  - Test backend: `tests/test_tro_giup.py` (6 test, không assert trực tiếp `lien_ket_*` nên
    không cần sửa) vẫn xanh sau khi đổi — xác nhận không phá luồng "Nhờ thầy/cô" hiện có.
  - `eslint` 0 lỗi, `npm run build` OK, `pytest` 421/421. **CHƯA kiểm thử qua trình duyệt thật**
    (môi trường không có công cụ điều khiển trình duyệt) — như mục dưới, đề nghị tự test tay:
    GV xem chuông thông báo "Học sinh nhờ trợ giúp", bấm vào, xác nhận nhảy đúng trang + đúng
    thẻ yêu cầu + tự cuộn tới + có viền nổi bật tạm thời.

- **✨ TÍNH NĂNG (v89): bấm thông báo "Thầy/cô trả lời" → chuyển thẳng vào phòng học.**
  Trước đây thông báo chỉ hiện nội dung, không click được. Backend đã sẵn đủ dữ liệu
  (`lien_ket_loai="session"`, `lien_ket_id=session_id`, gắn từ v-trước ở
  `tro_giup_service.tra_loi()`) — KHÔNG cần sửa backend, chỉ nối dây phần frontend.
  - `ChuongThongBao.jsx` nhận prop `onMoPhongHoc(sessionId)` — bấm vào thông báo có
    `lien_ket_loai === "session"` sẽ gọi callback này (kèm nhãn "→ Vào phòng học" gợi ý bấm
    được); `RoleLayout.jsx` xuyên prop này qua `ProfileMenu`/`UserMenu` (chỉ HS dùng, GV/Admin
    không truyền nên hành vi cũ giữ nguyên).
  - `PhongHoc.jsx` thêm prop `onSid` — báo lên `HocSinhApp` biết session ĐANG active trong
    phòng học (kể cả khi mở bài mới qua `problemId`, chỉ có sessionId thật sau khi tạo phiên).
  - `HocSinhApp.jsx` — hàm `moTuThongBao(sessionId)` xử lý đúng 2 tình huống theo yêu cầu:
    (1) HS đang ở SẴN đúng bài đó → `window.location.reload()` (đúng nghĩa đen "tải lại
    trang" — vì `phongHoc` đã lưu `sessionStorage` nên reload xong quay lại đúng bài, tải
    turns mới có câu trả lời); (2) HS đang làm dở BÀI KHÁC → hỏi xác nhận qua `useConfirm()`
    trước khi rời; (3) HS không ở phòng học nào → chuyển thẳng, không cần hỏi.
  - Phát hiện + xử lý thêm 1 rủi ro không nằm trong yêu cầu gốc: nếu HS đang ở phòng học A rồi
    chuyển THẲNG sang phòng học B (không rời trang giữa chừng), `PhongHoc` không unmount hoàn
    toàn (chỉ đổi prop) → có thể sót state UI phụ (hộp "nhờ thầy/cô" đang mở, ảnh đang zoom)
    của bài cũ. Thêm `key={phongHoc.sessionId || phongHoc.problemId}` để ép mount lại sạch —
    không ảnh hưởng các luồng cũ (trước đây luôn đổi trang nên vốn đã mount lại tự nhiên).
  - **CHƯA kiểm thử qua trình duyệt thật** (môi trường này không có công cụ điều khiển
    trình duyệt) — đã xác minh bằng đọc mã nguồn đầu-cuối (backend trả đúng field → frontend
    dùng đúng field → logic điều hướng đúng theo yêu cầu), `eslint` 0 lỗi, `npm run build`
    thành công. Đề nghị tự kiểm tra tay trước khi coi là xong: đăng nhập 2 tab (GV + HS), HS
    nhờ trợ giúp, GV trả lời, HS bấm chuông thông báo — thử cả 3 tình huống điều hướng.

- **🐞 FIX (v89): GV gõ vào ô "trả lời" ở "Hỗ trợ học sinh" cứ 1 ký tự lại mất focus.**
  Nguyên nhân: `CardYeuCau` (thẻ hiển thị 1 yêu cầu trợ giúp, gồm cả form trả lời) được định
  nghĩa BÊN TRONG thân hàm render của `HoTroHocSinh` — cùng loại lỗi với `KhoaApi` đã sửa ở
  v88 (`CauHinh.jsx`) nhưng lần này KHÔNG bị `eslint react-hooks/static-components` bắt được
  (rule không phát hiện khi component dùng qua `.map()` thay vì gọi lặp lại trực tiếp trong
  JSX). Mỗi lần gõ 1 ký tự → `setText` đổi state cha → `CardYeuCau` bị coi là 1 KIỂU COMPONENT
  MỚI ở lần render kế → React unmount/remount toàn bộ cây con bên trong (kể cả `<textarea>`
  của `MixedChatInput`) → mất focus, chỉ gõ được đúng 1 ký tự rồi bật ra ngoài.
  - Sửa: chuyển `CardYeuCau` ra module-level (ngoài `HoTroHocSinh`), nhận toàn bộ state/hàm
    cần thiết qua props (`dangXoa`, `onXoa`, `traLoiId`, `text`, `setText`, `loi`, `dangGui`,
    `onMoTraLoi`, `onHuyTraLoi`, `onGui`) thay vì đọc từ closure.
  - Đã rà toàn bộ `frontend/src` tìm thêm pattern "component định nghĩa lồng trong component
    khác" tương tự — không còn chỗ nào khác (chỉ `HoTroHocSinh.jsx` là trường hợp sót lại,
    eslint không bắt được do dùng qua `.map()`).
  - `eslint .` (toàn bộ) vẫn 0 lỗi, `npm run build` OK. Không có backend nào bị ảnh hưởng.

- **🧹 SỬA TOÀN BỘ REVIEW.md (v88, nối tiếp v87): review 5 bước → sửa hết trừ rủi ro đã chấp
  nhận.** User yêu cầu review toàn diện dự án theo quy trình 5 bước (hiểu dự án → kiểm tra
  tĩnh → chạy thử thực tế → bảo mật/cấu hình → báo cáo phân loại 🔴/🟡/🟢), tạo `REVIEW.md`,
  sau đó yêu cầu sửa hết (trừ lỗ hổng `xlsx` — chấp nhận rủi ro vì không có bản vá npm).
  - **Kết quả review**: 0 lỗi Critical, 6 nhóm Warning, 12 nhóm Minor. Điểm đáng chú ý nhất:
    lỗ hổng `ecdsa` (transitive qua `python-jose`) và thiếu `.catch()` ở 2 chỗ khiến trang có
    thể kẹt vĩnh viễn khi API lỗi.
  - **Backend đã sửa**: đổi `python-jose` → `PyJWT` (loại bỏ hẳn `ecdsa` khỏi dependency tree,
    `pip-audit` từ 2 lỗ hổng → 0); phát hiện thêm lúc đổi: PyJWT cảnh báo secret mẫu quá ngắn
    (<32 ký tự) mà jose cũ không cảnh báo — kéo dài secret mẫu, giữ cả giá trị cũ trong danh
    sách "không an toàn" để không phá fail-fast production; sửa 78 chỗ `raise ... from e`
    thiếu (B904, đa số áp dụng qua script có kiểm tra diff từng dòng, phần còn lại sửa tay);
    dọn 10 style nits `ruff` (SIM/C4/B905), xóa thư mục `api/routes/` rỗng, nâng cấp `pip`.
  - **Frontend đã sửa (eslint 20 lỗi → 0)**: thêm `.catch()` thiếu ở `FormulaEditor.jsx` (tải
    MathLive lỗi giờ có nút "Thử lại") và `CauHinh.jsx` (tải cấu hình lỗi không còn kẹt vĩnh
    viễn); chuyển `valueRef.current = value` (MixedChatInput.jsx) và component `KhoaApi`
    (CauHinh.jsx) ra khỏi thân render; `Date.now()` (TrangChu.jsx) chuyển vào effect (phát
    hiện `useMemo` KHÔNG đủ để qua rule "impure" mới của react-hooks, phải dùng effect thật);
    sửa 6+1 chỗ `set-state-in-effect`; gom 3 hàm (`kiemTraDapAnTLN`, `dungDangOptions`,
    `chuanHoaSteps`) từng trùng lặp/mixed-export giữa `QuanLyCauHoi.jsx` và
    `ImportCauHoiDialog.jsx` về `utils/cauHoi.js` dùng chung; tách `useConfirm` khỏi
    `ConfirmDialog.jsx` sang file riêng (không cần sửa 11 nơi đang dùng vì import qua barrel
    `components/ui/index.js`); dọn unused import/dead code, sửa key trùng trong object literal.
  - **Chủ động giữ nguyên có cân nhắc** (ghi rõ lý do trong `REVIEW.md`, không phải bỏ sót):
    lỗ hổng `xlsx` (theo yêu cầu), bundle chưa code-split thêm (rủi ro Suspense/regression >
    lợi ích, chỉ là gợi ý hiệu năng không phải lỗi), `SAWarning` khóa ngoại vòng lúc test
    teardown (sửa đòi hỏi đổi định nghĩa FK của 2 bảng lõi `users`/`lop`, không tương xứng).
  - **Kiểm chứng**: backend 421/421 test pass, `ruff` 0 lỗi, `pip-audit` 0 lỗ hổng; frontend
    eslint 0 lỗi, build OK; xác nhận bằng dev server thật — đăng nhập + gọi API có token qua
    PyJWT mới hoạt động đúng (thay đổi rủi ro cao nhất trong đợt sửa này).
- **🔍 RÀ SOÁT TOÀN DIỆN (v87, nối tiếp v86): chuyển đổi LaTeX→SymPy + CAS chấm đáp án HS.**
  User yêu cầu nghiêm túc rà soát để không phải vá đi vá lại nhiều lần. Thay vì đợi lỗi tiếp
  theo tự lộ ra, đã test CÓ HỆ THỐNG toàn bộ ký hiệu trong bảng công thức thật (`MathPalette.jsx`
  — đúng bộ HS/GV dùng để nhập, không phải LaTeX tùy ý) qua thẳng parser antlr — phát hiện 7 lỗ
  hổng cùng loại với v86 (parser hiểu SAI ÂM THẦM, không báo lỗi):
  1. **🔴 NGHIÊM TRỌNG NHẤT — Số phức: "i" không bao giờ được hiểu là đơn vị ảo.** `3+4i` (HS
     gõ) parse thành ký hiệu tự do "i" nhân vào, KHÔNG PHẢI `I` (đơn vị ảo SymPy) — so với đáp
     án chuẩn lưu dạng `3+4*I` sẽ KHÔNG BAO GIỜ khớp dù đúng giá trị. Ảnh hưởng CẢ CHUYÊN ĐỀ Số
     phức (chủ đề chính thức lớp 12), không phải 1 ký hiệu lẻ.
  2. Giá trị tuyệt đối/môđun `\left|x\right|` (nút "|x|"/"|z|") — LỖI THẲNG dù là cú pháp LaTeX
     hợp lệ (antlr đòi `\rangle`). Ảnh hưởng cả môđun số phức `|3+4i|`.
  3. Tổ hợp `C_n^k` / chỉnh hợp `A_n^k` (nút "Cₙᵏ"/"Aₙᵏ", ký hiệu SGK VN) — bị hiểu thành "C"/"A"
     (ký hiệu tự do) lũy thừa thay vì `binomial(n,k)`/`n!/(n-k)!`, ÂM THẦM SAI. Chủ đề Tổ hợp -
     Xác suất rất phổ biến trong đề thi.
  4. Ký hiệu độ `^{\circ}` (nút "°") — `180^{\circ}` bị hiểu thành `180` lũy thừa ký hiệu tự do
     "circ" thay vì giữ nguyên `180`.
  5. `\ne` (nút "≠") — antlr chỉ hiểu `\neq` (có "q"), `\ne` bị hiểu thành ký hiệu tự do "ne".
  6. `\pm`/`\mp`/`\approx` (nút "±"/"≈") — không đại diện 1 giá trị xác định NHƯNG antlr âm thầm
     biến thành ký hiệu tự do nhân vào thay vì báo lỗi → **đổi chiến lược**: chủ động báo lỗi rõ
     ràng (an toàn hơn để lọt qua so sánh sai không ai biết).
  - **Sửa** (`backend/app/core/matching/latex.py`): dồn TOÀN BỘ chuẩn hóa LaTeX (kể cả
    `\star`/`\ast`→`\cdot` trước đây nằm riêng ở `cas.py`) về 1 module DUY NHẤT — để ô "chuyển
    đổi công thức" của GV và CAS chấm bài HS LUÔN đồng bộ, tránh vá 1 chỗ mà chỗ kia vẫn lỗi
    (đúng yêu cầu "không phát sinh lỗi mới" của user). Xóa `_chuan_hoa_latex()` trùng lặp khỏi
    `cas.py`.
  - 10 test mới `test_latex.py`, xác nhận bằng `git stash`: **10/10 test đều fail trên code cũ**
    (kể cả ca số phức nghiêm trọng nhất) — đúng nguyên nhân gốc, không phải false positive.
  - Tự phát hiện + sửa 1 lỗi trong chính bản vá: kiểm tra `\pm` ban đầu dùng substring thô, sẽ
    báo NHẦM cả `\pmod` (chứa "\pm" làm tiền tố) — đổi sang regex có ranh giới từ trước khi
    commit, thêm test khóa lại (`test_pm_khong_bao_nham_pmod`).
  - **Đã cân nhắc và CHỦ ĐỘNG KHÔNG sửa** (rủi ro thấp — không phải định dạng đáp án cuối hợp
    lệ trong thực tế): `\vec{v}` (vectơ không phải "1 giá trị"), `P(A \mid B)` (xác suất điều
    kiện không dùng làm đáp án cuối, HS gõ số thập phân trực tiếp). Ghi lại ở đây để không cần
    rà soát lại nếu sau này có báo cáo — đã xem xét, quyết định có chủ đích.
  - 421/421 test xanh (+10 test mới). Không đổi schema DB.


- Backend (FastAPI + SQLAlchemy, SQLite `dev.db` / đích PostgreSQL) + Frontend (React + Vite +
  Tailwind) chạy end-to-end. **411/411 test backend xanh** (`pytest`, +3 test mới).
- **🐞 FIX (v86): ô chuyển đổi LaTeX→SymPy (v79) báo lỗi "Không thể parse LaTeX '\sqrt2'".**
  Nguyên nhân: LaTeX chuẩn cho phép bỏ ngoặc nhọn quanh `\sqrt` khi đối số chỉ đúng 1 "token"
  (1 ký tự hoặc 1 lệnh `\ten` — vd `\sqrt2`, `\sqrt\alpha` đều hợp lệ, hiển thị đúng khi biên
  dịch LaTeX thật), nhưng parser `sympy.parsing.latex` (backend antlr) lại BẮT BUỘC phải có
  `{}`. Nghiêm trọng hơn: phát hiện thêm trường hợp KHÔNG báo lỗi mà ÂM THẦM SAI — `2\sqrt3`
  (thiếu ngoặc, đứng sau số khác) bị parser cắt cụt thành `2`, mất hẳn phần căn, không ai biết.
  - **Sửa** (`backend/app/core/matching/latex.py`): thêm bước tiền xử lý `_them_ngoac_sqrt()`
    tự bổ sung `{}` quanh đối số `\sqrt`/`\sqrt[n]` bị thiếu ngoặc TRƯỚC khi đưa cho parser (chỉ
    khi chưa có ngoặc sẵn, không đụng input đã đúng). Hàm này dùng chung cho cả ô chuyển đổi của
    GV (`/api/problems/latex-sang-sympy`) LẪN việc CAS chấm đáp án học sinh
    (`core/matching/cas.py._parse_an_toan`) — sửa 1 chỗ, cả 2 luồng đều được lợi (HS gõ `\sqrt2`
    trong ô đáp án TLN từ nay cũng chấm đúng thay vì trước đây có thể bị chấm sai/báo lỗi).
  - Test mới `test_latex.py` (3 case): thiếu ngoặc đơn giản, thiếu ngoặc kèm bậc `[n]`, và hồi
    quy khóa lại đúng-không-còn-âm-thầm-sai cho `2\sqrt3`. Xác nhận bằng `git stash`: cả 3 test
    thất bại trên code cũ (kể cả case âm thầm sai, không chỉ case báo lỗi thẳng).
  - Không đổi schema DB.
- **🏗️ GIẢI PHÁP TRIỆT ĐỂ (v85, nối tiếp v84): chặn tận gốc nhóm lỗi "AI sinh JSON hỏng" thay vì
  vá từng ca một.** User phản ánh: dù v84 đã vá lỗi escape LaTeX, "thỉnh thoảng AI sinh câu hỏi/
  tạo bước gợi ý lại phát sinh lỗi MỚI" — phân tích nghiêm túc (không code trước) xác định gốc rễ:
  kiến trúc cũ để AI "tự viết tay" JSON dưới dạng văn bản tự do rồi code ĐOÁN & VÁ bằng regex sau
  khi nhận về — cách này về bản chất không triệt để vì AI không được RÀNG BUỘC phải đúng cú pháp,
  chỉ được "nhắc" bằng lời; mỗi kiểu lệch mới (escape sai, phẩy thừa, thiếu khóa...) lại phải vá
  thêm một lần, không gian lỗi gần như vô hạn. Đã trình bày phân tích + phương án cho user, được
  chọn triển khai đủ 3 lớp:
  1. **Lớp chính — Structured Output (Gemini `responseSchema`)**: ép Gemini CHỈ SINH ĐƯỢC JSON
     đúng cấu trúc ngay ở tầng giải mã token (constrained decoding) — loại tận gốc CẢ NHÓM lỗi
     "JSON không hợp lệ", không cần đoán trước từng kiểu lỗi để vá nữa. Thêm `schema_sinh_cau_hoi()`
     / `schema_doc_de_tu_anh()` (`app/llm/prompts.py`, đặt cạnh các `_MAU_*` mà chúng mô tả) —
     schema dựng ĐỘNG theo `loai_cau` (TN4PA/TNDS/TLN có `meta` khác nhau). Wire vào
     `GeminiLLMClient._call`/`_call_voi_anh` (tham số `response_schema`, tự set
     `response_mime_type="application/json"`) cho cả 3 luồng: `sinh_cau_hoi`, `tao_buoc_goi_y`,
     `doc_de_tu_anh`. Anthropic/OpenAI chưa hỗ trợ (không phải provider khuyến nghị) — vẫn dùng
     đường vá regex hiện có, cũng là lớp dự phòng cho chính Gemini nếu vì lý do gì đó schema lỗi.
  2. **Lớp 2 — Retry có phản hồi lỗi cụ thể**: `_goi_va_parse`/`_doc_de_tu_anh_qua_call` giờ nối
     thêm nguyên văn lỗi parse lần trước vào prompt của lần thử lại kế tiếp (AI tự sửa đúng chỗ
     thay vì lặp lại y hệt sai lầm cũ) — CHỈ áp dụng khi lỗi là JSON hỏng (có phản hồi để đọc),
     KHÔNG áp dụng khi lỗi mạng/API (phản hồi không có ý nghĩa gì để sửa).
  3. **Lớp 3 — Log JSON thô khi thất bại**: mỗi lần parse lỗi, ghi `logger.warning` kèm JSON thô
     (rút gọn 2000 ký tự) — nếu tương lai vẫn có kiểu lỗi mới lọt qua (vd provider khác, ảnh lạ),
     chẩn đoán được từ dữ liệu thật thay vì đoán mù từ 1 dòng thông báo lỗi ngắn như các lần trước.
  - 10 test mới: cấu trúc schema đúng theo từng loại câu, `GeminiLLMClient` truyền đúng
    `response_schema`/`response_mime_type`, retry nối đúng ghi chú lỗi (và KHÔNG nối khi lỗi
    mạng), log JSON thô xuất hiện khi thất bại.
  - Không đổi schema DB, không đổi hành vi StubLLMClient/Anthropic/OpenAI.
- **🐞 FIX (v84): AI "Tạo bước và gợi ý" (và "Sinh câu hỏi") lỗi ngẫu nhiên với LaTeX — báo cáo
  qua TNDS sinh từ ảnh dán, thông báo "LLM trả JSON không hợp lệ: Invalid \escape: line 8 column
  61".** Nguyên nhân gốc: `_va_escape_json()` (`backend/app/llm/client.py`) vá backslash đơn của
  LaTeX cho hợp lệ JSON, nhưng coi `\b \f \n \r \t` là "escape JSON hợp lệ sẵn" nên KHÔNG vá —
  trong khi b/f/n/r/t lại chính là chữ cái mở đầu của rất nhiều lệnh LaTeX phổ biến (`\begin`,
  `\bar`, `\frac`, `\forall`, `\neq`, `\nabla`, `\right`, `\tan`, `\theta`, `\to`...). Kết quả: câu
  hỏi có các lệnh này hỏng JSON thầm lặng (không lỗi nhưng nội dung sai), hoặc vỡ hẳn ("Invalid
  \escape") khi đứng cạnh dấu `\\` LaTeX thật (vd `\begin{cases}...\\...\end{cases}`, phổ biến khi
  AI đọc ảnh đề có hệ phương trình/TNDS nhiều ý). Đã kiểm chứng bằng `git stash`: test mới thất bại
  trên code cũ với ĐÚNG dạng lỗi user báo cáo, xác nhận đúng nguyên nhân gốc.
  - **Sửa**: viết lại `_va_escape_json()` — chỉ tin `\"` và `\\` (cặp backslash đã tự escape đúng)
    và `\uXXXX` là escape JSON thật; MỌI backslash đơn khác đều nhân đôi. Xử lý theo CẶP ký tự
    (`re.sub` với callback, không phải lookahead đơn ký tự) để không tách đôi 1 cặp `\\` hợp lệ.
    Hàm dùng chung cho cả `_parse_json_cau_hoi` (sinh câu hỏi/tạo bước gợi ý) lẫn
    `_parse_phan_tich`/`_parse_json_doc_de_tu_anh` — sửa 1 chỗ, khỏi ảnh hưởng cả 3 luồng.
  - Test mới `test_parse_json_latex_chu_b_f_n_r_t` (`test_question_gen.py`) khóa các lệnh LaTeX
    hay gặp (`\frac \to \neq \begin{cases}...\\...\end{cases}`) parse đúng, không vỡ JSON.
  - Không đổi schema DB, không đổi hành vi khi JSON không có LaTeX đặc biệt.
- **✅ Trang bảo trì — logo + xuống hàng (v82–v83, nối tiếp v81):** thêm logo MathTutor
  (`/logomt.png`, dùng chung ảnh với trang đăng nhập) phía trên câu thông báo; sửa `<p>` thiếu
  `whitespace-pre-wrap` khiến Enter trong ô nhập nội dung ở Admin không xuống hàng khi hiển thị
  cho người dùng ngoài (ô textarea nhập vẫn nhận Enter bình thường — chỉ thiếu phần hiển thị).
- **✅ Chế độ bảo trì — admin tự sửa nội dung thông báo (v81, nối tiếp v80):** thêm khóa cấu hình
  `bao_tri_noi_dung` (chuỗi, mặc định câu gốc) — sửa được ngay trong Admin > Cấu hình > "Chế độ
  bảo trì" (đổi tên từ "Sản phẩm đang hoàn thiện" cho ngắn gọn), qua ô textarea bên dưới mã xem
  trước. `GET /api/trang-thai-bao-tri` trả thêm `noi_dung`; `App.jsx` hiển thị đúng nội dung admin
  đã lưu (fallback về câu mặc định nếu rỗng/lỗi mạng — vẫn fail-open như thiết kế gốc). Không cần
  migration DB (vẫn dùng bảng `cau_hinh` key-value có sẵn). Test mới khóa nội dung tùy chỉnh trả
  đúng qua API.
- **✅ Trang "Sản phẩm đang hoàn thiện" — chặn người ngoài xem trước khi ra mắt chính thức (v80):**
  domain `mathtutor.pro.vn` đã trỏ xong về Render (custom domain qua 2 bản ghi A tại nhà cung cấp
  BKNS, không cần CNAME/CORS_EXTRA_ORIGINS gì thêm — kiến trúc gọi cùng-origin qua Render proxy).
  Chủ dự án muốn: (1) người ngoài vào domain chỉ thấy 1 dòng thông báo, (2) bản thân vẫn test được
  bình thường mọi vai trò GV/HS/admin, (3) bật/tắt được bất kỳ lúc nào không cần deploy lại.
  - **Thiết kế: chặn ở TẦNG HIỂN THỊ frontend, không chặn API** — mọi endpoint nghiệp vụ đã có JWT
    nên khách vãng lai không làm được gì kể cả không có cổng này; đây thuần là lớp trình bày.
  - **Tái dùng CƠ CHẾ CẤU HÌNH key-value có sẵn** (`cau_hinh` table, `CAU_HINH_MAC_DINH` trong
    `admin_service.py`) — thêm 2 khóa mới `bao_tri_bat` (bool) và `bao_tri_ma` (chuỗi bí mật),
    **không cần migration DB nào** (đúng ràng buộc "không ảnh hưởng dữ liệu thật trên Render").
    Bật/tắt lưu ngay vào DB qua endpoint `PATCH /api/admin/config` đã có sẵn → thỏa yêu cầu (3).
  - **Backend**: `GET /api/trang-thai-bao-tri` (công khai, không cần đăng nhập) — trả
    `{bao_tri, hop_le}`; `hop_le` = true khi query param `ma` khớp `bao_tri_ma` trong Cấu hình.
    KHÔNG bao giờ trả nguyên văn mã ra response (tránh lộ mã xem trước).
  - **Frontend** (`App.jsx`): gọi endpoint trên khi mở trang; nếu `hop_le` → lưu cờ vào
    `localStorage` (`mt_xem_truoc`) rồi dọn `?ma=` khỏi URL — từ đó trình duyệt đó luôn vào bình
    thường (đăng nhập GV/HS/admin không bị ảnh hưởng, vì cổng chỉ can thiệp việc render component
    nào, không đụng auth). Nếu `bao_tri=true` và chưa có cờ bypass → hiện `TrangBaoTri` (trang
    trắng, 1 dòng chữ lớn giữa màn hình, đúng nguyên văn yêu cầu). Lỗi mạng khi kiểm tra → fail-open
    (hiện app bình thường), tránh tự khóa nhầm chính mình.
  - **Admin UI** (`CauHinh.jsx`): thêm Card "Sản phẩm đang hoàn thiện" ở đầu trang — checkbox bật/
    tắt + ô sửa mã xem trước + hiện sẵn URL đầy đủ để copy (`<origin>/?ma=<mã>`).
  - Test mới `test_bao_tri.py` (5 case): mặc định tắt, bật không có mã, mã sai, mã đúng, không lộ
    mã qua response khi sai.
  - Bypass URL sau khi bật cho chủ dự án: `https://mathtutor.pro.vn/?ma=xem-truoc-mt79` (mã mặc
    định `xem-truoc-mt79`, đổi được bất kỳ lúc nào qua Admin > Cấu hình). Mở URL này 1 lần trên
    trình duyệt của mình TRƯỚC KHI bật `bao_tri_bat`, hoặc bất kỳ lúc nào sau đó vẫn vào lại được
    qua chính URL này.
- **✅ Thay "Bảng cú pháp SymPy" bằng ô chuyển đổi LaTeX→SymPy tương tác (v79):** trang Xem/Sửa
  câu hỏi (GV) — sidebar phải trước đây có bảng tra cứu TĨNH (vd "$\sqrt x$ → sqrt(x)"), GV phải
  tự đối chiếu bằng mắt. Thay bằng công cụ chuyển đổi TRỰC TIẾP.
  - **Backend**: hàm CAS thuần có sẵn `latex_sang_sympy()` (`core/matching/latex.py`, dùng
    `sympy.parsing.latex.parse_latex`) — TRƯỚC ĐÓ chưa có endpoint nào expose ra ngoài. Thêm
    `POST /api/problems/latex-sang-sympy` (chỉ GV/Admin, giống pattern `/ve-do-thi`/`/ve-bbt`).
  - **Frontend**: component mới `ChuyenDoiLatexSympy` (thay `BangCuPhapSymPy` — đã XÓA hẳn cùng
    `NHOM_SYMPY`, không để lại code chết) — tái dùng NGUYÊN VẸN `FormulaEditor` (MathLive
    math-field) + `MathPalette`, đúng 2 component HS đã dùng để nhập đáp án TLN trong phòng học
    (đúng yêu cầu "giống như phần nhập kết quả trong phòng học của học sinh"). GV gõ trực tiếp
    HOẶC bấm bảng công thức → hiện đồng thời 2 ô: công thức Toán (KaTeX, đối chiếu đã nhập đúng
    ý) + cú pháp SymPy (debounce 500ms gọi API, có nút "Sao chép" để dán qua ô "Biểu thức kết
    quả"). Bảng công thức `BangCongThuc` (TexField, dùng cho đề bài/gợi ý) giữ nguyên không đổi.
  - Sửa 1 lỗi lint mới phát sinh khi viết effect debounce (setState đồng bộ đầu effect —
    `react-hooks/set-state-in-effect`) bằng cách dời state-update vào trong callback bất đồng bộ
    (`setTimeout`/promise) — không thêm nợ kỹ thuật mới, giữ nguyên 5 lỗi lint có sẵn của file.
  - Test mới `test_ve_hinh.py`: chuyển đổi đúng vài công thức hay gặp, HS bị chặn 403, LaTeX hỏng
    → 400, rỗng → 422.
  - Không đổi schema DB.
  - **User test tay trên UI thật, phát hiện + đã sửa 2 vấn đề:**
    1. Bấm nút bảng công thức có Ô TRỐNG (vd "logₐ" chèn `\log_{\placeholder{}}(\placeholder{})`)
       nhưng chưa điền — gửi dịch ngay sẽ luôn lỗi khó hiểu. Frontend giờ tự phát hiện
       `\placeholder{}` còn sót trong latex TRƯỚC khi gọi API, hiện cảnh báo nhẹ "⚠ Còn ô trống
       (□) chưa điền" thay vì gọi API rồi hiện lỗi kỹ thuật.
    2. Thông báo lỗi backend (`latex_sang_sympy`) từng lộ nguyên văn dump lỗi ANTLR (dài, tiếng
       Anh, có dấu `^^^` chỉ vị trí) — cắt bỏ phần dump kỹ thuật khỏi message hiển thị (vẫn giữ
       `raise ... from e` để debug qua traceback khi cần). Đã xác nhận hàm này còn dùng chung cho
       CAS chấm đáp án HS (`core/matching/cas.py`) — an toàn vì message ValueError ở đó bị nuốt
       (không hiện cho HS), chỉ ảnh hưởng phần hiển thị cho GV ở công cụ mới. Test mới khóa: lỗi
       không còn chứa `^^^`, độ dài < 100 ký tự.
    3. Thêm nút ✕ nhỏ trong ô nhập công thức để xóa nhanh (chỉ hiện khi có nội dung).
- **✅ 2 sửa UI nhỏ cho GV (v78):**
  1. **Ô dán ảnh đề (Ctrl+V) — `ODanAnh` (`AISinhCauHoi.jsx`)**: 2 nút "🔎 Nhận dạng từ ảnh" /
     "Xóa ảnh" trước xếp ngang cạnh ảnh preview (`flex items-start`), ảnh lớn/rộng đẩy nút tràn
     ra ngoài hoặc bị khuất. Đổi thành ảnh trên, 2 nút xuống hàng dưới (`flex-col`) + thêm
     `max-w-full` cho ảnh (trước chỉ giới hạn `max-h-40`, chưa giới hạn chiều rộng). Xác nhận
     với user: đổi CSS hiển thị này KHÔNG ảnh hưởng dữ liệu `anh_base64` gửi AI nhận dạng — ảnh
     đọc từ `FileReader` lúc dán, tách biệt hoàn toàn khỏi cách `<img>` được render.
  2. **Ô xem trước trong `TexField` (dùng chung cho mọi ô nhiều dòng, gồm "Lời giải chi tiết")
     mất dấu xuống dòng**: user báo "gõ Enter trong Lời giải chi tiết không có tác dụng". Nguyên
     nhân KHÔNG phải do LaTeX (lệnh `\\`/`\newline` chỉ có tác dụng TRONG `$...$`, không áp dụng
     cho chữ thường) — dữ liệu Enter đã lưu đúng, nhưng ô preview nhỏ dưới textarea (thẻ `<p>`)
     thiếu CSS `white-space: pre-wrap` nên xuống dòng bị collapse khi hiển thị, khiến user tưởng
     "không có tác dụng". Thêm `whitespace-pre-wrap` — sửa 1 chỗ, áp dụng cho MỌI ô nhiều dòng
     (đề bài/mô tả bước/gợi ý/lời giải chi tiết...), không chỉ riêng lời giải chi tiết. Màn
     "Xem lại bài" của HS đã đúng từ trước (đã thêm `whitespace-pre-wrap` khi làm tính năng ở
     v76), chỉ preview lúc GV đang sửa là thiếu.
  - Không đổi backend/schema DB.
- **✅ AI tự sinh "Lời giải chi tiết" cho GV sửa (v77, nối tiếp v76):** v76 mới thêm được
  Ô/cấu hình "Lời giải chi tiết" do GV TỰ GÕ; lượt này bắt AI (cả "Sinh hàng loạt" lẫn "Tạo
  bước và gợi ý") TỰ SINH nội dung này luôn, đổ sẵn vào ô để GV chỉ cần sửa thay vì viết từ đầu.
  - `app/llm/prompts.py`: thêm khóa `"loi_giai_chi_tiet"` vào cả 3 schema mẫu
    (`_MAU_TN4PA`/`_MAU_TNDS`/`_MAU_TLN`, dùng chung cho cả 2 luồng AI) + chỉ thị rõ trong
    `SYSTEM_SINH_CAU_HOI` và `SYSTEM_TAO_BUOC_GOI_Y`: đây là **lời giải ĐẦY ĐỦ dạng văn xuôi**,
    KHÁC HẲN `danh_sach_goi_y` (chỉ là các ý gợi mở ngắn cho gia sư Socratic lúc HS đang học).
  - Không cần sửa `app/llm/client.py` cho 3 provider thật (Gemini/Anthropic/OpenAI) — hàm parse
    JSON dùng chung `_parse_json_cau_hoi()` vốn đã tổng quát (giữ nguyên mọi khóa AI trả về,
    không lọc theo whitelist), nên chỉ cần đổi prompt là đủ. Có cập nhật `StubLLMClient` (mẫu
    tất định dùng khi test/demo không có API key) để cũng trả `loi_giai_chi_tiet` mẫu — đồng bộ
    hành vi giữa Stub và AI thật.
  - `app/llm/question_gen.py` — `validate_cau_hoi()` thêm cảnh báo (KHÔNG chặn lưu) nếu AI lỡ
    thiếu trường này, đúng tinh thần cảnh báo mềm sẵn có (giống thiếu gợi ý/bieu_thuc_ket_qua).
  - **Mặc định an toàn giữ nguyên**: `hien_loi_giai_chi_tiet` vẫn mặc định `False` dù AI đã điền
    sẵn nội dung — GV PHẢI tự xem/sửa rồi chủ động bật mới cho HS thấy (không tự động lộ ra).
  - Test mới: Stub sinh đủ `loi_giai_chi_tiet` cho cả 3 loại câu; thiếu trường này → có cảnh
    báo; `sinh_va_luu`/`luu_cau_nhap` (cả 2 luồng AI) lưu đúng nội dung AI sinh vào DB.
  - Không đổi schema DB (đã có từ v76), không cần migration thêm.
- **✅ "Lời giải chi tiết" cho câu hỏi — GV cấu hình, HS xem sau khi hoàn thành (v76):**
  - `Problem` thêm 2 cột: `loi_giai_chi_tiet` (Text, mặc định rỗng) và `hien_loi_giai_chi_tiet`
    (Boolean, mặc định `False` — ẨN cho tới khi GV chủ động bật, an toàn theo mặc định).
    Khác `solution_steps`/`bieu_thuc_ket_qua` (dùng cho gợi ý Socratic LÚC ĐANG học) —
    đây là bài giải đầy đủ, chỉ hiện SAU KHI hoàn thành nếu GV cho phép.
  - **Áp dụng cho cả 3 nguồn tạo câu hỏi** (đúng yêu cầu): `ThanCauHoiForm` (form dùng CHUNG
    cho `TaoCauHoi` + `SuaCauHoi` trong `QuanLyCauHoi.jsx`, và cũng được `AISinhCauHoi.jsx` tái
    dùng cho luồng "AI tạo bước và gợi ý" xem/sửa bản nháp trước khi lưu) — sửa 1 chỗ, áp dụng
    cả 3 nơi. Riêng `_luu_mot_cau()` (`question_gen_service.py`, dùng chung cho "Sinh hàng loạt"
    và "Tạo bước và gợi ý") tạo `Problem` trực tiếp, tách biệt khỏi `problem_service.tao_problem()`
    → phải sửa riêng để đọc đúng field khi GV chỉnh bản nháp AI.
  - **An toàn dữ liệu**: `loi_giai_chi_tiet`/`hien_loi_giai_chi_tiet` KHÔNG đưa vào
    `_strip_answers()` (hàm dùng chung cho lúc ĐANG học) — chỉ trả riêng ở endpoint
    `GET /sessions/{id}/xem-lai`, và CHỈ khi `problem.hien_loi_giai_chi_tiet == True`, nếu
    không trả `None`. Test khóa hành vi: HS không thấy qua danh sách/chi tiết bài (đang học),
    chỉ thấy qua xem-lại khi GV đã bật, mất ngay khi GV tắt lại.
  - Frontend: `TexField` (`QuanLyCauHoi.jsx`) thêm prop `rows` tùy chọn (mặc định vẫn 2, không
    đổi hành vi chỗ khác) — dùng `rows={6}` riêng cho ô này vì nội dung thường dài hơn 1 dòng.
    `XemLaiBai.jsx` thêm Card "Lời giải chi tiết" ngay SAU "Hành trình của em", chỉ hiện khi
    response có nội dung; dùng `whitespace-pre-wrap` để giữ xuống dòng GV đã gõ.
  - 2 cột mới thêm qua `ALTER TABLE` tự động lúc khởi động (đã xác nhận qua `dev.db` thật) —
    không cần migration thủ công, không đụng dữ liệu cũ.
- **🔒 Rà soát bảo mật & hoàn thiện vận hành toàn diện (v75)** — theo yêu cầu "kiểm tra và đánh
  giá toàn diện dự án như 1 senior developer", đã thực hiện đủ 7 mục đề xuất theo đúng thứ tự ưu
  tiên đã phân tích:
  1. **🔴 Vá lỗ hổng IDOR nghiêm trọng ở `monitor.py`** — vi phạm trực tiếp bất biến #6
     (CLAUDE.md: "GV chỉ thấy lớp mình"). Cả 5 endpoint (`GET/POST /monitor/flags`,
     `PATCH /monitor/flags/{id}`, `GET /monitor/sessions/{id}/turns`,
     `GET /monitor/sessions-hoan-thanh`) TRƯỚC ĐÓ không kiểm quyền sở hữu — bất kỳ GV nào
     cũng đọc/sửa được cờ, hội thoại, tên HS + điểm của HS thuộc GV KHÁC. Sửa bằng cách tái
     dùng `hoc_sinh_thuoc_gv()` (đã có sẵn, dùng đúng ở `progress.py`) + hàm mới
     `hs_ids_cua_gv()` (`progress_service.py`) để lọc theo GV ở cấp truy vấn (không lọc sau khi
     limit, tránh GV bị cờ của GV khác chiếm hết trang). Admin/tài khoản Quản lý
     (`co_toan_quyen`) không bị lọc, thấy toàn hệ thống như thiết kế.
     - **Test `test_monitor_idor.py` (7 test) đã XÁC NHẬN THẬT bằng cách chạy lại trên code
       CŨ** (git stash) — 5/7 test fail đúng như dự đoán trước khi vá, pass sau khi vá. Đây
       không phải suy đoán, đã kiểm chứng thực nghiệm.
  2. **Fail-fast khi `JWT_SECRET` mặc định chạy chung PostgreSQL** — `config.py` thêm
     `kiem_tra_an_toan_khoi_dong()`, gọi ở đầu `lifespan` (`main.py`) TRƯỚC `init_db()`. Nếu
     `DATABASE_URL` chứa "postgres" (dấu hiệu production) mà `JWT_SECRET` vẫn là
     `dev-secret-change-in-prod`/`change-me-in-production` → raise ngay, app từ chối khởi
     động thay vì âm thầm chạy với secret công khai (ai đọc mã nguồn cũng tự ký được JWT giả
     mạo Admin). SQLite (dev/test) không bị chặn. 4 test mới `test_config_safety.py`.
     - **✅ ĐÃ XÁC NHẬN (user, 2026-07-08)**: `JWT_SECRET` trên Render dashboard (service
       `mathtutor`) là 1 chuỗi ngẫu nhiên riêng, không phải giá trị mẫu mặc định.
  3. **`pool_pre_ping=True, pool_recycle=300`** cho engine SQLAlchemy (`db/base.py`) — chống lỗi
     "server closed the connection unexpectedly" khi Postgres managed (Render) tự đóng kết nối
     nhàn rỗi, nhất là sau khi service free/starter "ngủ" rồi "thức" lại.
  4. **CI GitHub Actions** (`.github/workflows/ci.yml`, MỚI — trước đây không có CI nào): job
     `backend` chạy `ruff check` + import smoke test + `pytest` (cài `.[llm,dev]` — GIỐNG HỆT
     Build Command thật trên Render, để CI cũng bắt được lỗi thiếu extra như sự cố v56); job
     `frontend` chạy `npm run build` (chặn) + `npm run lint` (KHÔNG chặn — còn nợ kỹ thuật lint
     cũ trước đợt này, vd `QuanLyCauHoi.jsx` 5 lỗi có sẵn, `XemLaiBai.jsx` 1 lỗi có sẵn, chưa
     thuộc phạm vi đợt rà soát này). Sẽ tự chạy trên mỗi push/PR vào `main` — đúng loại lỗi vừa
     làm sập production ở v72 (`DATETIME` không phải cú pháp Postgres) sẽ được CI chặn TRƯỚC khi
     Render deploy, nếu lỗi đó tái diễn dạng tương tự.
  5. **Chặn dò mật khẩu (brute-force) khi đăng nhập** — module mới `app/auth/throttle.py`
     (cửa sổ trượt trong bộ nhớ, KHÔNG thêm dependency mới, khớp phong cách dự án dùng thư viện
     tối giản). Khóa mềm theo TÊN ĐĂNG NHẬP (không theo IP — HS dùng chung mạng trường/NAT dễ
     khóa oan cả lớp nếu khóa theo IP) sau 5 lần sai liên tiếp trong 5 phút → 429. Đăng nhập
     đúng xóa lịch sử sai. Khởi động lại app thì bộ đếm reset — chấp nhận được, Render không
     restart theo từng request. 3 test mới `test_login_throttle.py`.
     Đồng thời giới hạn `anh_base64` (AI đọc đề từ ảnh) `max_length=10_000_000` ký tự ở tầng
     Pydantic (`schemas/question_gen.py`) — chặn NGOÀI payload khổng lồ trước khi tốn RAM giải
     mã base64; ngưỡng nghiệp vụ THẬT (5MB ảnh gốc, thông báo tiếng Việt rõ ràng) vẫn giữ
     nguyên ở `question_gen_service.doc_de_tu_anh()` — đã tính kỹ để 2 ngưỡng không đụng nhau
     (10M ký tự base64 ≈ 7,3MB ảnh gốc, rộng hơn 5MB).
  6. **`render.yaml` (mới, KHÔNG tự động áp dụng — chỉ tài liệu hóa/IaC tham khảo)** +
     `backend/runtime.txt` (`python-3.11.9`, ghim phiên bản — log deploy cho thấy Render đang
     chạy Python 3.14.3, quá mới so với `pyproject.toml` nhắm `py311` và các gói ghim chặt như
     `bcrypt<4.0`/`antlr4==4.11.0`, rủi ro tương thích). ⚠️ `render.yaml` có `<TODO>` placeholder
     cho URL thật (không tự bịa URL) — đọc kỹ cảnh báo đầu file trước khi cân nhắc bật Blueprint
     sync, KHÔNG tự ý bật vì có thể ảnh hưởng Persistent Disk chứa `backend/uploads/` đang có
     dữ liệu thật.
  7. Dọn 2 khoảng trống nhỏ còn lại: chốt chặn rò rỉ (`kiem_tra_ro_ri`) giờ rà CẢ lời chào mở
     đầu phiên (`tao_phien()`, `tutor_service.py`) — trước đây chỉ rà các lượt trả lời sau,
     lời chào đầu tiên đi thẳng ra HS không qua chốt chặn, vi phạm bất biến #3 ("rà MỌI phản
     hồi"). Test `test_leak_guard_opening_turn.py` — đã XÁC NHẬN THẬT bằng git stash y hệt
     cách 1. `/api/health` giờ ping DB thật (`SELECT 1`), trả `503` + `db:false` nếu DB chết
     thay vì luôn luôn trả `200 ok` dù mất kết nối — uptime monitor phân biệt được "app đứng"
     vs "app sống nhưng DB chết".
  - **An toàn dữ liệu**: KHÔNG đổi schema DB nào (chỉ thêm code/config/CI), không cần migration,
    không đụng dữ liệu production. Đã xác nhận qua dev server thật (khởi động lại, gọi
    `/api/health` và `/api/auth/login` qua HTTP thật, không chỉ pytest) — không có lỗi khởi động.
- **✅ Sửa phần "Xem lại bài" của HS — hiện công thức toán đúng (v74):**
  - Đổi tên "Lời giải chuẩn" → "Gợi ý các bước làm" (`XemLaiBai.jsx`).
  - **Fix "Kết quả bước" hiện lỗi kiểu `3∗x∗∗2−3`:** `bieu_thuc_ket_qua` lưu bằng cú pháp
    SymPy (vd `3*x**2 - 3`, dùng để CAS đối chiếu đáp án) nhưng frontend đưa thẳng vào KaTeX
    như thể đã là LaTeX. Sửa ở backend — endpoint `GET /sessions/{id}/xem-lai` (`sessions.py`)
    giờ chuyển `bieu_thuc_ket_qua` sang LaTeX thật bằng `sympy.latex()` (tái dùng
    `parse_bieu_thuc_an_toan()` có sẵn ở `core/matching/cas.py`) trước khi trả về — vd
    `3*x**2 - 3` → `3 x^{2} - 3`. Có fallback giữ nguyên chuỗi gốc nếu không parse được, không
    làm hỏng cả trang vì 1 biểu thức lỗi. Test mới `test_xem_lai_bieu_thuc_ket_qua_tra_ve_latex`
    khóa hành vi (chốt trạng thái hoàn thành phiên thẳng qua DB thay vì hội thoại, để tách biệt
    khỏi logic orchestrator — test này chỉ quan tâm bước chuyển đổi LaTeX ở response).
  - Không đổi schema DB, không cần migration.
- **✅ Chi tiết trang kết quả thi thử (v73):**
  - **Fix "ô trống" ở gợi ý giao nhiệm vụ (v71 gây ra):** `_bai_dict()` (`nhiem_vu_service.py`,
    dùng chung cho "gợi ý theo điểm yếu" + "gợi ý theo dạng") thiếu trường `de_bai` — trước giờ
    không lộ vì gợi ý theo điểm yếu chỉ dùng `problem_id` để gộp vào danh sách đã tải sẵn cục
    bộ, còn "gợi ý theo dạng" (mới ở v71) render trực tiếp từ response nên hiện trống. Thêm
    `de_bai` vào `_bai_dict()`; test mới khóa lại (assert `de_bai` không rỗng), tiện sửa luôn
    chỗ frontend quên bọc `renderDe()` (câu có công thức toán sẽ hiện `$...$` thô nếu không bọc).
  - **Trang xem kết quả (cả HS `ThiThu.jsx` và GV `ChiTietBaiGV`)** giờ hiện ĐỦ nội dung câu hỏi:
    thêm hình minh họa (nếu có) và 4 phương án A/B/C/D (TN4PA) / 4 ý a/b/c/d (TNDS) — dữ liệu
    này backend đã trả sẵn từ trước qua `_strip_answers()` (`meta.phuong_an`/`meta.y`), chỉ là
    2 nơi hiển thị kết quả đều chưa render ra, không phải thiếu API.
  - **Danh sách gợi ý bài giao nhiệm vụ** (`GoiYNhiemVu` trong `QuanLyDeThi.jsx`) mỗi câu thêm
    badge ghi rõ loại (TN4PA/TNDS/TLN) — vì 1 "dạng" (dang_id) có thể gồm nhiều loại câu khác
    nhau, cần phân biệt trước khi GV chọn giao.
  - Không đổi schema DB, không cần migration — thuần sửa logic/hiển thị.
- **🔥 HOTFIX production sập lúc deploy (v72):** v71 thêm migration `ALTER TABLE de_thi ADD
  COLUMN ... DATETIME` — `DATETIME` là kiểu riêng của SQLite, PostgreSQL không hiểu (lỗi
  `psycopg2.errors.UndefinedObject: type "datetime" does not exist`) → `init_db()` raise ngay
  lúc khởi động → toàn bộ app crash-loop trên Render (`Application startup failed. Exiting`).
  Sửa: đổi cả 3 chỗ dùng `DATETIME` trong `_migrate_them_cot()` (`init_db.py`) sang `TIMESTAMP`
  (kiểu ANSI chuẩn, cả SQLite lẫn Postgres đều hiểu đúng — đã test tay cả 2 phía trước khi
  push). 1 trong 3 chỗ (`problems.tao_luc`) là lỗi CŨ có từ trước, chỉ chưa lộ ra vì cột đó đã
  tồn tại sẵn trên production nên nhánh `if ... not in cot` chưa từng chạy tới — nay sửa luôn
  cho chắc, dù không ảnh hưởng hành vi hiện tại (branch vẫn không chạy vì cột đã có).
  **Bài học**: mọi câu lệnh `ALTER TABLE` raw SQL thêm cột kiểu ngày giờ PHẢI dùng `TIMESTAMP`,
  KHÔNG dùng `DATETIME` — pattern chuẩn từ nay cho `_migrate_them_cot()`.
  - Chủ động đẩy fix ngay (không chờ user yêu cầu "đưa lên github") vì production đang crash-loop
    thật — mức độ khẩn cấp cao hơn quy trình chờ xác nhận thông thường; đã báo rõ với user.
- **✅ GV xem chi tiết kết quả thi của HS + gợi ý giao nhiệm vụ luyện tập (v71):**
  - Mỗi thẻ đề (trang GV) hiện thêm **ngày tạo/phát hành/thu hồi**. `DeThi` thêm 2 cột nullable
    `phat_hanh_luc`/`thu_hoi_luc` — lưu MỐC GẦN NHẤT (không lưu lịch sử nhiều lần bấm), cập nhật
    mỗi khi GV bấm Phát hành/Thu hồi; `thu_hoi_luc` KHÔNG bị xóa khi phát hành lại và ngược lại.
  - Bảng "Kết quả lớp" mỗi HS thêm nút **"Xem chi tiết"** → mở panel hiện đúng thông tin HS tự
    xem sau khi thi (điểm, từng câu, đúng/sai, HS trả lời gì, đáp án đúng). Endpoint mới
    `GET /de-thi/bai/{bai_id}/chi-tiet-gv` — refactor phần build "kết quả đã nộp" ra hàm dùng
    chung `_ket_qua_bai_da_nop()` giữa HS tự xem (`_trang_thai_bai`) và GV xem (endpoint mới),
    tránh lặp code lẫn lệch dữ liệu giữa 2 nơi; kiểm quyền theo GV sở hữu ĐỀ (không phải HS sở
    hữu bài) + chặn xem khi bài chưa nộp (400).
  - **Gợi ý giao nhiệm vụ ngay tại câu sai** (đã hỏi & xác nhận với user: chọn phương án "tạo
    nhanh tại chỗ", không điều hướng sang trang khác): mỗi câu sai có gắn `dạng` hiện nút
    "🎯 Giao nhiệm vụ luyện lại dạng ..." → hiện danh sách bài CÙNG DẠNG, đã duyệt, HS CHƯA làm
    để GV tick chọn rồi giao ngay tại chỗ (gọi thẳng `POST /nhiem-vu` có sẵn). Hàm mới
    `de_xuat_theo_dang()` (`nhiem_vu_service.py`) — mirror `de_xuat_theo_diem_yeu()` nhưng khoanh
    đúng 1 `dang_id` do GV chỉ định thay vì quét toàn bộ hồ sơ năng lực; endpoint mới
    `GET /nhiem-vu/de-xuat-dang?hoc_sinh_id=&dang_id=`.
  - **An toàn production**: 2 cột mới trên `de_thi` đều nullable, thêm qua `ALTER TABLE` tự động
    lúc khởi động (giống pattern `pham_vi`/`diem_cau` các v trước) — không đụng dữ liệu cũ.
  - Test mới: `test_ngay_tao_phat_hanh_thu_hoi`, `test_chi_tiet_bai_gv_va_goi_y_nhiem_vu` (kiểm
    cả quyền sở hữu đề/HS và trường hợp bài chưa nộp).
- **✅ Chế độ "Tự do" khi GV tạo đề thi thử (v70):** ngoài chế độ "Chuẩn 2025" hiện có (điểm/câu
  cố định 0,25/1,0/0,5), thêm chế độ Tự do — GV tự bật/tắt từng phần (I/II/III), tự đặt TỔNG
  ĐIỂM mỗi phần đã bật (không bắt buộc theo cấu trúc chuẩn), tổng toàn đề không vượt quá 10
  điểm. Ràng buộc loại câu theo phần (I=TN4PA/II=TNDS/III=TLN) vẫn giữ nguyên (đã hỏi & xác
  nhận với user — bậc thang TNDS chỉ có ý nghĩa đúng loại). Toggle chế độ tích hợp ngay trong
  form "Tạo đề mới" hiện có; cả 2 cách chọn câu (thủ công / trộn ma trận) đều dùng lại được —
  khối "Trộn đề tự động theo ma trận" xác nhận là DÙNG CHUNG cho cả 2 chế độ (chỉ lo chọn câu,
  không biết khái niệm điểm phần; phần đã tắt tự trộn 0 câu).
  - Backend: `DeThiCau` thêm cột `diem_cau` (nullable) — đề Chuẩn/đề cũ không set, fallback về
    hằng số `DIEM_CAU` cũ qua helper `_diem_moi_cau()` (không ảnh hưởng đề đã có). `tao_de()`
    nhận thêm `diem_phan`, validate ĐẦY ĐỦ trước khi tạo bản ghi nào (áp dụng bài học từ bug
    tuần trước: validate trước, mutate sau). Điểm/câu = tổng điểm phần ÷ số câu, làm tròn 2 chữ
    số; cảnh báo (không chặn) nếu lệch làm tròn > 0,01đ; chặn tạo đề nếu tổng phần > 10đ hoặc
    phần có câu mà thiếu điểm hợp lệ.
  - **An toàn production**: cột `diem_cau` mới thêm qua `ALTER TABLE` tự động lúc khởi động
    (giống pattern `pham_vi` ở v69) — không đụng dữ liệu cũ.
  - Test mới `test_tao_de_tu_do`: bỏ phần II/III, chia điểm không tròn có cảnh báo đúng, chấm
    điểm dùng đúng điểm/câu mới (không phải 0,25 mặc định), chặn đúng khi tổng > 10đ.
- **✅ 4 sửa/thêm ở Thi thử (v69):**
  1. **Fix lỗi đếm giờ sai** — đề 90 phút hiện đếm ngược từ "90 phút mấy giây" thay vì đúng
     90:00. Nguyên nhân: `_het_han_luc()` (hạn CHẤP NHẬN thao tác trễ, có cộng gia hạn
     `GIA_HAN_GIAY=30`) bị dùng luôn để tính `con_lai_giay` hiển thị cho HS. Tách riêng
     `_han_hien_thi()` (không cộng gia hạn) chỉ dùng cho hiển thị đồng hồ đếm ngược
     (`de_thi.py` dòng tính `con_giay`); 4 chỗ dùng `_het_han_luc` còn lại (autosave/nộp/tự
     chốt quá hạn) giữ nguyên vì đúng là cần nhân nhượng phía server.
  2. Đổi chữ "Thi thử theo đề hoàn chỉnh" → "Thi thử" (`ThiThu.jsx`).
  3. Danh sách đề của HS: bỏ badge số câu + điểm tối đa; dòng "Lần gần nhất" thêm "Làm trong"
     (giây giữa `bat_dau_luc`/`nop_luc`) và "Ngày" (ngày nộp) — backend `ds_de_hs()` trả thêm
     `lam_trong_giay`/`nop_luc` trong `bai_gan_nhat`.
  4. **Chức năng mới — chọn đối tượng khi phát hành đề thi thử:** GV giờ chọn "Tất cả học
     sinh" hoặc "Tùy chọn lớp/học sinh" khi phát hành (thay vì luôn phát cho mọi HS chủ
     nhiệm) — thực tế xác nhận trên production: 1 GV có thể chủ nhiệm nhiều lớp (`gv12a1`
     quản cả 12A1 + 12D4), trước đây không có cách giới hạn. Mirror đúng pattern có sẵn của
     "Giao nhiệm vụ" (`NhiemVu`/`NhiemVuHocSinh` + `_so_huu_lop`/`_so_huu_hs`):
     - Model mới: `DeThi.pham_vi` (`"tat_ca"` | `"tuy_chon"`, cột `String(16)` — **cố ý KHÔNG
       dùng Postgres native ENUM** để có thể thêm cột bằng `ALTER TABLE ADD COLUMN` đơn giản
       trên production, theo đúng pattern `_migrate_them_cot` đã có sẵn); bảng mới
       `de_thi_hoc_sinh` (junction, chỉ dùng khi `pham_vi="tuy_chon"`).
     - `dat_phat_hanh()` nhận thêm `pham_vi`/`lop_ids`/`hoc_sinh_ids`; validate quyền sở hữu
       lớp/HS TRƯỚC khi mutate bất kỳ gì (tránh lỗi tìm thấy qua test: nếu mutate rồi mới
       validate, autoflush của các câu query xác thực sẽ đẩy `phat_hanh=True` dở dang xuống DB
       dù request sau đó bị từ chối). `pham_vi=None` (chỉ đổi cờ phát hành) → giữ nguyên phạm
       vi đã cấu hình trước đó.
     - Enforce ở 3 nơi: `ds_de_hs` (danh sách hiện cho HS), `bat_dau_thi` (chặn bắt đầu nếu
       không nằm trong danh sách được giao), và tất nhiên `dat_phat_hanh` khi ghi.
     - Frontend: `QuanLyDeThi.jsx` thêm `ChonDoiTuongPhatHanh` — bấm "Phát hành" (đề đang
       nháp) mở panel chọn "Tất cả"/"Tùy chọn" + picker lớp/học sinh (tái dùng UI pattern từ
       `GiaoNhiemVu.jsx`); "Thu hồi" vẫn là nút tắt nhanh không mở panel.
     - **An toàn production**: cột mới có `DEFAULT 'tat_ca' NOT NULL` (hành vi cũ = phát hành
       cho tất cả, không đổi behavior các đề đã phát hành trước đây); bảng mới tự tạo qua
       `Base.metadata.create_all` lúc khởi động — cả hai đều KHÔNG đụng dữ liệu đã có.
  - Test mới: `test_de_thi.py` (giờ hiển thị đúng + `test_phat_hanh_tuy_chon_doi_tuong`).
- **✅ Dialog hỏi Duyệt ngay sau khi GV lưu câu hỏi (v68):** trước đây GV Sửa xong bấm Lưu thì
  quay thẳng về danh sách, phải tự tìm lại để duyệt — bất tiện. `SuaCauHoi` (`QuanLyCauHoi.jsx`)
  giờ sau khi lưu thành công, nếu câu hỏi **chưa** ở trạng thái "Đã duyệt" → hiện dialog hỏi
  "Duyệt luôn" hay "Chỉ lưu, duyệt sau"; chọn Duyệt luôn thì gọi API duyệt (`api.duyetCau`)
  ngay trước khi đóng màn sửa. Câu đã duyệt sẵn thì lưu bình thường, không hỏi thừa. Mở rộng
  `useConfirm()` (`ConfirmDialog.jsx`) nhận thêm nhãn nút tùy chỉnh (`labelYes`/`labelNo`), mặc
  định vẫn "OK"/"Hủy" — không ảnh hưởng các chỗ dùng cũ (xóa/khôi phục/hủy duyệt).
- **✅ 2 UI nhỏ khác trong "Chọn bài khác" phòng học HS (v68):** đổi từ chữ mờ sang nút rõ ràng
  (`Button variant="secondary" size="sm"`), sau đó tô nền cam nhạt (`bg-warning-soft` — màu gần
  "cam" nhất có sẵn trong hệ thống, không bịa hex mới) + đổ bóng nhẹ (`--shadow-card`) theo yêu
  cầu cho dễ thấy hơn. Đã kiểm tra thứ tự CSS biên dịch để đảm bảo màu ghi đè đúng.
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
