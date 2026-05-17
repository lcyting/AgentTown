# 使用项目虚拟环境启动后端（确保依赖一致）
$ErrorActionPreference = "Stop"
$BackendRoot = $PSScriptRoot
$Python = Join-Path $BackendRoot "venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "未找到 venv，请先创建虚拟环境：" -ForegroundColor Yellow
    Write-Host "  cd `"$BackendRoot`""
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

Write-Host "Python: $Python" -ForegroundColor DarkGray
& $Python -m pip install -q -r (Join-Path $BackendRoot "requirements.txt")
Set-Location $BackendRoot
& $Python main.py
