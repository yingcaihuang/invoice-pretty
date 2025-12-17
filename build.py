#!/usr/bin/env python3
"""
构建脚本
自动化打包PDF发票拼版打印系统
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def run_command(cmd, cwd=None):
    """运行命令并检查结果"""
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def check_dependencies():
    """检查构建依赖"""
    print("检查构建依赖...")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller未安装")
        return False
    
    # 检查其他依赖
    required_modules = ['fitz', 'PIL', 'tkinter']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}模块可用")
        except ImportError:
            print(f"✗ {module}模块未安装")
            return False
    
    return True

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"✓ 已删除 {dir_name}")
    
    # 清理.pyc文件
    for pyc_file in Path('.').rglob('*.pyc'):
        pyc_file.unlink()
    
    print("✓ 构建目录清理完成")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 使用PyInstaller构建
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'build.spec'
    ]
    
    if not run_command(cmd):
        return False
    
    print("✓ 可执行文件构建完成")
    return True

def create_installer():
    """创建安装包"""
    print("创建安装包...")
    
    system = platform.system().lower()
    dist_dir = Path('dist')
    
    if system == 'windows':
        # Windows: 创建ZIP包
        import zipfile
        
        zip_path = dist_dir / 'pdf-invoice-layout-windows.zip'
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            exe_path = dist_dir / 'pdf-invoice-layout.exe'
            if exe_path.exists():
                zipf.write(exe_path, 'pdf-invoice-layout.exe')
                
            # 添加配置和文档文件
            for file_name in ['config.json', 'CONFIG.md', 'README.md']:
                if Path(file_name).exists():
                    zipf.write(file_name, file_name)
        
        print(f"✓ Windows安装包已创建: {zip_path}")
        
    elif system == 'darwin':
        # macOS: 创建DMG（如果有工具）或ZIP
        app_path = dist_dir / 'PDF发票拼版打印系统.app'
        if app_path.exists():
            # 创建ZIP包
            import zipfile
            zip_path = dist_dir / 'pdf-invoice-layout-macos.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in app_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(dist_dir)
                        zipf.write(file_path, arcname)
            
            print(f"✓ macOS安装包已创建: {zip_path}")
        
    elif system == 'linux':
        # Linux: 创建tar.gz包
        import tarfile
        
        tar_path = dist_dir / 'pdf-invoice-layout-linux.tar.gz'
        with tarfile.open(tar_path, 'w:gz') as tar:
            exe_path = dist_dir / 'pdf-invoice-layout'
            if exe_path.exists():
                tar.add(exe_path, 'pdf-invoice-layout')
                
            # 添加配置和文档文件
            for file_name in ['config.json', 'CONFIG.md', 'README.md']:
                if Path(file_name).exists():
                    tar.add(file_name, file_name)
        
        print(f"✓ Linux安装包已创建: {tar_path}")

def test_executable():
    """测试可执行文件"""
    print("测试可执行文件...")
    
    system = platform.system().lower()
    dist_dir = Path('dist')
    
    if system == 'windows':
        exe_path = dist_dir / 'pdf-invoice-layout.exe'
    elif system == 'darwin':
        exe_path = dist_dir / 'PDF发票拼版打印系统.app' / 'Contents' / 'MacOS' / 'pdf-invoice-layout'
    else:
        exe_path = dist_dir / 'pdf-invoice-layout'
    
    if not exe_path.exists():
        print(f"✗ 可执行文件不存在: {exe_path}")
        return False
    
    # 测试版本信息（如果支持）
    try:
        result = subprocess.run(
            [str(exe_path), '--help'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        print("✓ 可执行文件可以正常启动")
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"✗ 可执行文件测试失败: {e}")
        return False

def main():
    """主函数"""
    print("PDF发票拼版打印系统构建脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("✗ 依赖检查失败，请安装必要的依赖")
        return 1
    
    # 清理构建目录
    clean_build()
    
    # 构建可执行文件
    if not build_executable():
        print("✗ 构建失败")
        return 1
    
    # 测试可执行文件
    if not test_executable():
        print("✗ 可执行文件测试失败")
        return 1
    
    # 创建安装包
    create_installer()
    
    print("=" * 50)
    print("✓ 构建完成！")
    print(f"输出目录: {Path('dist').absolute()}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())