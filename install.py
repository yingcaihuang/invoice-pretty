#!/usr/bin/env python3
"""
安装脚本
用于安装PDF发票拼版打印系统的依赖和配置
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并检查结果"""
    print(f"执行: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("安装依赖包...")
    
    # 升级pip
    if not run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip']):
        print("警告: pip升级失败，继续安装...")
    
    # 安装requirements.txt中的依赖
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        if not run_command([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]):
            print("✗ 依赖安装失败")
            return False
    else:
        print("✗ requirements.txt文件不存在")
        return False
    
    print("✓ 依赖安装完成")
    return True

def setup_virtual_environment():
    """设置虚拟环境（可选）"""
    print("设置虚拟环境...")
    
    venv_path = Path('venv')
    if venv_path.exists():
        print("✓ 虚拟环境已存在")
        return True
    
    # 创建虚拟环境
    if not run_command([sys.executable, '-m', 'venv', 'venv']):
        print("✗ 虚拟环境创建失败")
        return False
    
    print("✓ 虚拟环境创建完成")
    
    # 提示激活虚拟环境
    system = platform.system().lower()
    if system == 'windows':
        activate_cmd = 'venv\\Scripts\\activate'
    else:
        activate_cmd = 'source venv/bin/activate'
    
    print(f"请运行以下命令激活虚拟环境: {activate_cmd}")
    return True

def verify_installation():
    """验证安装"""
    print("验证安装...")
    
    # 检查关键模块
    modules_to_check = [
        ('fitz', 'PyMuPDF'),
        ('PIL', 'Pillow'),
        ('tkinter', 'tkinter'),
        ('hypothesis', 'Hypothesis'),
        ('pytest', 'pytest'),
    ]
    
    all_ok = True
    for module_name, package_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {package_name}模块可用")
        except ImportError:
            print(f"✗ {package_name}模块不可用")
            all_ok = False
    
    return all_ok

def create_desktop_shortcut():
    """创建桌面快捷方式（Windows）"""
    if platform.system().lower() != 'windows':
        return True
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, 'PDF发票拼版打印系统.lnk')
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = str(Path(__file__).parent / 'main.py')
        shortcut.WorkingDirectory = str(Path(__file__).parent)
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        print(f"✓ 桌面快捷方式已创建: {shortcut_path}")
        return True
        
    except ImportError:
        print("跳过桌面快捷方式创建（需要pywin32）")
        return True
    except Exception as e:
        print(f"桌面快捷方式创建失败: {e}")
        return True

def main():
    """主函数"""
    print("PDF发票拼版打印系统安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 询问是否创建虚拟环境
    create_venv = input("是否创建虚拟环境？(y/N): ").lower().startswith('y')
    if create_venv:
        if not setup_virtual_environment():
            return 1
        print("请激活虚拟环境后重新运行此脚本")
        return 0
    
    # 安装依赖
    if not install_dependencies():
        return 1
    
    # 验证安装
    if not verify_installation():
        print("✗ 安装验证失败，请检查错误信息")
        return 1
    
    # 创建桌面快捷方式（Windows）
    create_desktop_shortcut()
    
    print("=" * 50)
    print("✓ 安装完成！")
    print("运行以下命令启动应用:")
    print("  python main.py")
    print("或者运行以下命令查看帮助:")
    print("  python main.py --help")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())