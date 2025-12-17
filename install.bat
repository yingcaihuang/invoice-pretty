@echo off
REM PDF发票拼版打印系统 Windows安装脚本

echo PDF发票拼版打印系统 - Windows安装脚本
echo ========================================

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或不在PATH中
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 运行安装脚本
echo 开始安装...
python install.py

if errorlevel 1 (
    echo 安装失败
    pause
    exit /b 1
)

echo 安装完成！
echo 运行 python main.py 启动程序
pause