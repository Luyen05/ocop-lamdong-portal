param(
  [string]$BackendUrl = 'http://localhost:8000',
  [string]$FrontendUrl = 'http://localhost:5173'
)

$ErrorActionPreference = 'Stop'

function Invoke-NativeStep {
  param(
    [string]$Name,
    [scriptblock]$Command
  )

  Write-Host "`n==> $Name" -ForegroundColor Cyan
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Name that bai voi ma loi $LASTEXITCODE."
  }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw 'Khong tim thay Docker. Hay mo Docker Desktop va thu lai.'
}

Invoke-NativeStep 'Kiem tra cau hinh Docker Compose' { docker compose config --quiet }
Invoke-NativeStep 'Kiem tra cac dich vu dang chay' { docker compose ps }
Invoke-NativeStep 'Chay kiem thu backend' { docker compose exec -T backend python -m pytest -q }
Invoke-NativeStep 'Chay kiem thu frontend' { docker compose exec -T frontend npm test }
Invoke-NativeStep 'Kiem tra TypeScript' { docker compose exec -T frontend npm run type-check }
Invoke-NativeStep 'Build frontend' { docker compose exec -T frontend npm run build }

Write-Host "`n==> Kiem tra API va giao dien" -ForegroundColor Cyan
$health = Invoke-RestMethod -Uri "$BackendUrl/health" -TimeoutSec 10
if ($health.status -ne 'ok') {
  throw 'Backend co phan hoi nhung health check khong hop le.'
}

$databaseHealth = Invoke-RestMethod -Uri "$BackendUrl/api/v1/health/database" -TimeoutSec 10
if ($databaseHealth.status -ne 'ok') {
  throw 'Ket noi database khong san sang.'
}

$products = Invoke-RestMethod -Uri "$BackendUrl/api/v1/products?page=1&page_size=1" -TimeoutSec 10
if ($null -eq $products.items -or $null -eq $products.total) {
  throw 'API san pham khong tra dung cau truc phan trang.'
}

$frontend = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 10
if ($frontend.StatusCode -ne 200) {
  throw "Frontend tra ma HTTP $($frontend.StatusCode)."
}

Write-Host "`nTat ca kiem tra MVP da thanh cong." -ForegroundColor Green
Write-Host "So san pham cong khai hien tai: $($products.total)"
