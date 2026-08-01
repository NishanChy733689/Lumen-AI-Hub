@echo off
title Ollama Streamlit Hub Launcher

echo [1/5] Clearing existing Ollama instances...
taskkill /f /im ollama.exe >nul 2>&1

:: --- MULTI-USER CONFIGURATION ---
set OLLAMA_NUM_PARALLEL=4
set OLLAMA_KEEP_ALIVE=2h
:: --------------------------------

echo [2/5] Launching Optimized Ollama service...
start /b ollama serve

echo [3/5] Waiting for Ollama server to initialize...
timeout /t 3 /nobreak >nul

echo [4/5] Activating Python Virtual Environment...
:: Change ".venv" to the exact name/path of your venv folder
call .venv\Scripts\activate.bat

echo [5/5] Launching your Streamlit App...
streamlit run main_app.py --server.enableCORS=false --server.enableXsrfProtection=false

echo.
echo Process complete.
pause
