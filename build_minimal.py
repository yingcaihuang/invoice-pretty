#!/usr/bin/env python3
"""
最小化macOS应用程序构建脚本
使用最简单的方法避免所有可能的问题
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def create_minimal_main():
    """创建最小化主程序"""
    minimal_main = '''#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 最小化版本
使用最简单的启动方式
"""

import sys
import os
from pathlib import Path

# 确保正确的工作目录
if getattr(sys, 'frozen', False):
    # PyInstaller环境
    app_dir = Path(sys.executable).parent
    os.chdir(app_dir)

def main():
    """主函数"""
    try:
        # 直接启动GUI
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建简单的启动窗口
        root = tk.Tk()
        root.title("PDF发票拼版打印系统")
        root.geometry("400x300")
        
        # 添加启动按钮
        def start_app():
            try:
                root.destroy()
                # 导入并启动真正的应用程序
                sys.path.insert(0, str(Path(__file__).parent))
                from main_app import start_gui_app
                start_gui_app()
            except Exception as e:
                messagebox.showerror("启动错误", f"应用程序启动失败:\\n{e}")
        
        # 创建界面
        tk.Label(root, text="PDF发票拼版打印系统", font=("Arial", 16)).pack(pady=20)
        tk.Label(root, text="智能处理12306电子发票", font=("Arial", 12)).pack(pady=10)
        tk.Button(root, text="启动应用程序", command=start_app, font=("Arial", 14)).pack(pady=20)
        
        # 添加测试按钮
        def test_modules():
            try:
                import fitz
                import PIL
                messagebox.showinfo("测试结果", "所有模块导入成功！")
            except Exception as e:
                messagebox.showerror("测试结果", f"模块导入失败:\\n{e}")
        
        tk.Button(root, text="测试模块", command=test_modules).pack(pady=10)
        
        root.mainloop()
        
    except Exception as e:
        # 如果GUI失败，显示错误信息
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误到桌面
        error_file = Path.home() / "Desktop" / "pdf_invoice_error.txt"
        with open(error_file, 'w') as f:
            f.write(f"错误: {e}\\n")
            f.write(traceback.format_exc())
        
        print(f"错误信息已保存到: {error_file}")

if __name__ == "__main__":
    main()
'''
    
    minimal_path = Path("minimal_main.py")
    with open(minimal_path, 'w') as f:
        f.write(minimal_main)
    
    return minimal_path

def create_main_app():
    """创建主应用程序模块"""
    main_app_content = '''#!/usr/bin/env python3
"""
主应用程序模块
"""

def start_gui_app():
    """启动GUI应用程序"""
    try:
        # 导入原始的main模块
        import main
        main.main()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动错误", f"无法启动主应用程序:\\n{e}")
        root.destroy()
'''
    
    main_app_path = Path("main_app.py")
    with open(main_app_path, 'w') as f:
        f.write(main_app_content)
    
    return main_app_path

def build_minimal():
    """构建最小化应用程序"""
    print("🔨 构建最小化应用程序...")
    
    # 清理旧文件
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
    
    # 创建最小化文件
    minimal_main = create_minimal_main()
    main_app = create_main_app()
    
    # 最简单的构建命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onefile',  # 单文件模式
        '--windowed',  # 无控制台
        '--name', 'PDF发票拼版打印系统-最小版',
        
        # 只添加绝对必要的文件
        '--add-data', f'{main_app}:.',
        '--add-data', 'main.py:.',
        '--add-data', 'config.json:.',
        '--add-data', 'src:src',
        
        # 只添加必要的隐藏导入
        '--hidden-import', 'tkinter',
        '--hidden-import', 'PIL',
        '--hidden-import', 'fitz',
        
        str(minimal_main)
    ]
    
    print("执行构建...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ 最小化应用程序构建完成")
        return True
    else:
        print("❌ 最小化应用程序构建失败")
        return False

def create_app_bundle():
    """手动创建.app包结构"""
    print("📦 手动创建.app包结构...")
    
    exe_path = Path("dist/PDF发票拼版打印系统-最小版")
    if not exe_path.exists():
        print("❌ 找不到可执行文件")
        return False
    
    # 创建.app目录结构
    app_name = "PDF发票拼版打印系统-最小版.app"
    app_path = Path("dist") / app_name
    
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # 创建目录结构
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    for dir_path in [contents_dir, macos_dir, resources_dir]:
        dir_path.mkdir(parents=True)
    
    # 复制可执行文件
    shutil.copy2(exe_path, macos_dir / "PDF发票拼版打印系统-最小版")
    os.chmod(macos_dir / "PDF发票拼版打印系统-最小版", 0o755)
    
    # 创建Info.plist
    info_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>PDF发票拼版打印系统-最小版</string>
    <key>CFBundleIdentifier</key>
    <string>com.pdfinvoicelayout.minimal</string>
    <key>CFBundleName</key>
    <string>PDF发票拼版打印系统-最小版</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.14.0</string>
</dict>
</plist>'''
    
    with open(contents_dir / "Info.plist", 'w') as f:
        f.write(info_plist)
    
    print(f"✅ .app包创建完成: {app_path}")
    return True

def create_minimal_dmg():
    """创建最小化DMG"""
    print("📦 创建最小化DMG...")
    
    app_path = Path("dist/PDF发票拼版打印系统-最小版.app")
    if not app_path.exists():
        print("❌ 找不到.app包")
        return False
    
    # 创建临时目录
    temp_dir = Path("dist/minimal_dmg_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # 复制应用程序
        shutil.copytree(app_path, temp_dir / app_path.name)
        
        # 创建Applications链接
        (temp_dir / "Applications").symlink_to("/Applications")
        
        # 创建使用说明
        readme = """PDF发票拼版打印系统 - 最小版

这是一个最小化版本，专门解决启动问题。

安装方法:
1. 将应用程序拖拽到Applications文件夹
2. 右键点击应用程序，选择"打开"
3. 在安全提示中点击"打开"

特点:
- 最小化依赖，提高兼容性
- 包含启动测试功能
- 详细的错误报告

如果仍然无法启动:
1. 运行终端命令: xattr -cr /Applications/PDF发票拼版打印系统-最小版.app
2. 检查桌面上的错误日志文件
"""
        
        with open(temp_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme)
        
        # 创建DMG
        dmg_path = "dist/PDF发票拼版打印系统-最小版.dmg"
        cmd = [
            'hdiutil', 'create',
            '-volname', 'PDF发票拼版打印系统-最小版',
            '-srcfolder', str(temp_dir),
            '-ov',
            '-format', 'UDZO',
            dmg_path
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"✅ 最小版DMG创建完成: {dmg_path}")
            return True
        else:
            print("❌ 最小版DMG创建失败")
            return False
            
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def main():
    """主函数"""
    print("🚀 PDF发票拼版打印系统 - 最小版构建")
    print("=" * 50)
    
    if sys.platform != 'darwin':
        print("❌ 此脚本只能在macOS上运行")
        return False
    
    # 检查PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except:
        print("❌ 请先安装PyInstaller: pip install pyinstaller")
        return False
    
    # 构建步骤
    steps = [
        ("构建最小化应用程序", build_minimal),
        ("创建.app包结构", create_app_bundle),
        ("创建DMG安装包", create_minimal_dmg),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ {step_name}失败")
            return False
    
    print("\n🎉 最小版构建完成！")
    print("\n📋 特点:")
    print("- 使用最简单的启动方式")
    print("- 包含模块测试功能")
    print("- 详细的错误报告")
    print("- 最小化依赖")
    
    print("\n💡 使用建议:")
    print("1. 这个版本应该能够启动")
    print("2. 如果仍有问题，点击'测试模块'按钮")
    print("3. 查看桌面上的错误日志")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)