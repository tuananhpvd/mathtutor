# UIUX_DESIGN.md — Hướng dẫn thiết kế UI/UX & quy trình Claude Design

Mục tiêu: giao diện đẹp, hiện đại, chuyên nghiệp, nhất quán cho ba vai trò. Dùng ở Phase 7
(định hình hệ thống thiết kế) và áp dụng ở Phase 8–10.

## 1. Nguyên tắc thiết kế

- **Rõ ràng trước hết.** Đối tượng gồm học sinh và giáo viên không chuyên công nghệ. Ưu tiên dễ
  hiểu, ít bước, nhãn tiếng Việt rõ.
- **Bình tĩnh, tập trung.** Phòng học là nơi suy nghĩ — nền dịu, ít nhiễu, công thức nổi bật.
- **Phân biệt vai trò bằng bố cục, không bằng màu lòe loẹt.** HS thân thiện ấm; GV/Admin thiên
  dữ liệu, bảng, biểu đồ.
- **Công thức là công dân hạng nhất.** Render KaTeX sạch, cỡ chữ đủ lớn, không vỡ dòng xấu.
- **Phản hồi tức thì.** Trạng thái chờ (gia sư đang soạn câu hỏi), nhãn đúng/sai bước, badge
  trạng thái bài (đang làm/hoàn thành) phải thấy ngay.

## 2. Design tokens (đề xuất, Phase 7 chốt lại)

- **Màu:**
  - Nền chính: trắng ngà / xám rất nhạt (vd `#FAFAF8`).
  - Nhấn chính (primary): tím trí tuệ (vd `#5B4BDA`) — dùng cho nút chính, liên kết.
  - Thành công/đúng: xanh lá dịu (`#1F9D6B`). Cảnh báo/sai nhẹ: hổ phách (`#C77D14`)
    — KHÔNG dùng đỏ gắt khi HS trả lời sai (tránh gây nản); đỏ chỉ cho lỗi hệ thống.
  - Trung tính chữ: `#2C2C2A`; phụ: `#6B6A66`.
- **Typography:** một font sans dễ đọc (Inter/Be Vietnam Pro). Cỡ gốc 16px; tiêu đề rõ thang bậc.
- **Spacing:** thang 4/8/12/16/24/32. **Radius:** 8–12px (mềm, hiện đại). **Shadow:** nhẹ, 1 lớp.
- Lưu thành biến CSS/Tailwind theme ở `frontend/src/styles`.

## 3. Thành phần dùng lại (Phase 7 dựng)

Button (primary/secondary/ghost), Card, Input, Select, Badge trạng thái (đang làm/hoàn thành/
chờ duyệt/đã duyệt), Table (cho GV/Admin), ProgressChart (tiến độ HS), RoleLayout (khung 3 vai trò
với sidebar/topbar riêng), Formula (KaTeX), FormulaEditor (MathLive), ChatBubble (HS/gia sư).

## 4. Quy trình dùng Claude Design (tùy chọn nhưng khuyến nghị cho 4 màn hình trụ cột)

Claude Design là công cụ tạo và lặp giao diện trên canvas qua chat. Quy trình đề xuất:

1. **Tạo thiết kế ở Claude Design** cho 4 màn hình trụ cột, mỗi màn hình một prompt mô tả rõ:
   - **Login:** đơn giản, 1 form, chọn vai trò ngầm theo tài khoản, tông tím trí tuệ.
   - **PhòngHọc (HS):** layout 2 phần — khung hội thoại bên trái (bong bóng chat HS/gia sư,
     công thức render), vùng nhập đáp án bên phải đổi theo loại câu (4 nút A/B/C/D; hoặc 4 dòng
     a–d Đúng/Sai; hoặc ô nhập + editor công thức + bản render xác nhận), nút "Em chưa hiểu".
   - **Dashboard GV:** thẻ số liệu (HS, bài, cờ chưa xử lý), bảng theo dõi tiến bộ, biểu đồ
     chuyên đề yếu.
   - **Dashboard Admin:** thẻ thống kê toàn hệ thống, bảng tài khoản, khu cấu hình.
2. **Tinh chỉnh** màu/spacing/bố cục trong Claude Design cho khớp tokens mục 2.
3. **Xuất/chụp thiết kế**, đưa cho Claude Code ở Phase 7 kèm yêu cầu: "chuyển thiết kế này thành
   component React + Tailwind dùng đúng design tokens trong frontend/src/styles".
4. Claude Code dựng component, chạy build, đối chiếu thị giác, tinh chỉnh.

> Nếu không dùng Claude Design: ở Phase 7 yêu cầu Claude Code tự đề xuất thiết kế theo tokens và
> mô tả 4 màn hình ở trên, rồi dựng component.

## 5. Gợi ý bố cục theo vai trò

- **HS:** topbar mỏng (tên, tiến độ nhanh), nội dung trung tâm rộng, ít menu. Cảm giác như một
  ứng dụng học tập nhẹ nhàng.
- **GV:** sidebar trái (Câu hỏi / AI sinh / Cờ / Học sinh / Tiến bộ), nội dung bảng + biểu đồ.
- **Admin:** sidebar trái (Dashboard / Tài khoản / Cấu hình / Nhật ký), nhấn vào số liệu tổng.

## 6. Khả năng truy cập & responsive

- Tương phản đạt mức đọc tốt; vùng bấm đủ lớn cho tablet.
- Ưu tiên desktop/laptop và tablet; mobile chỉ cần dùng được (không vỡ layout).
- Công thức không tràn ngang gây cuộn khó chịu; cho cuộn riêng vùng công thức dài nếu cần.

## 7. Tiêu chí "đẹp & chuyên nghiệp" để tự đánh giá ở Phase 7–10

- Nhất quán: mọi trang dùng cùng tokens và component, không lệch màu/spacing.
- Khoảng thở: đủ trắng, không nhồi nhét.
- Thứ bậc thị giác rõ: mắt biết nhìn đâu trước.
- Trạng thái đầy đủ: loading, rỗng (chưa có bài/chưa có cờ), lỗi, thành công.
- Phòng học khiến học sinh muốn tập trung, không phân tán.
