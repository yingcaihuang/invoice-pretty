@echo off
chcp 65001 >nul
echo 🚀 PDF发票拼版打印系统 - Windows构建
echo ============================================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 🔍 发现虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  未发现虚拟环境，使用系统Python
)

REM 检查PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 📦 安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller安装失败
        pause
        exit /b 1
    )
)

REM 运行构建脚本
echo 🔨 开始构建Windows EXE...
python build_windows.py

if errorlevel 1 (
    echo ❌ 构建失败
    pause
    exit /b 1
) else (
    echo ✅ 构建成功完成！
    echo.
    echo 📁 生成的文件在 dist\ 目录中
    echo.
    pause
)