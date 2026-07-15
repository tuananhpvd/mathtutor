# Giám sát dev MathTutor: giữ backend (8000) + frontend (5173) luôn chạy,
# và tự TẮT cả hai khi đóng VS Code (không còn tiến trình "Code").
# Chạy detached (qua Start-Process), harness KHÔNG theo dõi → không có thông báo đánh thức chat.
#
# Ghi PID ra file (scripts/.pid/*) để dev-check.ps1 xác minh CHÍNH XÁC — KHÔNG dò theo
# CommandLine (dễ tự khớp nhầm chính lệnh chẩn đoán đang chạy, và netstat/Get-NetTCPConnection
# có thể báo trạng thái trễ hơn 1 phút sau khi tiến trình đã chết thật).
$ErrorActionPreference = 'SilentlyContinue'
$root = 'D:\claude\mathtutor'
$pidDir = "$root\scripts\.pid"
New-Item -ItemType Directory -Force -Path $pidDir | Out-Null
Set-Content "$pidDir\supervisor" $PID

function Test-Port($p) {
  [bool](Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue)
}
function Kill-Port($p) {
  Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }
}
function Start-Backend {
  $p = Start-Process -WindowStyle Hidden -WorkingDirectory "$root\backend" `
    -FilePath "$root\backend\.venv\Scripts\python.exe" `
    -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--reload','--reload-dir','app' `
    -PassThru
  Set-Content "$pidDir\backend" $p.Id
}
function Start-Frontend {
  $p = Start-Process -WindowStyle Hidden -WorkingDirectory "$root\frontend" `
    -FilePath 'cmd.exe' -ArgumentList '/c','npm run dev' -PassThru
  Set-Content "$pidDir\frontend" $p.Id
}

# Vòng giám sát: VS Code còn mở thì giữ server sống; đóng VS Code thì tắt server rồi thoát.
while ($true) {
  if (-not (Get-Process -Name 'Code' -EA SilentlyContinue)) {
    Kill-Port 8000
    Kill-Port 5173
    Remove-Item "$pidDir\*" -Force -EA SilentlyContinue
    break
  }
  if (-not (Test-Port 8000)) { Start-Backend }
  if (-not (Test-Port 5173)) { Start-Frontend }
  Start-Sleep -Seconds 5
}
