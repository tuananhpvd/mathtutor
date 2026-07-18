import * as Sentry from '@sentry/react'

// Bắt lỗi JS runtime phía HS/GV — hiện chỉ nằm trong console trình duyệt của người dùng,
// không ai thấy để sửa. KHÔNG khởi tạo gì nếu chưa cấu hình VITE_SENTRY_DSN (an toàn mặc
// định cho dev/chưa đăng ký Sentry — không phát request nào ra ngoài, không lỗi console).
export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  })
}

// baoLoi an toàn khi gọi dù initSentry() chưa chạy/chưa có DSN — captureException tự no-op.
export function baoLoi(error, info) {
  Sentry.captureException(error, { extra: info })
}
