# Hệ thống thiết kế MathTutor (Phase 7)

Tài liệu ngắn cho design system. Chi tiết nguyên tắc: `docs/UIUX_DESIGN.md`.

## Design tokens — `theme.css`
Khai báo trong `@theme` của Tailwind v4 → sinh utility tự động.

| Nhóm | Token | Giá trị | Utility ví dụ |
|------|-------|---------|---------------|
| Nền | `--color-bg` | `#f6f6fc` | `bg-bg` |
| Bề mặt | `--color-surface` / `--color-surface-2` | trắng / `#efeef9` | `bg-surface` |
| Nhấn (điều hướng, thương hiệu) | `--color-primary` | `#3b36cc` (indigo học thuật) | `bg-primary`, `text-primary` |
| CTA (hành động chính) | `--color-cta` | `#ff5a1f` (cam) — CHỈ dùng cho nút hành động chính (Lưu/Gửi/Đăng nhập), không dùng cho điều hướng | `bg-cta` |
| AI / tính năng thông minh | `--color-accent` | `#8b5cf6` | `text-accent`, `bg-accent-soft` |
| Thành công | `--color-success` | `#16a34a` | `text-success`, `bg-success-soft` |
| Cảnh báo (sai nhẹ) | `--color-warning` | `#f59e0b` (chữ dùng `--color-warning-ink: #7a4e06` để đủ tương phản trên nền warning) | `text-warning` |
| Lỗi hệ thống | `--color-danger` | `#e11d48` | `text-danger` |
| Chưa làm / chưa có dữ liệu | `--color-idle` | `#6f6b86` (xám, KHÔNG dùng đỏ) | `text-idle`, `bg-idle-soft` |
| Chữ | `--color-ink` / `--color-muted` | `#181430` / `#6b6785` | `text-ink`, `text-muted` |
| Viền | `--color-border` | `#e4e3f2` | `border-border` |
| Vai trò | `--color-hs` / `--color-gv` / `--color-admin` | `#3b36cc` / `#1f7a8c` / `#3b3a55` | `text-gv` |
| Bo góc | `--radius-sm/md/lg/card` | 8 / 10 / 12 / 12px | `rounded-card` |
| Bóng | `--shadow-card` / `--shadow-pop` | nhẹ 2 lớp, nhuộm theo `ink` | `shadow-[var(--shadow-card)]` |

**Font:** Be Vietnam Pro (Google Fonts) → fallback Inter/system-ui. Cỡ gốc 17px (`--text-base`, tăng +1px so với mặc định Tailwind để dễ đọc).

## Component dùng lại — `src/components/ui/`
`Button` (variant: `primary`/`secondary`/`ghost`/`success`/`warning`/`danger`/`indigo`/`warningSoft` · size `sm`/`md`/`lg`) · `Card` (+ `CardHeader`, `CardBody`, `StatCard`) · `Input` · `Select` · `Badge` (theo `trang_thai` nghiệp vụ — ưu tiên dùng preset này thay vì tự set `tone` + text viết hoa tay — hoặc `tone` cho badge tự do) · `Table` (columns/rows/empty) · `ProgressChart` (thuần CSS) · `ChatBubble` (+ `TypingBubble`). Công thức: `Formula` (KaTeX), `FormulaEditor` (MathLive).

Import gọn: `import { Button, Card, Badge } from '../../components/ui'`.

## Bố cục theo vai trò — `RoleLayout.jsx`
- **HS:** topbar mỏng (pill nav desktop, bottom tab bar mobile) — cảm giác app học tập nhẹ.
- **GV/Admin:** sidebar trái điều hướng (icon-only ở tablet, đầy đủ chữ ở desktop, drawer ở mobile) + topbar tiêu đề, nội dung bảng/biểu đồ.

## Icon
Dùng **`lucide-react`** cho MỌI icon chức năng (nút, nhãn thẻ, trạng thái, tiêu đề card — xem cách dùng trong `RoleLayout.jsx`, `TongQuan.jsx`, `Dashboard.jsx`). KHÔNG dùng emoji làm icon chức năng hay trong tooltip biểu đồ. Emoji chỉ chấp nhận trong câu chào thuần văn bản (vd "Chào em 👋"), không thay thế icon.

## Màu sắc
- Tối đa 1 màu CTA cam nổi bật trên mỗi màn hình cho hành động chính; các nút khác trong cùng nhóm dùng `secondary` đồng nhất, không phối nhiều variant màu (`warning`/`indigo`/`success`) cạnh nhau trừ khi thể hiện đúng trạng thái nghiệp vụ khác nhau.
- KHÔNG hard-code hex trong JSX (vd `bg-[#f2f1fd]`, `border-[#2596be]`) — nếu cần 1 sắc thái mới, thêm token vào `theme.css` rồi dùng qua utility, để mọi nơi cùng tham chiếu 1 nguồn.
- Thang màu biểu đồ nhiệt/legend riêng (vd bản đồ năng lực, hiệu quả phương pháp) nên khai báo dùng chung 1 lần (hằng số export từ 1 file, vd `utils/chartColors.js`) thay vì lặp lại mảng hex trong từng component.

## 4 màn hình trụ cột (phác Phase 7, nối API ở Phase 8–10)
Login · PhòngHọc HS (hội thoại + vùng nhập đổi theo loại câu + "Em chưa hiểu") ·
Dashboard GV · Dashboard Admin.

## Nguyên tắc khi dựng trang mới
1. Chỉ dùng token/utility ngữ nghĩa, KHÔNG hard-code hex.
2. Tái dùng component `ui/`, không tự viết lại button/card.
3. Icon chức năng luôn dùng `lucide-react`, không emoji.
4. Đủ trạng thái: loading, rỗng, lỗi, thành công.
5. Sai của HS dùng hổ phách, không đỏ gắt; đỏ chỉ cho lỗi hệ thống.
