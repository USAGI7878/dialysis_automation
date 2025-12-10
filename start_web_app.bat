@echo off
cls
echo ========================================
echo   Dialysis Automation Web App
echo   Dialysis Automation System
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check virtual environment
if not exist "venv\" (
    echo [WAIT] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [WAIT] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check dependencies
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo [WAIT] Installing dependencies...
    pip install -r requirements.txt
    echo [OK] Dependencies installed
    echo.
)

REM Get IP address
echo ========================================
echo   Network Information
echo ========================================
echo.
echo [INFO] Detecting IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    echo Your IP: %%a
)
echo.

REM Display access information
echo ========================================
echo   Starting Web App
echo ========================================
echo.
echo App will be available at:
echo.
echo    Local:   http://localhost:8501
echo    Network: http://%IP:~1%:8501
echo.
echo [TIP] Share the Network URL with colleagues!
echo.
echo [WARNING] Keep this window open while using the app
echo.
echo ========================================
echo.
echo [WAIT] Starting Streamlit server...
echo.

REM Start Streamlit
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

REM If error occurs
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start app!
    echo.
    echo Common fixes:
    echo 1. Port 8501 already in use? Try a different port
    echo 2. Missing files? Make sure app.py exists
    echo 3. Import errors? Reinstall: pip install -r requirements.txt
    echo.
    pause
)
