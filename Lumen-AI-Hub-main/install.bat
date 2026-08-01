@echo off
title Lumen AI Hub Setup
color 0A

echo ==========================================
echo      Lumen AI Hub Setup Wizard
echo ==========================================
echo.

:: ---------------------------------
:: Check Python
:: ---------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    echo Please install Python 3.11+ first.
    pause
    exit /b
)

:: ---------------------------------
:: Check Ollama
:: ---------------------------------
where ollama >nul 2>&1

if errorlevel 1 (
    echo.
    echo Ollama not found.
    echo Installing Ollama...
    echo.

    irm https://ollama.com/install.ps1 | iex 

    if errorlevel 1 (
        echo.
        echo Automatic installation failed.
        echo Please install Ollama manually:
        echo https://ollama.com/download/windows
        pause
        exit /b
    )
)

:: ---------------------------------
:: Start Ollama
:: ---------------------------------
tasklist | find /I "ollama.exe" >nul

if errorlevel 1 (
    start "" ollama serve
    timeout /t 3 >nul
)

:: ---------------------------------
:: Create Virtual Environment
:: ---------------------------------
if not exist ".venv" (
    echo.
    echo Creating Virtual Environment...
    python -m venv .venv
)

:: ---------------------------------
:: Activate
:: ---------------------------------
call .venv\Scripts\activate.bat

:: ---------------------------------
:: Upgrade pip
:: ---------------------------------
python -m pip install --upgrade pip

:: ---------------------------------
:: Install Requirements
:: ---------------------------------
echo.
echo Installing Python packages...
pip install -r requirements.txt

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Activate with:
echo     .venv\Scripts\activate
echo.
echo Run:
echo     streamlit run app.py
echo.
pause
