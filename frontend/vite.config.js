import process from 'node:process'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// E2E (Playwright) chạy backend RIÊNG trên port khác để không đụng backend dev (dev.db)
// đang chạy của người dùng — cho phép đổi đích proxy qua env, mặc định giữ nguyên 8000.
const API_PROXY = process.env.MT_API_PROXY || 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': API_PROXY,
      '/uploads': API_PROXY,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    // e2e/ là spec của Playwright (chạy bằng `npm run e2e`) — vitest không được bắt nhầm
    // (pattern mặc định *.spec.js của vitest sẽ quét trúng nếu không loại trừ).
    exclude: ['node_modules/**', 'e2e/**'],
  },
})
