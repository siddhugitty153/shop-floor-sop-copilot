# BiztelAI SOP Copilot - PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "BiztelAI SOP Copilot Launcher"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  BiztelAI Shop-Floor SOP Copilot - PowerShell Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/2] Starting FastAPI Backend on http://0.0.0.0:8000 ..." -ForegroundColor Yellow
$BackendCmd = "cd '$ScriptDir'; `$env:PYTHONPATH='backend'; & '$ScriptDir\backend\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Vite React Frontend on http://0.0.0.0:5173 ..." -ForegroundColor Yellow
$FrontendCmd = "cd '$ScriptDir\frontend'; npm run dev -- --host 0.0.0.0 --port 5173"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  SERVICES ARE RUNNING!" -ForegroundColor Green
Write-Host "  - Laptop Browser: http://localhost:5173" -ForegroundColor White
Write-Host "  - Phone on Wi-Fi: http://192.168.1.3:5173" -ForegroundColor White
Write-Host "  - Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to close this launcher (servers will keep running in their own windows)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

