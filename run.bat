@echo off
TITLE ComicCraft – AI Comic Story Creator
echo.
echo  ==============================================
echo    ComicCraft – AI Comic Story Creator
echo  ==============================================
echo.

REM ─── Detect Python from multiple possible locations ───────────────
SET PYTHON_EXE=

REM Check standard PATH first
where python >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    FOR /F "delims=" %%i IN ('where python 2^>nul') DO (
        SET PYTHON_EXE=%%i
        GOTO :python_found
    )
)

REM Check common install directories
IF EXIST "%USERPROFILE%\Python311\python.exe" SET PYTHON_EXE=%USERPROFILE%\Python311\python.exe & GOTO :python_found
IF EXIST "C:\Python312\python.exe"  SET PYTHON_EXE=C:\Python312\python.exe  & GOTO :python_found
IF EXIST "C:\Python311\python.exe"  SET PYTHON_EXE=C:\Python311\python.exe  & GOTO :python_found
IF EXIST "C:\Python310\python.exe"  SET PYTHON_EXE=C:\Python310\python.exe  & GOTO :python_found
IF EXIST "C:\Python39\python.exe"   SET PYTHON_EXE=C:\Python39\python.exe   & GOTO :python_found
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" SET PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe & GOTO :python_found
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" SET PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe & GOTO :python_found
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" SET PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe & GOTO :python_found
IF EXIST "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"  SET PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python39\python.exe  & GOTO :python_found

REM Check Anaconda/Miniconda
IF EXIST "%USERPROFILE%\anaconda3\python.exe"  SET PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe  & GOTO :python_found
IF EXIST "%USERPROFILE%\miniconda3\python.exe" SET PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe & GOTO :python_found
IF EXIST "C:\ProgramData\anaconda3\python.exe" SET PYTHON_EXE=C:\ProgramData\anaconda3\python.exe & GOTO :python_found
IF EXIST "C:\ProgramData\miniconda3\python.exe" SET PYTHON_EXE=C:\ProgramData\miniconda3\python.exe & GOTO :python_found

REM Not found – guide user
echo [ERROR] Python 3.10 or higher is required but was not found.
echo.
echo  Please install Python:
echo    1. Download from: https://www.python.org/downloads/
echo    2. IMPORTANT: Check "Add Python to PATH" during installation
echo    3. Re-run this script after installation
echo.
echo  Or if you have Anaconda/Miniconda:
echo    Open "Anaconda Prompt" and run:
echo      cd /d "%~dp0"
echo      pip install -r requirements.txt
echo      uvicorn app.main:app --reload
echo.
pause
EXIT /B 1

:python_found
echo [OK] Found Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

REM ─── Check/Create virtual environment ─────────────────────────────
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [*] Creating virtual environment...
    "%PYTHON_EXE%" -m venv venv
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        EXIT /B 1
    )
    echo [OK] Virtual environment created.
)

REM ─── Activate venv ────────────────────────────────────────────────
echo [*] Activating virtual environment...
CALL venv\Scripts\activate.bat

REM ─── Install / upgrade dependencies ───────────────────────────────
echo [*] Installing/verifying dependencies (this may take a few minutes first time)...
pip install --upgrade pip -q
pip install -r requirements.txt -q
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to install dependencies.
    echo         Try running:  pip install -r requirements.txt
    pause
    EXIT /B 1
)
echo [OK] All dependencies ready.

REM ─── Check for .env file ──────────────────────────────────────────
IF NOT EXIST ".env" (
    echo.
    echo [WARN] No .env file found – copying from .env.example...
    COPY .env.example .env
    echo.
    echo [ACTION REQUIRED]
    echo  Open the .env file and fill in your API keys:
    echo    GEMINI_API_KEY=your_actual_key_here
    echo    HF_API_KEY=your_actual_key_here   (optional)
    echo.
    echo  Get a FREE Gemini key at: https://aistudio.google.com/app/apikey
    echo.
    echo  Then run this script again.
    echo.
    pause
    EXIT /B 0
)

REM ─── Verify GEMINI_API_KEY is set ─────────────────────────────────
FINDSTR /C:"your_gemini_api_key_here" .env >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo.
    echo [WARN] GEMINI_API_KEY is still set to the placeholder value.
    echo.
    echo  Open .env and replace:
    echo    GEMINI_API_KEY=your_gemini_api_key_here
    echo  with your actual key from: https://aistudio.google.com/app/apikey
    echo.
    echo  The app will start but comic generation will fail without a valid key.
    echo.
)

REM ─── Create output directories ────────────────────────────────────
IF NOT EXIST "static\panels"  MKDIR "static\panels"
IF NOT EXIST "static\exports" MKDIR "static\exports"

REM ─── Start the server ─────────────────────────────────────────────
echo.
echo [*] Starting ComicCraft server...
echo.
echo  ──────────────────────────────────────────────────────
echo   Open your browser at:  http://127.0.0.1:8000
echo   API Docs (Swagger):    http://127.0.0.1:8000/docs
echo   Health Check:          http://127.0.0.1:8000/health
echo   Test Image Gen:        http://127.0.0.1:8000/test-image
echo   Press Ctrl+C to stop the server.
echo  ──────────────────────────────────────────────────────
echo.

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo.
echo [*] Server stopped.
pause
