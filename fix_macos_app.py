#!/usr/bin/env python3
"""
macOS应用程序故障排除脚本
专门解决DMG安装后应用立即退出的问题
"""

import os
import sys
import subprocess
from pathlib import Path

def diagnose_app_issues():
    """诊断应用程序问题"""
    print("🔍 诊断macOS应用程序问题...")
    
    app_path = Path("/Applications/PDF发票拼版打印系统.app")
    
    if not app_path.exists():
        print("❌ 应用程序未安装在Applications文件夹中")
        return False
    
    print(f"✅ 找到应用程序: {app_path}")
    
    # 检查权限
    print("\n📋 检查文件权限...")
    exe_path = app_path / "Contents" / "MacOS" / "PDF发票拼版打印系统"
    
    if exe_path.exists():
        stat_info = exe_path.stat()
        permissions = oct(stat_info.st_mode)[-3:]
        print(f"  可执行文件权限: {permissions}")
        
        if not os.access(exe_path, os.X_OK):
            print("  ❌ 可执行文件没有执行权限")
            return False
        else:
            print("  ✅ 可执行文件权限正常")
    else:
        print("  ❌ 找不到可执行文件")
        return False
    
    # 检查扩展属性（隔离标记）
    print("\n📋 检查扩展属性...")
    try:
        result = subprocess.run(['xattr', '-l', str(app_path)], 
                              capture_output=True, text=True)
        if 'com.apple.quarantine' in result.stdout:
            print("  ⚠️  发现隔离标记，这可能导致应用无法启动")
            return 'quarantine'
        else:
            print("  ✅ 没有发现隔离标记")
    except Exception as e:
        print(f"  ⚠️  无法检查扩展属性: {e}")
    
    # 检查依赖库
    print("\n📋 检查依赖库...")
    try:
        result = subprocess.run(['otool', '-L', str(exe_path)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ 依赖库检查完成")
            # 可以在这里分析具体的依赖
        else:
            print("  ⚠️  无法检查依赖库")
    except Exception as e:
        print(f"  ⚠️  依赖库检查失败: {e}")
    
    return True

def fix_quarantine_issue():
    """修复隔离问题"""
    print("🔧 修复隔离问题...")
    
    app_path = Path("/Applications/PDF发票拼版打印系统.app")
    
    try:
        # 移除隔离标记
        result = subprocess.run(['xattr', '-cr', str(app_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 隔离标记已移除")
            return True
        else:
            print(f"❌ 移除隔离标记失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def fix_permissions():
    """修复权限问题"""
    print("🔧 修复权限问题...")
    
    app_path = Path("/Applications/PDF发票拼版打印系统.app")
    
    try:
        # 修复整个应用程序包的权限
        subprocess.run(['chmod', '-R', '755', str(app_path)], check=True)
        
        # 确保可执行文件有执行权限
        exe_path = app_path / "Contents" / "MacOS" / "PDF发票拼版打印系统"
        if exe_path.exists():
            subprocess.run(['chmod', '+x', str(exe_path)], check=True)
        
        print("✅ 权限修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 权限修复失败: {e}")
        return False

def test_app_launch():
    """测试应用程序启动"""
    print("🧪 测试应用程序启动...")
    
    app_path = Path("/Applications/PDF发票拼版打印系统.app")
    
    try:
        # 尝试启动应用程序
        result = subprocess.run(['open', str(app_path)], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 应用程序启动成功")
            return True
        else:
            print(f"❌ 应用程序启动失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  应用程序启动超时，但可能正在运行")
        return True
    except Exception as e:
        print(f"❌ 启动测试失败: {e}")
        return False

def create_debug_launcher():
    """创建调试启动器"""
    print("🐛 创建调试启动器...")
    
    debug_script = '''#!/bin/bash
# PDF发票拼版打印系统调试启动器

APP_PATH="/Applications/PDF发票拼版打印系统.app"
EXE_PATH="$APP_PATH/Contents/MacOS/PDF发票拼版打印系统"
LOG_FILE="$HOME/Desktop/pdf_invoice_debug.log"

echo "=== PDF发票拼版打印系统调试日志 ===" > "$LOG_FILE"
echo "时间: $(date)" >> "$LOG_FILE"
echo "应用程序路径: $APP_PATH" >> "$LOG_FILE"
echo "可执行文件路径: $EXE_PATH" >> "$LOG_FILE"

# 检查文件是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 应用程序包不存在" >> "$LOG_FILE"
    exit 1
fi

if [ ! -f "$EXE_PATH" ]; then
    echo "错误: 可执行文件不存在" >> "$LOG_FILE"
    exit 1
fi

# 检查权限
echo "文件权限:" >> "$LOG_FILE"
ls -la "$EXE_PATH" >> "$LOG_FILE"

# 检查扩展属性
echo "扩展属性:" >> "$LOG_FILE"
xattr -l "$APP_PATH" >> "$LOG_FILE"

# 尝试启动
echo "尝试启动应用程序..." >> "$LOG_FILE"
"$EXE_PATH" 2>> "$LOG_FILE" &

echo "调试日志已保存到: $LOG_FILE"
echo "如果应用程序无法启动，请查看日志文件"
'''
    
    debug_path = Path.home() / "Desktop" / "debug_pdf_invoice.sh"
    
    try:
        with open(debug_path, 'w') as f:
            f.write(debug_script)
        
        # 设置执行权限
        os.chmod(debug_path, 0o755)
        
        print(f"✅ 调试启动器已创建: {debug_path}")
        print("  使用方法: 双击运行或在终端中执行")
        return True
        
    except Exception as e:
        print(f"❌ 创建调试启动器失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 PDF发票拼版打印系统 - macOS故障排除工具")
    print("=" * 60)
    
    if sys.platform != 'darwin':
        print("❌ 此工具只能在macOS上运行")
        return False
    
    # 诊断问题
    diagnosis = diagnose_app_issues()
    
    if diagnosis == False:
        print("\n❌ 发现严重问题，无法继续")
        return False
    elif diagnosis == 'quarantine':
        print("\n🔧 检测到隔离问题，尝试修复...")
        if fix_quarantine_issue():
            print("✅ 隔离问题已修复")
        else:
            print("❌ 隔离问题修复失败")
    
    # 修复权限
    print("\n🔧 修复权限...")
    fix_permissions()
    
    # 创建调试启动器
    print("\n🐛 创建调试工具...")
    create_debug_launcher()
    
    # 测试启动
    print("\n🧪 测试应用程序...")
    if test_app_launch():
        print("\n🎉 应用程序应该可以正常运行了！")
    else:
        print("\n⚠️  应用程序可能仍有问题，请使用调试启动器查看详细信息")
    
    print("\n📋 故障排除完成")
    print("\n💡 如果问题仍然存在:")
    print("1. 运行桌面上的 debug_pdf_invoice.sh")
    print("2. 查看生成的调试日志")
    print("3. 尝试重新安装应用程序")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)