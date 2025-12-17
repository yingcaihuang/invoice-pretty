#!/usr/bin/env python3
"""
修复导入问题的macOS应用程序构建脚本
专门解决PyInstaller打包后的模块导入问题
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def create_fixed_main():
    """创建修复导入问题的主程序"""
    fixed_main_content = '''#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 导入修复版
解决PyInstaller打包后的模块导入问题
"""

import sys
import os
import logging
from pathlib import Path

def setup_paths():
    """设置Python路径"""
    # 获取当前脚本目录
    if getattr(sys, 'frozen', False):
        # PyInstaller环境
        base_dir = Path(sys._MEIPASS)
        app_dir = Path(sys.executable).parent
    else:
        # 开发环境
        base_dir = Path(__file__).parent
        app_dir = base_dir
    
    # 添加可能的路径到sys.path
    paths_to_add = [
        str(base_dir),
        str(base_dir / "src"),
        str(app_dir),
        str(app_dir / "src"),
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置工作目录
    if base_dir.exists():
        os.chdir(str(base_dir))
    elif app_dir.exists():
        os.chdir(str(app_dir))
    
    return base_dir, app_dir

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def test_imports(logger):
    """测试关键模块导入"""
    logger.info("测试模块导入...")
    
    # 测试基础模块
    try:
        import tkinter
        logger.info("✅ tkinter导入成功")
    except ImportError as e:
        logger.error(f"❌ tkinter导入失败: {e}")
        return False
    
    try:
        import PIL
        logger.info("✅ PIL导入成功")
    except ImportError as e:
        logger.error(f"❌ PIL导入失败: {e}")
        return False
    
    try:
        import fitz
        logger.info("✅ PyMuPDF导入成功")
    except ImportError as e:
        logger.error(f"❌ PyMuPDF导入失败: {e}")
        return False
    
    return True

def import_gui_controller(logger):
    """导入GUI控制器"""
    logger.info("尝试导入GUI控制器...")
    
    # 尝试多种导入方式
    import_attempts = [
        "from src.ui.gui_controller import GUIController",
        "from ui.gui_controller import GUIController", 
        "import src.ui.gui_controller as gui_module; GUIController = gui_module.GUIController",
        "import ui.gui_controller as gui_module; GUIController = gui_module.GUIController"
    ]
    
    for i, attempt in enumerate(import_attempts, 1):
        try:
            logger.info(f"尝试方法 {i}: {attempt}")
            
            # 创建局部命名空间执行导入
            local_vars = {}
            exec(attempt, globals(), local_vars)
            
            if 'GUIController' in local_vars:
                logger.info(f"✅ 方法 {i} 导入成功")
                return local_vars['GUIController']
            elif 'GUIController' in globals():
                logger.info(f"✅ 方法 {i} 导入成功（全局）")
                return globals()['GUIController']
                
        except Exception as e:
            logger.warning(f"❌ 方法 {i} 失败: {e}")
            continue
    
    # 如果所有方法都失败，尝试直接文件导入
    logger.info("尝试直接文件导入...")
    try:
        import importlib.util
        
        # 查找gui_controller.py文件
        possible_paths = [
            "src/ui/gui_controller.py",
            "ui/gui_controller.py",
            "../src/ui/gui_controller.py"
        ]
        
        gui_controller_path = None
        for path in possible_paths:
            if os.path.exists(path):
                gui_controller_path = path
                break
        
        if gui_controller_path:
            logger.info(f"找到GUI控制器文件: {gui_controller_path}")
            
            spec = importlib.util.spec_from_file_location("gui_controller", gui_controller_path)
            gui_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gui_module)
            
            if hasattr(gui_module, 'GUIController'):
                logger.info("✅ 直接文件导入成功")
                return gui_module.GUIController
        
    except Exception as e:
        logger.error(f"❌ 直接文件导入失败: {e}")
    
    logger.error("❌ 所有导入方法都失败")
    return None

def main():
    """主函数"""
    # 设置路径
    base_dir, app_dir = setup_paths()
    
    # 设置日志
    logger = setup_logging()
    logger.info("PDF发票拼版打印系统启动 - 导入修复版")
    logger.info(f"基础目录: {base_dir}")
    logger.info(f"应用目录: {app_dir}")
    logger.info(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径
    
    try:
        # 测试基础模块导入
        if not test_imports(logger):
            logger.error("基础模块导入失败，无法继续")
            input("按回车键退出...")
            return
        
        # 导入GUI控制器
        GUIController = import_gui_controller(logger)
        
        if GUIController is None:
            logger.error("GUI控制器导入失败")
            logger.info("尝试启动简化版界面...")
            
            # 创建简化的tkinter界面
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.title("PDF发票拼版打印系统")
            root.geometry("400x300")
            
            tk.Label(root, text="PDF发票拼版打印系统", font=("Arial", 16)).pack(pady=20)
            tk.Label(root, text="GUI模块导入失败", font=("Arial", 12), fg="red").pack(pady=10)
            tk.Label(root, text="请使用命令行版本:", font=("Arial", 10)).pack(pady=5)
            tk.Label(root, text="python cli_main.py input.pdf -o output.pdf", 
                    font=("Courier", 9)).pack(pady=5)
            
            def show_error():
                messagebox.showerror("错误", "GUI模块导入失败\\n请查看控制台输出获取详细信息")
            
            tk.Button(root, text="显示错误详情", command=show_error).pack(pady=10)
            tk.Button(root, text="退出", command=root.quit).pack(pady=5)
            
            root.mainloop()
            return
        
        # 成功导入，启动GUI
        logger.info("启动GUI应用程序...")
        
        gui = GUIController()
        gui.run()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 保存错误日志到桌面
        try:
            error_log = Path.home() / "Desktop" / "pdf_invoice_import_error.log"
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"PDF发票拼版打印系统启动错误\\n")
                f.write(f"错误: {e}\\n\\n")
                f.write(f"详细信息:\\n{traceback.format_exc()}")
            
            logger.info(f"错误日志已保存到: {error_log}")
        except Exception:
            pass
        
        input("按回车键退出...")

if __name__ == "__main__":
    main()
'''
    
    fixed_main_path = Path("main_import_fixed.py")
    with open(fixed_main_path, 'w', encoding='utf-8') as f:
        f.write(fixed_main_content)
    
    return fixed_main_path

def build_import_fixed():
    """构建导入修复版应用程序"""
    print("🔨 构建导入修复版应用程序...")
    
    # 清理旧文件
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
    
    # 创建修复版主程序
    fixed_main = create_fixed_main()
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onedir',  # 使用目录模式便于调试
        '--windowed',  # 无控制台窗口
        '--name', 'invoice_pretty',
        '--osx-bundle-identifier', 'com.pdfinvoicelayout.import.fixed',
        
        # 添加整个src目录
        '--add-data', 'src:src',
        '--add-data', 'config.json:.',
        '--add-data', 'main.py:.',
        '--add-data', 'cli_main.py:.',
        
        # 添加所有必要的隐藏导入
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--hidden-import', 'tkinter.filedialog',
        '--hidden-import', 'tkinter.messagebox',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'PIL.ImageTk',
        '--hidden-import', 'fitz',
        '--hidden-import', 'queue',
        '--hidden-import', 'threading',
        '--hidden-import', 'datetime',
        '--hidden-import', 'logging',
        '--hidden-import', 'pathlib',
        '--hidden-import', 'zipfile',
        '--hidden-import', 'tempfile',
        '--hidden-import', 'shutil',
        '--hidden-import', 'subprocess',
        '--hidden-import', 'importlib.util',
        
        # 显式添加src下的所有模块
        '--hidden-import', 'src',
        '--hidden-import', 'src.models',
        '--hidden-import', 'src.models.data_models',
        '--hidden-import', 'src.interfaces',
        '--hidden-import', 'src.interfaces.base_interfaces',
        '--hidden-import', 'src.services',
        '--hidden-import', 'src.services.file_handler',
        '--hidden-import', 'src.services.pdf_reader',
        '--hidden-import', 'src.services.layout_manager',
        '--hidden-import', 'src.services.pdf_processor',
        '--hidden-import', 'src.ui',
        '--hidden-import', 'src.ui.gui_controller',
        
        str(fixed_main)
    ]
    
    print("执行构建命令...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ 导入修复版构建完成")
        return True
    else:
        print("❌ 导入修复版构建失败")
        return False

def create_import_fixed_dmg():
    """创建导入修复版DMG"""
    print("📦 创建导入修复版DMG...")
    
    app_path = Path("dist/invoice_pretty.app")
    if not app_path.exists():
        print("❌ 找不到应用程序")
        return False
    
    # 创建临时目录
    temp_dir = Path("dist/import_fixed_dmg_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # 复制应用程序
        shutil.copytree(app_path, temp_dir / app_path.name)
        
        # 创建Applications链接
        (temp_dir / "Applications").symlink_to("/Applications")
        
        # 创建说明文件
        readme_content = """PDF Invoice Layout System

This version fixes PyInstaller module import issues.

Features:
- Smart module importing with multiple fallback methods
- Detailed startup logs for troubleshooting
- Simplified interface if GUI import fails
- Automatic error log saving to desktop

Installation:
1. Drag the application to Applications folder
2. Right-click the application and select "Open"
3. Click "Open" in the security prompt

If issues persist:
1. Check error log file on desktop
2. Use command line version: python cli_main.py input.pdf -o output.pdf
3. Run troubleshooting tool: python fix_macos_app.py
"""
        
        readme_path = temp_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 创建DMG
        dmg_path = "dist/invoice_pretty.dmg"
        cmd = [
            'hdiutil', 'create',
            '-volname', 'Invoice Pretty',
            '-srcfolder', str(temp_dir),
            '-ov',
            '-format', 'UDZO',
            dmg_path
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"✅ 导入修复版DMG创建完成: {dmg_path}")
            return True
        else:
            print("❌ 导入修复版DMG创建失败")
            return False
            
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def main():
    """主函数"""
    print("🚀 PDF发票拼版打印系统 - 导入修复版构建")
    print("=" * 60)
    
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
        ("构建导入修复版应用程序", build_import_fixed),
        ("创建DMG安装包", create_import_fixed_dmg),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ {step_name}失败")
            return False
    
    print("\n🎉 导入修复版构建完成！")
    print("\n📋 特点:")
    print("- 智能模块导入，解决PyInstaller路径问题")
    print("- 详细的启动诊断信息")
    print("- 如果GUI失败，显示简化界面")
    print("- 自动保存错误日志")
    
    print("\n💡 这个版本应该能够解决'No module named ui'的问题")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)