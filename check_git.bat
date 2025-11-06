@echo off
chcp 65001 >nul
echo ========================================
echo   Git 安装检测
echo   Git Installation Check
echo ========================================
echo.

echo 🔍 正在检测 Git...
echo Checking for Git...
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git 未安装！
    echo    Git is NOT installed!
    echo.
    echo 📥 请访问以下网址下载安装：
    echo    Please visit the following URL to download:
    echo.
    echo    https://git-scm.com/download/win
    echo.
    echo 📋 安装步骤：
    echo    Installation steps:
    echo    1. 点击下载 64-bit Git for Windows Setup
    echo       Click to download 64-bit Git for Windows Setup
    echo    2. 运行安装程序
    echo       Run the installer
    echo    3. 一直点击 "Next"（使用默认设置）
    echo       Keep clicking "Next" (use default settings)
    echo    4. 点击 "Finish" 完成安装
    echo       Click "Finish" to complete
    echo    5. 重新运行此脚本验证
    echo       Re-run this script to verify
    echo.
    echo 💡 提示：安装后需要重启命令提示符才能生效！
    echo    Tip: You need to restart Command Prompt after installation!
    echo.
    pause
    exit /b 1
)

echo ✅ Git 已安装！
echo    Git is installed!
echo.

echo 📊 Git 版本信息：
echo    Git version info:
git --version
echo.

echo 🔧 Git 配置检查：
echo    Git configuration check:
echo.

echo    用户名 (User name):
git config --global user.name >nul 2>&1
if errorlevel 1 (
    echo    ❌ 未设置 (Not set)
    set "need_config=1"
) else (
    for /f "delims=" %%i in ('git config --global user.name') do echo    ✅ %%i
)

echo.
echo    邮箱 (Email):
git config --global user.email >nul 2>&1
if errorlevel 1 (
    echo    ❌ 未设置 (Not set)
    set "need_config=1"
) else (
    for /f "delims=" %%i in ('git config --global user.email') do echo    ✅ %%i
)

echo.

if defined need_config (
    echo ⚠️  需要配置 Git 用户信息！
    echo    Git user info needs to be configured!
    echo.
    echo 是否现在配置？(Y/N)
    echo Configure now? (Y/N)
    set /p config_now="> "
    
    if /i "%config_now%"=="Y" (
        echo.
        echo 请输入你的名字 (例如: Zhang San)
        echo Enter your name (e.g., Zhang San):
        set /p git_name="> "
        
        echo.
        echo 请输入你的邮箱 (例如: zhangsan@example.com)
        echo Enter your email (e.g., zhangsan@example.com):
        set /p git_email="> "
        
        echo.
        echo 🔧 正在配置...
        git config --global user.name "%git_name%"
        git config --global user.email "%git_email%"
        
        echo ✅ 配置完成！
        echo    Configuration complete!
        echo.
        echo    用户名: %git_name%
        echo    邮箱: %git_email%
    )
)

echo.
echo ========================================
echo   检测完成！
echo   Check Complete!
echo ========================================
echo.

if not defined need_config (
    echo ✅ Git 已正确安装并配置！
    echo    Git is properly installed and configured!
    echo.
    echo 🚀 你可以开始使用 Git 了！
    echo    You can start using Git now!
    echo.
    echo 💡 下一步：运行 upload_to_github.bat 上传项目
    echo    Next step: Run upload_to_github.bat to upload project
) else (
    if /i not "%config_now%"=="Y" (
        echo ⚠️  请记得配置 Git 用户信息：
        echo    Please remember to configure Git user info:
        echo.
        echo    git config --global user.name "你的名字"
        echo    git config --global user.email "your.email@example.com"
    )
)

echo.
pause
