# kiem-tra-truoc-khi-push.ps1 — Chạy ĐÚNG các job trong .github/workflows/ci.yml tại local,
# THEO ĐÚNG THỨ TỰ VÀ NỘI DUNG, để đảm bảo CI xanh TRƯỚC khi push — không suy đoán "thay đổi
# nhỏ chắc không ảnh hưởng" (chính suy đoán đó đã gây CI đỏ nhiều lần: v139 quên chạy eslint,
# v143 quên chạy e2e). File này là NGUỒN SỰ THẬT DUY NHẤT cho "an toàn để push" — nếu ci.yml
# đổi job thì sửa file này theo, đừng để 2 nơi lệch nhau.
#
# Được gọi tự động bởi Git hook .git/hooks/pre-push — KHÔNG cần nhớ chạy tay, nhưng vẫn có
# thể chạy tay để kiểm tra sớm: powershell -File scripts\kiem-tra-truoc-khi-push.ps1
#
# Exit code: 0 = mọi job xanh, an toàn push. 1 = còn lỗi, PHẢI sửa xong mới được push.

$ErrorActionPreference = 'Stop'
$root = 'D:\claude\mathtutor'
$loi = @()
$batDau = Get-Date

function Chay($ten, [scriptblock]$lenh) {
    Write-Host "`n=== $ten ===" -ForegroundColor Cyan
    try {
        & $lenh
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            throw "exit code $LASTEXITCODE"
        }
        Write-Host "OK: $ten" -ForegroundColor Green
    } catch {
        Write-Host "LOI: $ten -> $_" -ForegroundColor Red
        $script:loi += $ten
    }
}

# ---- job "backend" (ci.yml) ----
Set-Location "$root\backend"
Chay "backend: ruff check app/" { & .venv\Scripts\python.exe -m ruff check app/ }
Chay "backend: import smoke test" { & .venv\Scripts\python.exe -c "import app.main" }
Chay "backend: pytest -q" { & .venv\Scripts\python.exe -m pytest -q }

# ---- job "frontend" (ci.yml) ----
Set-Location "$root\frontend"
Chay "frontend: npm run lint" { npm run lint }
Chay "frontend: npm run test (vitest)" { npm run test }
Chay "frontend: npm run build" { npm run build }

# ---- job "e2e" (ci.yml) — job hay bị BỎ SÓT nhất vì tưởng "chỉ đổi UI nhỏ" ----
Chay "e2e: npx playwright test (3 luong vang)" { npx playwright test }

Set-Location $root
$thoiGian = [math]::Round(((Get-Date) - $batDau).TotalSeconds, 1)

Write-Host "`n===================================================="
if ($loi.Count -gt 0) {
    Write-Host "CON LOI ($($loi.Count)) - KHONG DUOC PUSH:" -ForegroundColor Red
    $loi | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "Sua xong roi chay lai script nay truoc khi push." -ForegroundColor Red
    exit 1
}
Write-Host "TAT CA XANH ($thoiGian s) - an toan de push." -ForegroundColor Green
exit 0
