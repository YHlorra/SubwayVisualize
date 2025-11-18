Write-Host "[轨住图谱] 初始化依赖并启动Flask" -ForegroundColor Cyan

# 依赖安装（使用根目录 requirements.txt）
if (Test-Path "requirements.txt") {
  Write-Host "[Deps] 安装依赖..." -ForegroundColor Yellow
  pip install -r requirements.txt | Out-Null
}

Write-Host "[Frontend] 跳过前端依赖安装（使用Flask模板页面）" -ForegroundColor Yellow

Write-Host "[Backend] 启动 Flask 服务 : http://127.0.0.1:5000" -ForegroundColor Green
$envPath = Join-Path $PSScriptRoot '.env'
if (Test-Path $envPath) {
  try {
    $line = Select-String -Path $envPath -Pattern '^FIRECRAWL_API_KEY=(.+)$' | Select-Object -First 1
    if ($line -and $line.Matches.Count -gt 0) {
      $key = $line.Matches[0].Groups[1].Value.Trim()
      if ($key) { $env:FIRECRAWL_API_KEY = $key }
    }
  } catch {}
}
Start-Process -FilePath python -ArgumentList "serve.py"
Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:5000/"
Write-Host "[OK] 已启动，浏览器访问 http://127.0.0.1:5000/" -ForegroundColor Cyan
