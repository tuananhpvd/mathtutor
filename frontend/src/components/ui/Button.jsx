const VARIANTS = {
  // "primary" = hành động chính của màn hình (Lưu, Gửi, Xác nhận, Đăng nhập...) — dùng
  // riêng màu CTA cam, KHÔNG dùng --color-primary (Indigo dành cho điều hướng/nhận diện).
  primary: 'bg-cta text-white shadow-sm hover:bg-cta-hover hover:shadow disabled:opacity-50 disabled:shadow-none',
  secondary:
    'bg-surface text-ink border border-border hover:bg-surface-2 hover:border-border disabled:opacity-50',
  ghost: 'bg-transparent text-primary hover:bg-primary-soft disabled:opacity-50',
  success: 'bg-success text-white shadow-sm hover:opacity-90 disabled:opacity-50 disabled:shadow-none',
  // Chữ TỐI (không phải trắng) — nền vàng cam quá sáng, chữ trắng gần như không đọc
  // được (~2.2:1); chữ tối đạt ~8.3:1. Xem theme.css --color-warning-ink.
  warning: 'bg-warning text-warning-ink shadow-sm hover:opacity-90 disabled:opacity-50 disabled:shadow-none',
  danger: 'bg-danger text-white shadow-sm hover:opacity-90 disabled:opacity-50 disabled:shadow-none',
  // "indigo" = nền Indigo Học Đường (--color-primary). Theo yêu cầu dùng cho vài nút điều
  // hướng/gửi trong phòng học (Gửi câu hỏi, Quay lại làm sau).
  indigo: 'bg-primary text-white shadow-sm hover:opacity-90 disabled:opacity-50 disabled:shadow-none',
  // "warningSoft" = nền cam NHẠT (warning-soft) + chữ tối — cho nút trạng thái mềm (vd
  // "Đã dùng hết gợi ý").
  warningSoft: 'bg-warning-soft text-warning-ink border border-warning/40 hover:opacity-90 disabled:opacity-50',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-5 py-3 text-base',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium
        transition-all duration-150 active:scale-[0.98] focus:outline-none focus:ring-2
        focus:ring-primary/40 disabled:cursor-not-allowed disabled:active:scale-100
        ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    />
  )
}
