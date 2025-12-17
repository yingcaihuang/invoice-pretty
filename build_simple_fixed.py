#!/usr/bin/env python3
"""
简化版macOS打包脚本 - 专门解决DMG安装后立即退出的问题
"""

import os
import sys
import subprocess
from pathlib import Path

def build_simple_app():
    """构建简单但稳定的macOS应用程序"""
    print("🔨 构建简化版macOS应用程序...")
    
    # 清理之前的构建
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            subprocess.run(['rm', '-rf', dir_name])
    
    # 使用最简单的PyInstaller配置
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onefile',  # 单文件模式，避免路径问题
        '--windowed',
        '--name', 'PDF发票拼版打印系统',
        '--osx-bundle-identifier', 'com.pdfinvoicelayout.simple',
        
        # 只添加必要的隐藏导入
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--hidden-import', 'tkinter.filedialog',
        '--hidden-import', 'tkinter.messagebox',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'fitz',
        '--hidden-import', 'queue',
        '--hidden-import', 'threading',
        
        # 添加配置文件
        '--add-data', 'config.json:.',
        
        # 排除不需要的模块
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'numpy.distutils',
        '--exclude-module', 'scipy',
        '--exclude-module', 'pandas',
        '--exclude-module', 'pytest',
        '--exclude-module', 'hypothesis',
        
        'main.py'
    ]
    
    print("执行命令:", ' '.join(cmd))
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("❌ 构建失败")
        return False
    
    print("✅ 应用程序构建完成")
    return True

def create_simple_dmg():
    """创建简单的DMG"""
    print("📦 创建DMG...")
    
    app_path = Path("dist/PDF发票拼版打印系统.app")
    if not app_path.exists():
        print("❌ 找不到应用程序包")
        return False
    
    # 创建临时目录
    temp_dir = Path("dist/dmg_temp")
    if temp_dir.exists():
        subprocess.run(['rm', '-rf', str(temp_dir)])
    temp_dir.mkdir()
    
    try:
        # 复制应用程序
        subprocess.run(['cp', '-R', str(app_path), str(temp_dir)])
        
        # 创建Applications链接
        subprocess.run(['ln', '-s', '/Applications', str(temp_dir / 'Applications')])
        
        # 创建使用说明
        readme = temp_dir / "使用说明.txt"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write("""PDF发票拼版打印系统

安装方法:
1. 将应用程序拖拽到Applications文件夹
2. 首次运行时，右键点击应用程序，选择"打开"
3. 在安全提示中点击"打开"

如果应用程序无法启动:
1. 检查系统版本是否为macOS 10.14或更高
2. 尝试在终端中运行以下命令:
   xattr -cr /Applications/PDF发票拼版打印系统.app

功能说明:
- 支持PDF和ZIP文件
- 自动提取ZIP中的PDF文件
- 生成2列4行的拼版布局
- 保持原始纵横比
- 300DPI高质量输出
""")
        
        # 创建DMG
        dmg_path = "dist/PDF发票拼版打印系统-简化版.dmg"
        cmd = [
            'hdiutil', 'create',
            '-volname', 'PDF发票拼版打印系统',
            '-srcfolder', str(temp_dir),
            '-ov',
            '-format', 'UDZO',
            dmg_path
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"✅ DMG创建完成: {dmg_path}")
            return True
        else:
            print("❌ DMG创建失败")
            return False
            
    finally:
        # 清理临时目录
        if temp_dir.exists():
            subprocess.run(['rm', '-rf', str(temp_dir)])

def main():
    """主函数"""
    print("🚀 PDF发票拼版打印系统 - 简化版macOS打包")
    print("=" * 50)
    
    if sys.platform != 'darwin':
        print("❌ 此脚本只能在macOS上运行")
        return False
    
    # 检查PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 请先安装PyInstaller: pip install pyinstaller")
        return False
    
    # 构建应用程序
    if not build_simple_app():
        return False
    
    # 创建DMG
    if not create_simple_dmg():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 简化版构建完成！")
    print("\n📋 安装说明:")
    print("1. 打开生成的DMG文件")
    print("2. 将应用程序拖拽到Applications文件夹")
    print("3. 右键点击应用程序，选择'打开'")
    print("4. 在安全提示中点击'打开'")
    print("\n💡 如果仍然无法运行，请在终端执行:")
    print("   xattr -cr /Applications/PDF发票拼版打印系统.app")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)