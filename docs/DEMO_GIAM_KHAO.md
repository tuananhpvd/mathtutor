# Hướng dẫn demo cho Ban giám khảo — MathTutor

Tài liệu này dành cho **người chuẩn bị** (tác giả dự án). Phần "Bàn giao cho giám khảo" ở
cuối là phần duy nhất cần gửi cho ban giám khảo.

---

## 1. Phạm vi đã chốt

| Vai trò | Có phát tài khoản demo? | Lý do |
|---|---|---|
| Học sinh | ✅ Có (3 tài khoản) | Tự cô lập theo thiết kế — chỉ thấy dữ liệu của chính mình |
| Giáo viên | ✅ Có (1 tài khoản) | Có cơ chế cô lập theo lớp (`hoc_sinh_thuoc_gv`), đã có test IDOR khóa hành vi |
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

## 3. Cách chạy script chuẩn bị

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

> **Đã chạy thật trên production ngày 2026-08-03** — 4 tài khoản + lớp "Lớp Demo" + 10 câu hỏi
> + lịch sử học/cờ cảnh báo đã có sẵn. Chạy lại script này an toàn (idempotent), sẽ chỉ báo
> "đã có" cho mọi thứ, không tạo trùng.

**Script đi qua API, không ghi thẳng database** — mọi thứ nó làm đều là việc một người dùng
thật có thể làm qua giao diện, nên không thể tạo ra trạng thái dữ liệu "không hợp lệ". Chạy
lại nhiều lần không nhân đôi dữ liệu (idempotent).

**Về hạn mức AI**: script gọi API thật để dựng lịch sử học, tốn khoảng 60–80 lượt LLM. Nếu
vượt `gioi_han_llm_hs_ngay`, hệ thống tự chuyển sang phản hồi mẫu — phiên vẫn hoàn thành và
số liệu tiến độ vẫn đúng, chỉ lời thoại là mẫu có sẵn. Nên chạy lúc không trùng giờ học sinh
thật đang dùng.

**Đã kiểm chứng**: script đã chạy trọn vẹn trên môi trường local với DB sạch, và xác minh
bằng API rằng mọi tính năng dưới đây thật sự có dữ liệu để hiển thị (không phải chỉ tạo tài
khoản rỗng).

---

## 4. Sau khi chạy — nên sao lưu ngay

Hệ thống **không có** nút reset dữ liệu demo. Sau khi script chạy xong và bạn đã kiểm tra
giao diện đúng ý, hãy **sao lưu database** (theo đúng quy trình sao lưu hàng tuần đã có trong
`docs/THUC_NGHIEM.md`). Nếu giữa các lượt chấm dữ liệu demo bị lộn xộn (bài dở dang chồng
chất, mục tiêu test lung tung), khôi phục lại bản sao này.

---

## 5. Dữ liệu đã dựng sẵn và tính năng tương ứng

### `hsdemo_moi` — Học sinh mới bắt đầu
Chưa có dữ liệu gì. Dùng để xem **luồng học từ đầu**: chọn bài → gia sư chào và dẫn dắt →
nhập công thức → chấm từng bước → gợi ý bắc thang khi bí.

### `hsdemo_dahoc` — Học sinh đã có tiến độ
Đã hoàn thành 5 bài, **cố ý tạo chênh lệch năng lực** để các tính năng cá nhân hóa có dữ liệu
thật để hiển thị (nếu làm đúng hết thì mọi biểu đồ sẽ phẳng và vô nghĩa):

| Dạng | Cách làm | Kết quả trong hồ sơ năng lực |
|---|---|---|
| Tính đơn điệu của hàm số | 3 bài, làm gọn, không xin gợi ý | **Điểm mạnh — thành thạo 100%** |
| Tích phân | 2 bài, mỗi bài sai 3 lần + xin 3 gợi ý | **Điểm yếu — thành thạo 29%** |
| Tích phân (bài thứ 3) | **cố ý chưa làm** | Để GV còn bài để "đề xuất theo điểm yếu" |

Nhờ vậy giám khảo xem được: **Tiến độ**, **Bản đồ năng lực** (có màu đậm nhạt khác nhau),
**"Bài nên luyện tiếp"** ở màn hình hoàn thành bài, và **Mục tiêu**.

### `hsdemo_danglam` — Học sinh đang làm dở
Có 1 bài đang làm dở (đã xin 4 lần gợi ý + trả lời sai 2 lần). Dùng để xem **"Làm tiếp bài
dở"**, và quan trọng hơn: hành vi này **tự động sinh cờ cảnh báo** cho giáo viên đúng theo cơ
chế thật của sản phẩm — không phải dữ liệu dựng sẵn.

### `gvdemo` — Giáo viên
- **3 câu hỏi ở trạng thái "chờ duyệt"** → bấm Duyệt / Sửa / Loại ngay.
- **Cờ theo dõi có cảnh báo chờ xử lý** → xem hội thoại của học sinh, nhắn lại, đánh dấu đã xử lý.
- **Tiến bộ học sinh** → xem hồ sơ từng em, bản đồ năng lực lớp, đề xuất bài theo điểm yếu.
- Kho câu hỏi riêng gồm đủ **3 loại câu** (TLN / TN4PA / TNDS) và 3 mức độ khó.

---

## 6. Bàn giao cho giám khảo

> ⚠️ **Đừng ghi thông tin đăng nhập vào file thuyết minh nộp công khai.** Gửi riêng qua email
> trực tiếp cho ban giám khảo, tách khỏi bộ hồ sơ dự thi.

Nội dung gợi ý để gửi:

---

**Truy cập hệ thống:** https://mathtutor.pro.vn

**Tài khoản trải nghiệm**

| Vai trò | Tên đăng nhập | Mật khẩu | Nên xem gì |
|---|---|---|---|
| Học sinh | `hsdemo_moi` | `hsdemo123` | Trải nghiệm học từ đầu: chọn bài, gia sư gợi mở từng bước, gợi ý bắc thang, thử nhập sai để xem hệ thống KHÔNG cho đáp án |
| Học sinh | `hsdemo_dahoc` | `hsdemo123` | Tiến độ, Bản đồ năng lực, bài luyện được đề xuất theo điểm yếu, Mục tiêu |
| Học sinh | `hsdemo_danglam` | `hsdemo123` | Làm tiếp bài đang dở |
| Giáo viên | `gvdemo` | `gvdemo123` | Duyệt câu hỏi chờ duyệt, Cờ theo dõi (xem hội thoại học sinh, nhắn lại), Tiến bộ học sinh, Giao nhiệm vụ, AI sinh câu hỏi |

**Gợi ý trải nghiệm nhanh (khoảng 10 phút):**

1. Đăng nhập `hsdemo_moi` → *Chọn bài* → mở một bài bất kỳ.
2. Thử **hỏi thẳng "cho em đáp án luôn"** — hệ thống sẽ chuyển sang gợi mở, không đưa đáp án.
3. Bấm **"Gợi ý cho em"** vài lần để thấy gợi ý đi từ khái quát đến cụ thể mà vẫn không lộ kết quả.
4. Nhập một biểu thức **viết khác dạng nhưng tương đương** (ví dụ `1/2` và `0.5`) — hệ thống
   vẫn công nhận đúng nhờ đối chiếu bằng SymPy.
5. Đăng nhập `hsdemo_dahoc` → *Tiến độ* để xem bản đồ năng lực và bài luyện được đề xuất.
6. Đăng nhập `gvdemo` → *Câu hỏi* (duyệt bản nháp) → *Cờ theo dõi* (xem hội thoại của học
   sinh đang gặp khó) → *Tiến bộ học sinh*.

**Lưu ý:** đây là môi trường thật, mọi thao tác sẽ được lưu lại. Ban giám khảo có thể thao tác
tự do trên các tài khoản này.
