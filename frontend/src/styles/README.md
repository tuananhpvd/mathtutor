# Hệ thống thiết kế MathTutor (Phase 7)

Tài liệu ngắn cho design system. Chi tiết nguyên tắc: `docs/UIUX_DESIGN.md`.

## Design tokens — `theme.css`
Khai báo trong `@theme` của Tailwind v4 → sinh utility tự động.

| Nhóm | Token | Giá trị | Utility ví dụ |
|------|-------|---------|---------------|
| Nền | `--color-bg` | `#FAFAF8` | `bg-bg` |
| Bề mặt | `--color-surface` / `--color-surface-2` | trắng / `#F4F3EF` | `bg-surface` |
| Nhấn | `--color-primary` | `#5B4BDA` (tím trí tuệ) | `bg-primary`, `text-primary` |
| Thành công | `--color-success` | `#1F9D6B` | `text-success`, `bg-success-soft` |
| Cảnh báo (sai nhẹ) | `--color-warning` | `#C77D14` (hổ phách, KHÔNG đỏ gắt) | `text-warning` |
| Lỗi hệ thống | `--color-danger` | `#DC2626` | `text-danger` |
| Chữ | `--color-ink` / `--color-muted` | `#2C2C2A` / `#6B6A66` | `text-ink`, `text-muted` |
| Viền | `--color-border` | `#E7E5E0` | `border-border` |
| Vai trò | `--color-hs/gv/admin` | tím / xanh mòng két / chàm | `text-gv` |
| Bo góc | `--radius-card` | 12px | `rounded-card` |
| Bóng | `--shadow-card` | nhẹ 1 lớp | `shadow-[var(--shadow-card)]` |

**Font:** Be Vietnam Pro (Google Fonts) → fallback Inter/system-ui. Cỡ gốc 16px.

## Component dùng lại — `src/components/ui/`
`Button` (primary/secondary/ghost/success · sm/md/lg) · `Card` (+ `CardHeader`,
`CardBody`, `StatCard`) · `Input` · `Select` · `Badge` (theo `trang_thai` nghiệp vụ
hoặc `tone`) · `Table` (columns/rows/empty) · `ProgressChart` (thuần CSS) ·
`ChatBubble` (+ `TypingBubble`). Công thức: `Formula` (KaTeX), `FormulaEditor` (MathLive).

Import gọn: `import { Button, Card, Badge } from '../../components/ui'`.

## Bố cục theo vai trò — `RoleLayout.jsx`
- **HS:** topbar mỏng, nội dung trung tâm rộng (cảm giác app học tập nhẹ).
- **GV/Admin:** sidebar trái điều hướng + topbar tiêu đề, nội dung bảng/biểu đồ.

## 4 màn hình trụ cột (phác Phase 7, nối API ở Phase 8–10)
Login · PhòngHọc HS (hội thoại + vùng nhập đổi theo loại câu + "Em chưa hiểu") ·
Dashboard GV · Dashboard Admin.

## Nguyên tắc khi dựng trang mới
1. Chỉ dùng token/utility ngữ nghĩa, KHÔNG hard-code hex.
2. Tái dùng component `ui/`, không tự viết lại button/card.
3. Đủ trạng thái: loading, rỗng, lỗi, thành công.
4. Sai của HS dùng hổ phách, không đỏ gắt; đỏ chỉ cho lỗi hệ thống.
