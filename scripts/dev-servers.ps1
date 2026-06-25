# Giám sát dev MathTutor: giữ backend (8000) + frontend (5173) luôn chạy,
# và tự TẮT cả hai khi đóng VS Code (không còn tiến trình "Code").
# Chạy detached (không bị Claude/harness theo dõi) nên KHÔNG gửi thông báo đánh thức chat.
$ErrorActionPreference = 'SilentlyContinue'
$root = 'D:\claude\mathtutor'

function Test-Port($p) {
  [bool](Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue)
}
function Kill-Port($p) {
  Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }
}
function Start-Backend {
  Start-Process -WindowStyle Hidden -WorkingDirectory "$root\backend" `
    -FilePath "$root\backend\.venv\Scripts\python.exe" `
    -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--reload','--reload-dir','app'
}
function Start-Frontend {
  Start-Process -WindowStyle Hidden -WorkingDirectory "$root\frontend" `
    -FilePath 'cmd.exe' -ArgumentList '/c','npm run dev'
}

# Vòng giám sát: VS Code còn mở thì giữ server sống; đóng VS Code thì tắt server rồi thoát.
while ($true) {
  if (-not (Get-Process -Name 'Code' -EA SilentlyContinue)) {
    Kill-Port 8000
    Kill-Port 5173
    break
  }
  if (-not (Test-Port 8000)) { Start-Backend }
  if (-not (Test-Port 5173)) { Start-Frontend }
  Start-Sleep -Seconds 5
}
