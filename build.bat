@echo off
REM PDF发票拼版打印系统 Windows构建脚本

echo PDF发票拼版打印系统 - Windows构建脚本
echo ========================================

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 运行构建脚本
echo 开始构建...
python build.py

if errorlevel 1 (
    echo 构建失败
    pause
    exit /b 1
)

echo 构建完成！
echo 可执行文件位于 dist\ 目录中
pause