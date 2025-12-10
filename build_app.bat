@echo off
chcp 65001 >nul
echo ========================================
echo   Build Dialysis Automation App
echo   打包透析自动化系统
echo ========================================
echo.

echo 📋 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found
echo.

echo 📦 Installing/Updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
echo.

echo 🔨 Building application...
echo ⏳ This will take 5-10 minutes...
echo.
python build_app.py

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ BUILD COMPLETE!
echo ========================================
echo.
echo 📦 Your app is ready!
echo.
echo 📂 Files created:
echo    • dist\DialysisAutomation.exe (Main app)
echo    • distribution\ (Complete package for users)
echo.
echo 🧪 Test your app now?
set /p choice="Run app now? (Y/N): "

if /i "%choice%"=="Y" (
    echo.
    echo 🚀 Launching app...
    start "" "dist\DialysisAutomation.exe"
)

echo.
echo 💡 Next steps:
echo    1. Test the app thoroughly
echo    2. Copy distribution\ folder to USB/network
echo    3. Distribute to users
echo    4. Ensure Tesseract OCR is installed on target PCs
echo.
pause
