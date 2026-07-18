// Khởi động backend cho E2E, cross-platform (Windows dev lẫn Ubuntu CI) — thay lệnh shell
// Windows-only trước đây (`del`, `.venv\Scripts\python.exe`) không chạy được trên CI Linux.
import { existsSync, rmSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import process from 'node:process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const backendDir = path.resolve(__dirname, '..', '..', 'backend')

// Xóa DB e2e cũ nếu có — mỗi lần chạy là DB mới seed lại từ đầu, kết quả lặp lại được.
const dbPath = path.join(backendDir, 'e2e.db')
if (existsSync(dbPath)) rmSync(dbPath)

// Dev local có .venv (Windows: Scripts/python.exe, POSIX: bin/python); CI không có venv,
// deps cài thẳng vào Python hệ thống qua `pip install -e ".[llm,dev]"` — dùng python3 trên PATH.
const venvPython = process.platform === 'win32'
  ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
  : path.join(backendDir, '.venv', 'bin', 'python')
const python = existsSync(venvPython) ? venvPython : (process.platform === 'win32' ? 'python' : 'python3')

const child = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--port', '18000'], {
  cwd: backendDir,
  stdio: 'inherit',
  env: process.env,
})

child.on('exit', (code) => process.exit(code ?? 0))
process.on('SIGTERM', () => child.kill())
process.on('SIGINT', () => child.kill())
