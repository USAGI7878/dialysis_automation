@echo off
chcp 65001 >nul
echo ========================================
echo   Dialysis Automation Web App
echo   透析自动化系统 - 网页版
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not installed!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo ⏳ Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
    echo.
)

REM 激活虚拟环境
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM 检查依赖
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    echo ✅ Dependencies installed
    echo.
)

REM 获取IP地址
echo 🌐 Network Information:
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo    Your IP: !IP!
)
echo.

REM 显示访问信息
echo ========================================
echo   Starting Web App 启动网页应用
echo ========================================
echo.
echo 🚀 App will be available at:
echo.
echo    Local:   http://localhost:8501
echo    Network: http://!IP!:8501
echo.
echo 📱 Share the Network URL with colleagues!
echo    同事可以通过网络URL访问！
echo.
echo ⚠️  Keep this window open while using the app
echo    使用期间请保持此窗口打开
echo.
echo ========================================
echo.

REM 启动Streamlit
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

REM 如果出错
if errorlevel 1 (
    echo.
    echo ❌ Error starting app!
    echo.
    echo Common fixes:
    echo 1. Port 8501 already in use? Try: streamlit run app.py --server.port 8502
    echo 2. Missing files? Make sure app.py exists
    echo 3. Import errors? Run: pip install -r requirements.txt --force-reinstall
    echo.
    pause
)
