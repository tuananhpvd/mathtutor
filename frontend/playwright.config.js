import { defineConfig } from '@playwright/test'

// E2E smoke — 3 "luồng vàng" chạy trên trình duyệt thật (xem e2e/luong-vang.spec.js).
//
// Chạy trên CẶP SERVER RIÊNG (backend 18000 + vite dev 15173, DB backend/e2e.db xóa tạo lại
// mỗi lần chạy) — hoàn toàn tách khỏi backend/frontend dev (8000/5173, dev.db) người dùng
// đang mở, không bao giờ đụng dữ liệu dev. Chạy: `npm run e2e` (cần .venv backend đã cài).
export const E2E_API = 'http://localhost:18000/api'

export default defineConfig({
  testDir: './e2e',
  // Các test dùng chung 1 DB e2e (xóa tạo lại MỖI LẦN CHẠY, không phải mỗi test) — chạy
  // tuần tự 1 worker để trạng thái giữa các test có thứ tự rõ ràng.
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: 'http://localhost:15173',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      // `del ... &` (không phải &&): xóa DB e2e cũ nếu có rồi LUÔN khởi động backend —
      // đảm bảo mỗi lần chạy e2e là DB mới seed lại từ đầu, kết quả lặp lại được.
      command: 'del e2e.db 2>nul & .venv\\Scripts\\python.exe -m uvicorn app.main:app --port 18000',
      cwd: '../backend',
      url: 'http://localhost:18000/api/health',
      env: { DATABASE_URL: 'sqlite:///./e2e.db' },
      reuseExistingServer: false,
      timeout: 90_000,
    },
    {
      command: 'npm run dev -- --port 15173 --strictPort',
      url: 'http://localhost:15173',
      env: { MT_API_PROXY: 'http://localhost:18000' },
      reuseExistingServer: false,
      timeout: 90_000,
    },
  ],
})
