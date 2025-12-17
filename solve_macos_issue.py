#!/usr/bin/env python3
"""
一键解决macOS应用程序启动问题
按优先级尝试不同的解决方案
"""

import os
import sys
import subprocess
from pathlib import Path
import time

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}成功")
            return True
        else:
            print(f"❌ {description}失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}失败: {e}")
        return False

def check_environment():
    """检查构建环境"""
    print_header("检查构建环境")
    
    # 检查系统
    if sys.platform != 'darwin':
        print("❌ 此脚本只能在macOS上运行")
        return False
    
    print("✅ 运行在macOS系统上")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    else:
        print(f"⚠️  Python版本较低: {python_version.major}.{python_version.minor}")
    
    # 检查PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PyInstaller版本: {result.stdout.strip()}")
        else:
            print("❌ PyInstaller未安装")
            print("安装命令: pip install pyinstaller")
            return False
    except FileNotFoundError:
        print("❌ PyInstaller未安装")
        print("安装命令: pip install pyinstaller")
        return False
    
    # 检查必要文件
    required_files = ['main.py', 'config.json']
    for file in required_files:
        if Path(file).exists():
            print(f"✅ 找到文件: {file}")
        else:
            print(f"❌ 缺少文件: {file}")
            return False
    
    return True

def try_fix_existing_app():
    """尝试修复已安装的应用程序"""
    print_header("尝试修复已安装的应用程序")
    
    app_paths = [
        "/Applications/PDF发票拼版打印系统.app",
        "/Applications/PDF发票拼版打印系统-简化版.app",
        "/Applications/PDF发票拼版打印系统-最小版.app"
    ]
    
    fixed_any = False
    
    for app_path in app_paths:
        if Path(app_path).exists():
            print(f"\n找到应用程序: {app_path}")
            
            # 移除隔离标记
            if run_command(f'xattr -cr "{app_path}"', "移除隔离标记"):
                fixed_any = True
            
            # 修复权限
            if run_command(f'chmod -R 755 "{app_path}"', "修复权限"):
                fixed_any = True
            
            # 测试启动
            print("测试应用程序启动...")
            try:
                subprocess.run(['open', app_path], timeout=5)
                print("✅ 应用程序启动测试完成")
                time.sleep(2)  # 等待应用程序启动
                fixed_any = True
            except subprocess.TimeoutExpired:
                print("⚠️  应用程序启动超时，但可能正在运行")
                fixed_any = True
            except Exception as e:
                print(f"❌ 应用程序启动测试失败: {e}")
    
    if not fixed_any:
        print("❌ 没有找到已安装的应用程序")
    
    return fixed_any

def build_solutions():
    """按优先级构建不同版本"""
    print_header("构建新版本应用程序")
    
    solutions = [
        ("最小化版本（推荐）", "python3 build_minimal.py"),
        ("简化版本", "python3 build_simple_fixed.py"),
        ("终极调试版", "python3 build_debug_ultimate.py"),
    ]
    
    for solution_name, command in solutions:
        print(f"\n🔨 尝试构建{solution_name}...")
        
        if run_command(command, f"构建{solution_name}"):
            print(f"✅ {solution_name}构建成功！")
            
            # 检查生成的文件
            dist_dir = Path("dist")
            if dist_dir.exists():
                print("\n📁 生成的文件:")
                for item in dist_dir.iterdir():
                    if item.suffix in ['.app', '.dmg'] or item.is_dir():
                        print(f"  📄 {item.name}")
            
            return True
        else:
            print(f"❌ {solution_name}构建失败，尝试下一个方案...")
            continue
    
    print("❌ 所有构建方案都失败了")
    return False

def provide_manual_solutions():
    """提供手动解决方案"""
    print_header("手动解决方案")
    
    print("如果自动修复失败，请尝试以下手动方法:")
    print()
    print("1. 移除隔离标记:")
    print("   xattr -cr /Applications/PDF发票拼版打印系统*.app")
    print()
    print("2. 修复权限:")
    print("   chmod -R 755 /Applications/PDF发票拼版打印系统*.app")
    print()
    print("3. 首次运行:")
    print("   - 右键点击应用程序")
    print("   - 选择'打开'")
    print("   - 在安全提示中点击'打开'")
    print()
    print("4. 系统设置:")
    print("   - 打开'系统偏好设置' > '安全性与隐私'")
    print("   - 在'通用'标签页中允许应用程序运行")
    print()
    print("5. 重新安装:")
    print("   - 删除Applications文件夹中的旧版本")
    print("   - 重新安装新构建的版本")

def main():
    """主函数"""
    print("🚀 PDF发票拼版打印系统 - 一键问题解决方案")
    print("专门解决macOS应用程序启动问题")
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，无法继续")
        return False
    
    # 尝试修复现有应用程序
    if try_fix_existing_app():
        print("\n🎉 现有应用程序修复完成！")
        print("请尝试启动应用程序，如果仍有问题，继续执行构建新版本。")
        
        response = input("\n是否需要构建新版本？(y/N): ").lower()
        if response not in ['y', 'yes']:
            return True
    
    # 构建新版本
    if build_solutions():
        print("\n🎉 新版本构建完成！")
        print("\n📋 安装说明:")
        print("1. 打开生成的DMG文件")
        print("2. 将应用程序拖拽到Applications文件夹")
        print("3. 右键点击应用程序，选择'打开'")
        print("4. 在安全提示中点击'打开'")
        return True
    
    # 提供手动解决方案
    provide_manual_solutions()
    
    print("\n📞 如果问题仍然存在:")
    print("1. 运行终极调试版查看详细错误信息")
    print("2. 检查桌面上的调试日志文件")
    print("3. 确保系统版本为macOS 10.14或更高")
    
    return False

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✅ 问题解决完成！")
        else:
            print("\n⚠️  需要进一步排查问题")
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")