# ComicCraft - PowerShell Run Script
# Usage: Right-click > "Run with PowerShell"  OR  in terminal: .\run.ps1

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "    ComicCraft - AI Comic Story Creator" -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""

# ── Find Python ─────────────────────────────────────────────────────
$pythonPaths = @(
    "python",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:USERPROFILE\anaconda3\python.exe",
    "$env:USERPROFILE\miniconda3\python.exe",
    "C:\ProgramData\anaconda3\python.exe",
    "C:\ProgramData\miniconda3\python.exe"
)

$PYTHON = $null
foreach ($p in $pythonPaths) {
    try {
        $ver = & $p --version 2>&1
        if ($ver -match "Python 3\.(9|10|11|12|13)") {
            $PYTHON = $p
            Write-Host "[OK] Python found: $p ($ver)" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $PYTHON) {
    Write-Host "[ERROR] Python 3.10+ not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  IMPORTANT: Check 'Add Python to PATH' during install" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Create virtual environment ───────────────────────────────────────
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
    & $PYTHON -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create venv" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created." -ForegroundColor Green
}

# ── Activate venv ────────────────────────────────────────────────────
Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# ── Install dependencies ─────────────────────────────────────────────
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip -q
pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies ready." -ForegroundColor Green

# ── Check .env ───────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "[ACTION REQUIRED] Open .env and add your GEMINI_API_KEY" -ForegroundColor Yellow
    Write-Host "Get a free key at: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter after adding your key, then re-run this script"
    exit 0
}

# ── Create output dirs ───────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "static\panels", "static\exports" | Out-Null

# ── Start server ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ─────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "   App:      http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host "  ─────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
