# Hướng dẫn demo cho Ban giám khảo — MathTutor

Tài liệu này dành cho **người chuẩn bị** (tác giả dự án). Phần "Bàn giao cho giám khảo" ở
cuối là phần duy nhất cần gửi cho ban giám khảo.

---

## 1. Phạm vi đã chốt

| Vai trò | Có phát tài khoản demo? | Lý do |
|---|---|---|
| Học sinh | ✅ Có (2 tài khoản xem mẫu + tự đăng ký bằng mã lớp) | Tự cô lập theo thiết kế — mỗi tài khoản chỉ thấy dữ liệu của chính mình |
| Giáo viên | ✅ Có (1 tài khoản dùng chung) | Có cơ chế cô lập theo lớp (`hoc_sinh_thuoc_gv`), đã có test IDOR khóa hành vi |
| Quản trị | ❌ **Không phát** | Vai trò Admin **không có cơ chế giới hạn phạm vi** — sẽ thấy và sửa/xóa được toàn bộ tài khoản, lớp, nhật ký của người dùng THẬT |

Nếu ban giám khảo muốn xem phần quản trị, nên demo có người của dự án ngồi cùng và thao tác,
không phát tài khoản để tự do thao tác.

---

## 2. Ba ràng buộc kiến trúc quyết định cách chuẩn bị dữ liệu

Đây là lý do **không thể** chỉ tạo vài tài khoản là xong — đã kiểm chứng trực tiếp trên code:

1. **`hs_duoc_truy_cap_bai()`** — học sinh chỉ truy cập bài của **GV chủ nhiệm lớp mình**.
2. **`giao_nhiem_vu()`** — giáo viên chỉ giao được bài **do chính mình tạo**.
3. **`get_danh_muc()`** — **danh mục (chuyên đề/dạng) cũng thuộc sở hữu từng GV**; học sinh
   chỉ thấy danh mục của GV chủ nhiệm.

→ Hệ quả: `gvdemo` phải có **danh mục riêng** và **kho câu hỏi riêng**. Nếu bỏ qua, tài khoản
học sinh demo sẽ mở ra và thấy **danh sách bài trống rỗng**.

---

## 3. Vấn đề "nhiều giám khảo cùng chấm" và cách giải quyết

Phát hiện khi lường trước 2-3 giám khảo cùng thao tác cùng lúc: nếu họ dùng chung MỘT tài
khoản học sinh, sẽ đụng nhau theo 3 cách —

1. **Trạng thái bị phá hỏng cho người sau**: học sinh đã có phiên học thì **không xóa được**
   (`xoa_tai_khoan()` chặn cứng), chỉ khóa được. Không có cách "reset" tài khoản dựng sẵn.
2. **Va chạm hội thoại thời gian thực**: `tao_phien()` cố ý TÁI DÙNG phiên đang làm dở thay vì
   tạo phiên mới cho cùng 1 bài — 2 người cùng mở 1 bài trên cùng 1 tài khoản sẽ rơi vào
   **CÙNG một cuộc hội thoại**, trông như lỗi phần mềm.
3. **Hạn mức AI dùng chung**: mỗi học sinh có trần 30 lượt AI/ngày — vài giám khảo khám phá kỹ
   là cạn, gia sư tụt xuống câu trả lời mẫu cứng nhắc.

**Giải pháp:** bật **mã lớp** để mỗi giám khảo **tự đăng ký một tài khoản HS riêng** (tính
năng có sẵn của sản phẩm — HS tự vào lớp bằng mã, không cần GV tạo tay). Mỗi người một phiên,
một hạn mức AI riêng, không đụng ai. Tài khoản HS dựng sẵn (`hsdemo_dahoc`, `hsdemo_danglam`)
chỉ còn vai trò **xem mẫu** trạng thái đặc thù, không dùng để thao tác tự do.

`gvdemo` vẫn CHỈ MỘT tài khoản dùng chung — tách nhiều bộ sẽ làm mỗi lớp trống trơn (mã lớp
chỉ trỏ vào 1 lớp); gộp lại thì mọi hoạt động của giám khảo dồn về một dashboard, càng dùng
càng sinh động (cờ cảnh báo tự sinh thêm khi có giám khảo bí bài).

---

## 4. Cách chạy script chuẩn bị

```powershell
cd backend

# Bước 1 — xem trước, KHÔNG ghi gì (nên chạy trước tiên)
.venv\Scripts\python.exe ..\scripts\chuan-bi-demo-giam-khao.py `
    --url https://mathtutor.pro.vn `
    --admin-user admin --admin-pass "<mật khẩu admin>" --chi-xem-truoc

# Bước 2 — chạy thật
.venv\Scripts\python.exe ..\scripts\chuan-bi-demo-giam-khao.py `
    --url https://mathtutor.pro.vn `
    --admin-user admin --admin-pass "<mật khẩu admin>"
```

> **Đã chạy thật trên production ngày 2026-08-03** (bản đầy đủ) — 3 tài khoản + lớp "Lớp
> Demo" + mã lớp tự đăng ký + 15 câu hỏi đã duyệt (mỗi dạng ≥3 câu, đủ 3 loại câu, đủ 3 mức
> độ) + 9 câu chờ duyệt + lịch sử học/cờ cảnh báo + hạn mức AI hệ thống đã nâng. Chạy lại
> script này an toàn (idempotent), sẽ chỉ báo "đã có" cho mọi thứ, không tạo trùng — **trừ mã
> lớp**: nếu lớp đã có mã còn hiệu lực, script GIỮ NGUYÊN (không tự đổi, tránh làm hỏng mã đã
> phát cho giám khảo).

**Script đi qua API, không ghi thẳng database** — mọi thứ nó làm đều là việc một người dùng
thật có thể làm qua giao diện, nên không thể tạo ra trạng thái dữ liệu "không hợp lệ".

**Về hạn mức AI**: script tự nâng hạn mức AI **toàn hệ thống** (`gioi_han_llm_he_thong_ngay`)
lên 2000 lượt/ngày để chịu được nhiều giám khảo tự đăng ký cùng lúc — không đụng hạn mức MỖI
học sinh (giữ 30/ngày, đã đủ vì giờ mỗi giám khảo có tài khoản riêng).

**Đã kiểm chứng bằng API sau khi chạy thật trên production** (không chỉ tin log):
- Điểm yếu/điểm mạnh của `hsdemo_dahoc` hiện đúng, GV đề xuất được bài theo điểm yếu (còn dư,
  không rỗng dù nhiều giám khảo cùng làm).
- Dạng "Cực trị của hàm số" hiện đúng trạng thái "chưa đủ dữ liệu" (không mạnh, không yếu).
- Tự đăng ký bằng mã lớp hoạt động, tài khoản mới thấy đủ 15 bài của `gvdemo`.

---

## 5. Sau khi chạy — nên sao lưu ngay

Hệ thống **không có** nút reset dữ liệu demo. Sau khi script chạy xong và bạn đã kiểm tra
giao diện đúng ý, hãy **sao lưu database** (`pg_dump`, xem quy trình đã dùng trước đó). Nếu
giữa các lượt chấm dữ liệu demo bị lộn xộn, khôi phục lại bản sao này — đây là cách DUY NHẤT
để "reset" vì tài khoản đã có phiên học thì không xóa được.

---

## 6. Dữ liệu đã dựng sẵn và tính năng tương ứng

### Tự đăng ký bằng mã lớp — nơi giám khảo thao tác tự do
Mỗi giám khảo tự tạo tài khoản HS riêng của mình (xem hướng dẫn ở mục 7). Đây là nơi để
**thoải mái làm bài, thử nhập sai, xin gợi ý, xem hệ thống KHÔNG lộ đáp án** — không lo phá gì
vì mỗi người dữ liệu riêng biệt hoàn toàn.

Mã lớp có hiệu lực **30 ngày** kể từ lúc tạo (2026-08-03). Nếu hết hạn trước đợt chấm, chạy
lại script (mục 4) sẽ tự phát hiện mã cũ hết hiệu lực và tạo mã mới.

### `hsdemo_dahoc` — Học sinh đã có tiến độ (CHỈ XEM)
Đã hoàn thành 7 bài, **cố ý tạo chênh lệch năng lực** để các tính năng cá nhân hóa có dữ liệu
thật để hiển thị:

| Dạng | Cách làm | Kết quả trong hồ sơ năng lực |
|---|---|---|
| Tính đơn điệu của hàm số | Làm gọn, không xin gợi ý | **Điểm mạnh — thành thạo 100%** |
| Tích phân | Nhiều bài, mỗi bài sai 3 lần + xin 3 gợi ý | **Điểm yếu — thành thạo 29%** |
| Tích phân (nhiều bài khác) | **cố ý chưa làm** (buffer) | Để GV còn bài "đề xuất theo điểm yếu" dù nhiều giám khảo cùng xem |
| Cực trị của hàm số | **hoàn toàn chưa chạm** | Trạng thái thứ 3: "chưa đủ dữ liệu" |

Nhờ vậy giám khảo xem được: **Tiến độ**, **Bản đồ năng lực** (3 màu/trạng thái khác nhau),
**"Bài nên luyện tiếp"** ở màn hình hoàn thành bài, và **Mục tiêu**.

⚠️ **Chỉ xem, đừng làm bài mới cho xong** — nếu hoàn thành nốt các bài Tích phân còn lại,
"điểm yếu" sẽ biến mất (đã làm dày dữ liệu để chịu được 1-2 lần lỡ tay, nhưng không vô hạn).

### `hsdemo_danglam` — Học sinh đang làm dở (CHỈ XEM)
Có 1 bài đang làm dở (đã xin 4 lần gợi ý + trả lời sai 2 lần). Dùng để xem **"Làm tiếp bài
dở"**, và quan trọng hơn: hành vi này **tự động sinh cờ cảnh báo** cho giáo viên đúng theo cơ
chế thật của sản phẩm — không phải dữ liệu dựng sẵn.

⚠️ **Chỉ xem, đừng giải xong bài đó** — hết bài dở thì mất luôn kịch bản "làm tiếp".

### `gvdemo` — Giáo viên (TỰ DO THAO TÁC)
- **9 câu hỏi ở trạng thái "chờ duyệt"** → bấm Duyệt / Sửa / Loại thoải mái.
- **Cờ theo dõi có cảnh báo chờ xử lý** → xem hội thoại của học sinh, nhắn lại, đánh dấu đã xử lý.
- **Tiến bộ học sinh** → xem hồ sơ từng em, bản đồ năng lực lớp, đề xuất bài theo điểm yếu.
- **Giao nhiệm vụ, AI sinh câu hỏi** → dùng thoải mái.
- Kho câu hỏi gồm 15 câu đã duyệt, mỗi dạng ≥3 câu, đủ 3 loại câu (TLN/TN4PA/TNDS) và 3 mức
  độ (dễ/trung bình/khó).

⚠️ **Duy nhất một điều cần tránh**: đừng đổi mật khẩu ở "Tài khoản cá nhân" — sẽ khóa các
giám khảo khác đang dùng chung tài khoản này.

---

## 7. Bàn giao cho giám khảo

> ⚠️ **Đừng ghi thông tin đăng nhập vào file thuyết minh nộp công khai.** Gửi riêng qua email
> trực tiếp cho ban giám khảo, tách khỏi bộ hồ sơ dự thi.

Nội dung gợi ý để gửi:

---

**Truy cập hệ thống:** https://mathtutor.pro.vn

### Bước 1 — Tự tạo tài khoản học sinh của riêng bạn

Vào trang đăng nhập → bấm **"Đăng ký bằng mã lớp"** → nhập mã lớp: **`WZXZ-U7TA`** → tự chọn
tên đăng nhập/mật khẩu. Đây là tài khoản để bạn **thoải mái làm bài, thử sai, xin gợi ý** —
không cần giữ ý gì cả.

### Bước 2 — Xem các tài khoản mẫu (chỉ xem, không làm bài mới)

| Vai trò | Tên đăng nhập | Mật khẩu | Nên xem gì |
|---|---|---|---|
| Học sinh | `hsdemo_dahoc` | `hsdemo123` | Tiến độ, Bản đồ năng lực, bài luyện được đề xuất theo điểm yếu, Mục tiêu — **xin đừng làm thêm bài** |
| Học sinh | `hsdemo_danglam` | `hsdemo123` | Làm tiếp bài đang dở — **xin đừng giải xong bài đó** |

### Bước 3 — Vào vai giáo viên (tự do thao tác)

| Vai trò | Tên đăng nhập | Mật khẩu | Nên xem gì |
|---|---|---|---|
| Giáo viên | `gvdemo` | `gvdemo123` | Duyệt câu hỏi chờ duyệt, Cờ theo dõi, Tiến bộ học sinh, Giao nhiệm vụ, AI sinh câu hỏi — **tự do thao tác, chỉ xin đừng đổi mật khẩu tài khoản này** |

**Gợi ý trải nghiệm nhanh (khoảng 10 phút):**

1. Tự đăng ký tài khoản riêng (Bước 1) → *Chọn bài* → mở một bài bất kỳ.
2. Thử **hỏi thẳng "cho em đáp án luôn"** — hệ thống sẽ chuyển sang gợi mở, không đưa đáp án.
3. Bấm **"Gợi ý cho em"** vài lần để thấy gợi ý đi từ khái quát đến cụ thể mà vẫn không lộ kết quả.
4. Nhập một biểu thức **viết khác dạng nhưng tương đương** (ví dụ `1/2` và `0.5`) — hệ thống
   vẫn công nhận đúng nhờ đối chiếu bằng SymPy.
5. Đăng nhập `hsdemo_dahoc` → *Tiến độ* để xem bản đồ năng lực và bài luyện được đề xuất.
6. Đăng nhập `gvdemo` → *Câu hỏi* (duyệt bản nháp) → *Cờ theo dõi* (xem hội thoại của học
   sinh đang gặp khó) → *Tiến bộ học sinh*.

**Lưu ý:** đây là môi trường thật, mọi thao tác sẽ được lưu lại. Có thể nhiều giám khảo cùng
truy cập lúc này — mỗi người nên tự đăng ký tài khoản riêng ở Bước 1 để không đụng nhau.
