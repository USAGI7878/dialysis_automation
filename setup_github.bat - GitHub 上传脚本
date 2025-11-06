@echo off
chcp 65001 >nul
echo ========================================
echo   准备上传到 GitHub
echo   Preparing GitHub Upload
echo ========================================
echo.

echo 📋 检查 Git 安装...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git 未安装！
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git 已安装

echo.
echo 🔍 检查敏感文件...
if exist "config_local.json" (
    echo ⚠️  发现敏感文件: config_local.json
    echo 这个文件不会被上传（已在 .gitignore 中）
)

echo.
echo 📝 当前项目状态：
git status

echo.
echo ========================================
echo   下一步操作 Next Steps:
echo ========================================
echo.
echo 1️⃣  在 GitHub 创建新仓库（如果还没有）
echo    https://github.com/new
echo.
echo 2️⃣  初始化 Git（如果是新项目）
echo    git init
echo    git add .
echo    git commit -m "Initial commit: Dialysis Automation System v1.0.0"
echo.
echo 3️⃣  连接到远程仓库
echo    git remote add origin https://github.com/你的用户名/dialysis-automation.git
echo.
echo 4️⃣  推送到 GitHub
echo    git branch -M main
echo    git push -u origin main
echo.
echo ========================================
echo.
echo 💡 提示：记得修改 README.md 中的：
echo    - GitHub 用户名链接
echo    - 作者信息
echo    - 联系邮箱
echo.
echo 是否现在初始化 Git 仓库？(Y/N)
set /p choice="> "

if /i "%choice%"=="Y" (
    echo.
    echo 🔧 初始化 Git...
    git init
    
    echo.
    echo 📦 添加所有文件...
    git add .
    
    echo.
    echo 💾 创建首次提交...
    git commit -m "Initial commit: Dialysis Automation System v1.0.0"
    
    echo.
    echo ✅ Git 初始化完成！
    echo.
    echo 现在请：
    echo 1. 在 GitHub 创建新仓库
    echo 2. 复制仓库 URL
    echo 3. 运行以下命令：
    echo.
    echo    git remote add origin [你的仓库URL]
    echo    git branch -M main
    echo    git push -u origin main
    echo.
) else (
    echo.
    echo ℹ️  已取消。你可以稍后手动执行。
)

echo.
pause