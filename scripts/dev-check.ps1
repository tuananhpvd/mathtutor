# Kiểm tra ĐÁNG TIN CẬY trạng thái môi trường dev MathTutor — DÙNG THAY THẾ HOÀN TOÀN cho
# mọi lệnh netstat / Get-NetTCPConnection / grep CommandLine rời rạc trước đây, vốn:
#   - netstat/Get-NetTCPConnection có thể báo "vẫn LISTENING" TRỄ HƠN 1 PHÚT sau khi tiến
#     trình đã chết thật (đã gặp nhiều lần) → không bao giờ tự tin dựa vào chúng một mình.
#   - grep CommandLine dễ TỰ KHỚP NHẦM chính lệnh chẩn đoán đang chạy (vì lệnh đó chứa đúng
#     chuỗi đang tìm, ví dụ "uvicorn app.main" hay "dev-servers.ps1").
#   - Khởi động `dev-servers.ps1` nhiều lần mà không kiểm tra trước → nhiều supervisor
#     trùng lặp, tự khởi động lại backend chồng chéo, để lại tiến trình orphan giữ cổng.
#
# Cách xác định "khỏe & đúng code":
#   - HTTP OK (request thật, không tin socket table) VÀ
#   - PID đang phục vụ port PHẢI TRÙNG với PID do dev-servers.ps1 đã khởi động (ghi ra file
#     scripts/.pid/*) — nếu HTTP OK nhưng KHÔNG phải PID được quản lý, đó chính là dấu hiệu
#     "zombie/tiến trình thủ công đang âm thầm phục vụ code cũ" (đúng lỗi đã tốn nhiều thời
#     gian trước đây). KHÔNG so sánh mtime file với thời điểm khởi động — uvicorn --reload
#     giữ nguyên PID/start-time của reloader mỗi lần tự nạp lại, so kiểu đó sẽ báo sai liên tục.
#
# Dùng:
#   powershell -File scripts\dev-check.ps1            # chỉ báo cáo, không sửa gì
#   powershell -File scripts\dev-check.ps1 -Fix        # báo cáo rồi tự sửa nếu có vấn đề
#   powershell -File scripts\dev-check.ps1 -Fix -Wait  # sửa xong, chờ tới khi healthy hẳn
# Exit code: 0 = mọi thứ khỏe & đúng tiến trình được quản lý; 1 = còn vấn đề (xem output).

param([switch]$Fix, [switch]$Wait)

$ErrorActionPreference = 'SilentlyContinue'
$root = 'D:\claude\mathtutor'
$pidDir = "$root\scripts\.pid"

function Read-TrackedPid($name) {
  $f = "$pidDir\$name"
  if (Test-Path $f) {
    $p = Get-Content $f -EA SilentlyContinue
    if ($p -and (Get-Process -Id $p -EA SilentlyContinue)) { return [int]$p }
  }
  return $null
}

function Get-PortOwnerPid($port) {
  $c = Get-NetTCPConnection -LocalPort $port -State Listen -EA SilentlyContinue | Select-Object -First 1
  if ($c) { return [int]$c.OwningProcess }
  return $null
}

# Toàn bộ tiến trình con/cháu (đệ quy theo ParentProcessId) — bắt CHÍNH XÁC cả các tiến
# trình multiprocessing.spawn zombie giữ cổng dù cha (reloader) đã bị kill, bất kể chúng
# báo đường dẫn python.exe nào (đã gặp: hiện C:\PythonXXX thay vì venv của project).
function Get-ProcessTree($rootPid) {
  $all = Get-CimInstance Win32_Process
  $result = @($rootPid)
  $frontier = @($rootPid)
  while ($frontier.Count -gt 0) {
    $children = $all | Where-Object { $frontier -contains $_.ParentProcessId } |
      Select-Object -ExpandProperty ProcessId
    $children = $children | Where-Object { $result -notcontains $_ }
    $result += $children
    $frontier = $children
  }
  return $result
}
function Stop-ProcessTree($rootPid) {
  Get-ProcessTree $rootPid | ForEach-Object { Stop-Process -Id $_ -Force -EA SilentlyContinue }
}

function Test-Http($url) {
  try { return (Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing).StatusCode -eq 200 }
  catch { return $false }
}

# HTTP OK nhưng PID thực đang giữ cổng KHÔNG nằm trong cây tiến trình được quản lý (trackedPid)
# → đang có ai khác (zombie/thủ công) trả lời trên cổng đó, không phải server do ta kiểm soát —
# áp dụng cho CẢ backend lẫn frontend (frontend cũng từng gặp: kill `cmd.exe` cha nhưng con
# `node` mồ côi vẫn sống, tiếp tục phục vụ code cũ mà không ai theo dõi).
function Test-PortManaged($port, $trackedPid, $isOk) {
  if (-not $isOk) { return $true }  # DOWN không phải "quản lý sai", để nhánh riêng xử lý
  if (-not $trackedPid) { return $false }
  $owner = Get-PortOwnerPid $port
  $tree = Get-ProcessTree $trackedPid
  return -not ($owner -and ($tree -notcontains $owner))
}

function Report([switch]$Quiet) {
  $sup = Read-TrackedPid 'supervisor'
  $be = Read-TrackedPid 'backend'
  $fe = Read-TrackedPid 'frontend'
  $beOk = Test-Http 'http://127.0.0.1:8000/api/health'
  $feOk = Test-Http 'http://localhost:5173/'
  $beManaged = Test-PortManaged 8000 $be $beOk
  $feManaged = Test-PortManaged 5173 $fe $feOk

  if (-not $Quiet) {
    Write-Host "Supervisor: $(if ($sup) { "RUNNING (pid $sup)" } else { 'KHONG CHAY' })"
    Write-Host "Backend:    $(if ($beOk) { 'OK' } else { 'DOWN' })$(if ($be) { " (pid $be)" })$(if ($beOk -and -not $beManaged) { ' -- HTTP OK NHUNG LA TIEN TRINH LA (khong do supervisor quan ly) -> CHAY CODE CU' })"
    Write-Host "Frontend:   $(if ($feOk) { 'OK' } else { 'DOWN' })$(if ($fe) { " (pid $fe)" })$(if ($feOk -and -not $feManaged) { ' -- HTTP OK NHUNG LA TIEN TRINH LA (khong do supervisor quan ly) -> CHAY CODE CU' })"
  }

  [PSCustomObject]@{
    Sup = $sup; Be = $be; Fe = $fe; BeOk = $beOk; FeOk = $feOk; BeManaged = $beManaged; FeManaged = $feManaged
    Healthy = ([bool]$sup -and $beOk -and $beManaged -and $feOk -and $feManaged)
  }
}

$st = Report

if ($Fix -and -not $st.Healthy) {
  Write-Host "`n-- Dang sua --"
  if (-not $st.Sup) {
    # Không có supervisor theo PID file — dọn sạch MỌI bản trùng lỡ chạy trước đó (kể cả
    # file PID hỏng/cũ) rồi khởi động ĐÚNG 1 bản mới. Đây là nơi DUY NHẤT còn dò CommandLine,
    # chỉ chạy 1 lần lúc sửa (không phải mỗi lần kiểm tra) nên rủi ro tự khớp nhầm không đáng kể.
    Get-CimInstance Win32_Process |
      Where-Object { $_.CommandLine -like '*dev-servers.ps1*' -and $_.Name -eq 'powershell.exe' } |
      ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }
    Remove-Item "$pidDir\*" -Force -EA SilentlyContinue
    Start-Process -WindowStyle Hidden powershell -ArgumentList `
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$root\scripts\dev-servers.ps1"
    Write-Host "Da khoi dong 1 supervisor moi."
  }

  # QUAN TRỌNG: kiểm backend/frontend ĐỘC LẬP với nhánh supervisor ở trên, KHÔNG else —
  # 2 vấn đề (thiếu supervisor + có zombie chiếm cổng) có thể xảy ra ĐỒNG THỜI. Nếu chỉ xử
  # lý 1 trong 2 (else loại trừ), supervisor mới khởi động sẽ thấy cổng "đã có người nghe"
  # (zombie) rồi bỏ qua không tự bật backend — kẹt vĩnh viễn (đã tự kiểm chứng gặp đúng lỗi
  # này khi test lần đầu).
  if (-not $st.BeOk -or -not $st.BeManaged) {
    # Luôn kill theo PID THỰC ĐANG GIỮ CỔNG (không chỉ theo file PID cũ có thể đã lệch) +
    # toàn bộ cây con của nó — xử lý đúng cả trường hợp zombie lẫn tracked-nhưng-chết.
    $owner = Get-PortOwnerPid 8000
    if ($owner) { Stop-ProcessTree $owner }
    if ($st.Be) { Stop-ProcessTree $st.Be }
    Remove-Item "$pidDir\backend" -Force -EA SilentlyContinue
    Write-Host "Da kill backend (ca tien trinh la/con) - supervisor tu bat lai trong ~5s."
  }
  if (-not $st.FeOk -or -not $st.FeManaged) {
    $owner = Get-PortOwnerPid 5173
    if ($owner) { Stop-ProcessTree $owner }
    if ($st.Fe) { Stop-ProcessTree $st.Fe }
    Remove-Item "$pidDir\frontend" -Force -EA SilentlyContinue
    Write-Host "Da kill frontend (ca tien trinh la/con) - supervisor tu bat lai trong ~5s."
  }

  if ($Wait) {
    Write-Host "`n-- Cho toi khi healthy (toi da 40s) --"
    $ok = $false
    for ($i = 0; $i -lt 20; $i++) {
      Start-Sleep -Seconds 2
      $st = Report -Quiet
      if ($st.Healthy) { $ok = $true; break }
    }
    $st = Report
    Write-Host $(if ($ok) { "`nOK - moi truong da san sang." } else { "`nVAN CHUA HEALTHY sau 40s - xem lai output tren." })
  }
}

exit $(if ($st.Healthy) { 0 } else { 1 })
