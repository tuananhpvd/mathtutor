# DEMO.md — Kịch bản demo cố định MathTutor (Phase 11)

Kịch bản lặp lại được với **LLM_PROVIDER=stub** (không cần mạng, phản hồi tất định) và dữ liệu
seed chuẩn. Mọi bước dưới đây cho kết quả giống nhau mỗi lần chạy lại từ DB sạch.

## 0. Khởi động

```powershell
# Backend (cửa sổ 1)
cd D:\claude\mathtutor\backend
Remove-Item dev.db -ErrorAction SilentlyContinue   # bắt đầu từ DB sạch (sẽ tự seed)
$env:LLM_PROVIDER="stub"
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000

# Frontend (cửa sổ 2)
cd D:\claude\mathtutor\frontend
npm run dev
```

- Giao diện: http://localhost:5173 · API docs: http://127.0.0.1:8000/docs
- Tài khoản seed: `admin/admin123` · `gv1/gv123` · `hs1/hs123`

## 1. Dữ liệu seed (DATA_MODEL §9–10)

- 3 tài khoản (admin, gv1 thuộc lớp 12A1, hs1 thuộc lớp 12A1).
- **7 bài đã duyệt** trên 3 chuyên đề:
  | # | Chuyên đề | Loại | Mức |
  |---|-----------|------|-----|
  | 1 | Khảo sát hàm số | TLN | tb |
  | 2 | Khảo sát hàm số | TN4PA | de |
  | 3 | Khảo sát hàm số | TNDS | kho |
  | 4 | Nguyên hàm - Tích phân | TLN | tb |
  | 5 | Nguyên hàm - Tích phân | TN4PA | de |
  | 6 | Xác suất | TLN | tb |
  | 7 | Xác suất | TN4PA | de |

## 2. Kịch bản Học sinh (đăng nhập hs1)

### 2a. TLN nhiều bước — bài #1 (GTLN của $x^3-3x+2$ trên $[0;3]$)
1. **Chọn bài** → lọc loại "Trả lời ngắn" → Bắt đầu bài Khảo sát hàm số.
2. Gia sư mở đầu bằng câu hỏi định hướng (không lộ đáp án).
3. Vùng nhập TLN: gõ `3x^2-3` vào editor → bản render xác nhận hiện $3x^2-3$ → Gửi.
   → CAS chấm đúng, gia sư xác nhận và sang bước 2.
4. Gửi `1` (nghiệm trong đoạn) → sang bước 3.
5. Gửi `20` → **Hoàn thành**, điểm 1.0.
6. Thử nút **"Em chưa hiểu"** ở bước bất kỳ → gia sư nâng cấp gợi ý (không đọc kết quả).

### 2b. TN4PA — bài #2 (đồng biến)
1. Chọn bài TN4PA → chọn phương án **B** → Gửi → Hoàn thành, điểm 1.0.
2. (Tùy chọn) chọn sai trước để thấy gia sư hỏi ngược, không phán "sai".

### 2c. TNDS bậc thang — bài #3 ($f(x)=2\cos x+x$)
1. Lần lượt trả lời 4 mệnh đề: **a) Đúng · b) Đúng · c) Đúng · d) Sai**.
2. Mỗi ý xong, thanh tiến trình a→d cập nhật; gia sư chuyển ý tự nhiên.
3. Hết 4 ý → màn **Kết thúc** hiển thị **4/4 mệnh đề đúng, điểm 1.0** (bậc thang).
4. Biến thể: trả lời 3 đúng → điểm 0.5; 2 đúng → 0.25 (kiểm bậc thang).

### 2d. Làm tiếp bài dở
1. Vào bài #4 (TLN Tích phân), gửi đúng bước 1 (`x^3`) rồi rời trang (về Trang chủ).
2. Trang chủ → mục "Bài đang làm dở" hiện bài #4 ở **Bước 2** → bấm **Làm tiếp** →
   hội thoại khôi phục đúng chỗ.

### 2e. Tiến độ
- Tab **Tiến độ**: bảng theo chuyên đề (số bài hoàn thành / đã làm, tỉ lệ đúng TB).

## 3. Kịch bản Giáo viên (đăng nhập gv1)

1. **Tổng quan:** thẻ số liệu (HS, câu đã duyệt, chờ duyệt, cờ) + chuyên đề lớp yếu.
2. **AI sinh câu hỏi:** chọn chuyên đề/loại/độ khó/số lượng → **Sinh** → xem bản nháp kèm
   cảnh báo (nếu có) → **Duyệt** một câu → câu chuyển sang Đã duyệt (HS sẽ thấy).
   - Số gợi ý nháp theo độ khó: de→2, tb→3, kho→4.
3. **Câu hỏi:** danh sách + lọc trạng thái duyệt; bấm **Xem** mở chi tiết (có đáp án cho GV).
4. **Cờ theo dõi:** hàng đợi cờ; bấm **Đã xử lý / Bỏ qua**.
5. **Tiến bộ học sinh:** bảng HS lớp 12A1 + biểu đồ chi tiết từng em.

## 4. Kịch bản Quản trị (đăng nhập admin)

1. **Dashboard:** thống kê toàn hệ thống (người dùng/câu hỏi/phiên/cờ) + nhà cung cấp LLM.
2. **Quản lý tài khoản:** tạo HS/GV mới → đăng nhập được; **Khóa** → tài khoản đó login bị chặn.
3. **Cấu hình:** đổi ngưỡng cờ, nhiệt độ LLM (lưu lại được); xem số gợi ý mặc định + bảng bậc thang.
4. **Nhật ký:** danh sách cờ/cảnh báo gần đây.
5. **Phân quyền:** HS/GV không truy cập được khu admin (API trả 403; UI không hiển thị).

## 5. Bất biến cần thấy trong demo

- Gia sư **không bao giờ** đọc đáp án/kết quả bước — chỉ hỏi gợi mở (lớp chốt chặn rà đầu ra).
- Đúng/sai do **CAS (SymPy)** và dữ liệu chuẩn quyết định, không phải LLM.
- HS không thấy trường đáp án trong mọi response (`/problems`, chi tiết phiên đã strip).

## 6. Chạy kiểm thử tự động

```powershell
cd D:\claude\mathtutor\backend && .\.venv\Scripts\pytest -q     # toàn bộ test lõi + API
cd D:\claude\mathtutor\frontend && npm run build                # build sản xuất
```
