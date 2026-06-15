@echo off
cd /d "%~dp0"
title FunASR Duo Yu Yan Zhuan Xie Xi Tong

echo ==========================================
echo   FunASR Duo Yu Yan Zhuan Xie Xi Tong
echo ==========================================
echo.

:: ---- Detect Python ----
set "PYEXE="
where python >nul 2>nul
if not errorlevel 1 (
    set "PYEXE=python"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYEXE=py -3"
    )
)
if "%PYEXE%"=="" (
    echo [Error] Python not found! Install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python found.

:: ---- Create venv if missing ----
if not exist "venv\Scripts\python.exe" (
    echo [Info] Creating virtual environment...
    %PYEXE% -m venv venv >nul 2>&1
    if errorlevel 1 (
        echo [Error] Failed to create venv!
        pause
        exit /b 1
    )
    echo [OK] venv created.
)

:: ---- Check venv is usable ----
"venv\Scripts\python.exe" -c "import sys" 2>nul
if errorlevel 1 (
    echo [Info] Rebuilding broken venv...
    rmdir /s /q "venv" 2>nul
    %PYEXE% -m venv venv >nul 2>&1
    if errorlevel 1 (
        echo [Error] Cannot rebuild venv!
        pause
        exit /b 1
    )
    echo [OK] venv rebuilt.
)

:: ---- Install dependencies ----
"venv\Scripts\python.exe" -c "import funasr" 2>nul
if errorlevel 1 (
    echo.
    echo [Info] Installing dependencies. This may take 3-10 min...
    echo [Info] Downloading from PyPI. Progress will show below:
    echo.
    "venv\Scripts\pip.exe" install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo.
        echo [Info] Retrying with individual packages...
        for %%p in (funasr modelscope PyQt6 sounddevice numpy scipy) do (
            "venv\Scripts\pip.exe" install %%p
        )
    )
    echo.
    echo [Info] Installing PyTorch...
    "venv\Scripts\pip.exe" install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    if errorlevel 1 (
        echo [Info] CUDA not found; installing CPU PyTorch...
        "venv\Scripts\pip.exe" install torch torchaudio
    )
    echo [OK] Dependencies installed.
)

:: ---- Ensure model directory ----
if not exist "models" mkdir models >nul 2>&1

:: ---- Set environment variables ----
set "MODELSCOPE_CACHE=%~dp0models"
set "VIRTUAL_ENV=%~dp0venv"
set "PATH=%~dp0;%~dp0venv\Scripts;%PATH%"

:: ---- Launch application ----
echo.
echo Starting GUI...
echo.
"venv\Scripts\python.exe" "%~dp0launcher.py"
if errorlevel 1 (
    echo.
    echo ==========================================
    echo   Error: Application exited with error
    echo ==========================================
    pause
    exit /b 1
)
echo.
echo [OK] Application closed.
echo Press any key to exit...
pause >nul
