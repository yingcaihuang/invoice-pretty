#!/usr/bin/env python3
"""
终极调试版macOS应用程序构建脚本
专门用于诊断和解决应用程序立即退出的问题
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def create_debug_main():
    """创建终极调试版主程序"""
    debug_main_content = '''#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 终极调试版
捕获所有可能的启动错误
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from datetime import datetime

# 设置详细日志
log_file = Path.home() / "Desktop" / f"pdf_invoice_ultimate_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def log_system_info():
    """记录系统信息"""
    logger.info("=== 系统信息 ===")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"Python可执行文件: {sys.executable}")
    logger.info(f"平台: {sys.platform}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"Python路径: {sys.path}")
    logger.info(f"环境变量:")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['PYTHON', 'PATH', 'DYLD', 'MEIPASS']):
            logger.info(f"  {key}: {value}")
    
    # 检查是否在PyInstaller环境中
    if getattr(sys, 'frozen', False):
        logger.info(f"运行在PyInstaller环境中")
        logger.info(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'Not found')}")
        logger.info(f"executable: {sys.executable}")
    else:
        logger.info("运行在普通Python环境中")

def test_imports():
    """测试关键模块导入"""
    logger.info("=== 测试模块导入 ===")
    
    modules_to_test = [
        ('os', 'os'),
        ('sys', 'sys'),
        ('pathlib', 'pathlib'),
        ('tkinter', 'tkinter'),
        ('tkinter.ttk', 'tkinter.ttk'),
        ('tkinter.filedialog', 'tkinter.filedialog'),
        ('tkinter.messagebox', 'tkinter.messagebox'),
        ('PIL', 'PIL'),
        ('PIL.Image', 'PIL.Image'),
        ('fitz', 'fitz'),
        ('logging', 'logging'),
        ('threading', 'threading'),
        ('queue', 'queue'),
        ('datetime', 'datetime'),
        ('zipfile', 'zipfile'),
        ('tempfile', 'tempfile'),
        ('shutil', 'shutil'),
    ]
    
    failed_imports = []
    
    for module_name, import_name in modules_to_test:
        try:
            __import__(import_name)
            logger.info(f"✅ {module_name} 导入成功")
        except Exception as e:
            logger.error(f"❌ {module_name} 导入失败: {e}")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports

def test_tkinter():
    """测试tkinter功能"""
    logger.info("=== 测试tkinter功能 ===")
    
    try:
        import tkinter as tk
        logger.info("✅ tkinter导入成功")
        
        # 测试创建根窗口
        root = tk.Tk()
        logger.info("✅ 根窗口创建成功")
        
        # 测试基本功能
        root.title("测试窗口")
        root.geometry("300x200")
        logger.info("✅ 窗口配置成功")
        
        # 立即销毁窗口
        root.destroy()
        logger.info("✅ tkinter功能测试完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ tkinter测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_file_access():
    """测试文件访问权限"""
    logger.info("=== 测试文件访问权限 ===")
    
    try:
        # 测试当前目录读写
        test_file = Path("test_write.txt")
        test_file.write_text("测试写入")
        content = test_file.read_text()
        test_file.unlink()
        logger.info("✅ 当前目录读写正常")
        
        # 测试桌面写入
        desktop_test = Path.home() / "Desktop" / "test_desktop.txt"
        desktop_test.write_text("桌面写入测试")
        desktop_test.unlink()
        logger.info("✅ 桌面目录写入正常")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件访问测试失败: {e}")
        return False

def try_import_app_modules():
    """尝试导入应用程序模块"""
    logger.info("=== 测试应用程序模块导入 ===")
    
    # 添加src目录到路径
    src_path = Path(__file__).parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        logger.info(f"添加src路径: {src_path}")
    
    app_modules = [
        'src.models.data_models',
        'src.interfaces.base_interfaces', 
        'src.services.file_handler',
        'src.services.pdf_reader',
        'src.services.layout_manager',
        'src.services.pdf_processor',
        'src.ui.gui_controller',
    ]
    
    failed_modules = []
    
    for module in app_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} 导入成功")
        except Exception as e:
            logger.error(f"❌ {module} 导入失败: {e}")
            failed_modules.append((module, str(e)))
    
    return failed_modules

def try_start_main_app():
    """尝试启动主应用程序"""
    logger.info("=== 尝试启动主应用程序 ===")
    
    try:
        # 尝试导入并运行主程序
        import main
        logger.info("✅ main模块导入成功")
        
        # 检查main函数是否存在
        if hasattr(main, 'main'):
            logger.info("✅ 找到main函数")
            
            # 尝试启动（但不实际运行GUI）
            logger.info("准备启动应用程序...")
            
            # 这里我们不实际调用main.main()，因为它会启动GUI
            # 而是检查能否成功导入所有依赖
            from src.ui.gui_controller import GUIController
            logger.info("✅ GUIController导入成功")
            
            # 测试创建控制器（不创建窗口）
            controller = GUIController()
            logger.info("✅ GUIController创建成功")
            
            return True
        else:
            logger.error("❌ main模块中没有main函数")
            return False
            
    except Exception as e:
        logger.error(f"❌ 主应用程序启动失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("PDF发票拼版打印系统 - 终极调试版启动")
    logger.info("=" * 60)
    
    try:
        # 记录系统信息
        log_system_info()
        
        # 测试基础模块导入
        failed_imports = test_imports()
        
        # 测试tkinter
        tkinter_ok = test_tkinter()
        
        # 测试文件访问
        file_access_ok = test_file_access()
        
        # 测试应用程序模块
        failed_app_modules = try_import_app_modules()
        
        # 尝试启动主应用程序
        main_app_ok = try_start_main_app()
        
        # 总结结果
        logger.info("=" * 60)
        logger.info("诊断结果总结:")
        logger.info(f"基础模块导入: {'✅ 正常' if not failed_imports else '❌ 有问题'}")
        logger.info(f"tkinter功能: {'✅ 正常' if tkinter_ok else '❌ 有问题'}")
        logger.info(f"文件访问: {'✅ 正常' if file_access_ok else '❌ 有问题'}")
        logger.info(f"应用程序模块: {'✅ 正常' if not failed_app_modules else '❌ 有问题'}")
        logger.info(f"主应用程序: {'✅ 正常' if main_app_ok else '❌ 有问题'}")
        
        if failed_imports:
            logger.error("失败的基础模块:")
            for module, error in failed_imports:
                logger.error(f"  {module}: {error}")
        
        if failed_app_modules:
            logger.error("失败的应用程序模块:")
            for module, error in failed_app_modules:
                logger.error(f"  {module}: {error}")
        
        # 如果所有测试都通过，尝试启动真正的应用程序
        if tkinter_ok and not failed_imports and not failed_app_modules and main_app_ok:
            logger.info("所有测试通过，启动真正的应用程序...")
            import main
            main.main()
        else:
            logger.error("存在问题，无法启动应用程序")
            logger.info(f"详细日志已保存到: {log_file}")
            
            # 在macOS上显示通知
            try:
                subprocess.run([
                    'osascript', '-e', 
                    f'display notification "调试日志已保存到桌面" with title "PDF发票拼版打印系统调试"'
                ])
            except:
                pass
            
            # 等待用户查看日志
            input("按回车键退出...")
        
    except Exception as e:
        logger.error(f"终极调试版运行失败: {e}")
        logger.error(traceback.format_exc())
        logger.info(f"详细日志已保存到: {log_file}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
'''
    
    debug_main_path = Path("debug_ultimate_main.py")
    with open(debug_main_path, 'w', encoding='utf-8') as f:
        f.write(debug_main_content)
    
    return debug_main_path

def build_ultimate_debug():
    """构建终极调试版应用程序"""
    print("🐛 构建终极调试版应用程序...")
    
    # 清理旧文件
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
    
    # 创建调试主程序
    debug_main = create_debug_main()
    
    # 构建命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onedir',  # 使用目录模式便于调试
        '--console',  # 显示控制台
        '--name', 'PDF发票拼版打印系统-终极调试版',
        '--osx-bundle-identifier', 'com.pdfinvoicelayout.ultimate.debug',
        
        # 添加所有源文件
        '--add-data', 'src:src',
        '--add-data', 'config.json:.',
        '--add-data', 'main.py:.',
        
        # 添加所有可能需要的隐藏导入
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
        
        # 添加src下的所有模块
        '--hidden-import', 'src.models.data_models',
        '--hidden-import', 'src.interfaces.base_interfaces',
        '--hidden-import', 'src.services.file_handler',
        '--hidden-import', 'src.services.pdf_reader',
        '--hidden-import', 'src.services.layout_manager',
        '--hidden-import', 'src.services.pdf_processor',
        '--hidden-import', 'src.ui.gui_controller',
        
        str(debug_main)
    ]
    
    print("执行构建命令...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ 终极调试版构建完成")
        
        # 创建简单的DMG
        create_debug_dmg()
        
        return True
    else:
        print("❌ 终极调试版构建失败")
        return False

def create_debug_dmg():
    """创建调试版DMG"""
    print("📦 创建调试版DMG...")
    
    app_path = Path("dist/PDF发票拼版打印系统-终极调试版.app")
    if not app_path.exists():
        print("❌ 找不到调试版应用程序")
        return False
    
    # 创建临时目录
    temp_dir = Path("dist/debug_dmg_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # 复制应用程序
        shutil.copytree(app_path, temp_dir / app_path.name)
        
        # 创建Applications链接
        (temp_dir / "Applications").symlink_to("/Applications")
        
        # 创建详细说明
        readme_content = """PDF发票拼版打印系统 - 终极调试版

这是一个专门用于诊断问题的调试版本。

使用方法:
1. 将应用程序拖拽到Applications文件夹
2. 双击运行应用程序
3. 应用程序会显示控制台窗口，显示详细的调试信息
4. 调试日志会自动保存到桌面

如果应用程序仍然无法启动:
1. 在终端中运行: xattr -cr /Applications/PDF发票拼版打印系统-终极调试版.app
2. 右键点击应用程序，选择"打开"
3. 查看桌面上生成的调试日志文件

调试信息包括:
- 系统环境信息
- Python模块导入状态
- tkinter功能测试
- 文件访问权限测试
- 应用程序模块导入测试

如果所有测试都通过，应用程序会自动启动正常版本。
如果有任何测试失败，会显示详细的错误信息。
"""
        
        readme_path = temp_dir / "调试说明.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 创建DMG
        dmg_path = "dist/PDF发票拼版打印系统-终极调试版.dmg"
        cmd = [
            'hdiutil', 'create',
            '-volname', 'PDF发票拼版打印系统-终极调试版',
            '-srcfolder', str(temp_dir),
            '-ov',
            '-format', 'UDZO',
            dmg_path
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print(f"✅ 调试版DMG创建完成: {dmg_path}")
            return True
        else:
            print("❌ 调试版DMG创建失败")
            return False
            
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def main():
    """主函数"""
    print("🚀 PDF发票拼版打印系统 - 终极调试版构建")
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
    
    # 构建终极调试版
    if build_ultimate_debug():
        print("\n🎉 终极调试版构建完成！")
        print("\n📋 使用说明:")
        print("1. 安装生成的DMG文件")
        print("2. 运行终极调试版应用程序")
        print("3. 查看控制台输出和桌面上的日志文件")
        print("4. 根据调试信息确定问题原因")
        print("\n💡 这个版本会显示详细的诊断信息，帮助找出问题所在")
        return True
    else:
        print("❌ 终极调试版构建失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)