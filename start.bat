@echo off
chcp 65001 >nul
echo ========================================
echo   Dialysis Automation System
echo   透析自动化系统
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo ⚠️ 虚拟环境不存在，正在创建...
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ 虚拟环境创建成功！
    echo.
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM 检查是否需要安装依赖
pip show paddleocr >nul 2>&1
if errorlevel 1 (
    echo 📦 安装依赖包...
    echo Installing dependencies...
    pip install -r requirements.txt
    echo ✅ 依赖安装完成！
    echo.
)

REM 启动程序
echo 🚀 启动程序...
echo Starting application...
echo.
python main.py

REM 如果程序退出，暂停以显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序出错！请检查错误信息。
    echo Program encountered an error. Please check the message above.
    pause
)