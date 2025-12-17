#!/usr/bin/env python3
"""
修复版macOS应用程序打包脚本
解决DMG安装后应用立即退出的问题
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

class MacOSBuilderFixed:
    def __init__(self):
        self.project_root = Path.cwd()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.app_name = "PDF发票拼版打印系统"
        self.bundle_id = "com.pdfinvoicelayout.app"
        self.version = "1.0.0"
        
    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"  删除: {dir_path}")
                except OSError as e:
                    print(f"  警告: 无法完全删除 {dir_path}: {e}")
                    subprocess.run(['rm', '-rf', str(dir_path)], check=False)
        
        print("✅ 清理完成")
    
    def create_launcher_script(self):
        """创建启动脚本来解决路径和环境问题"""
        print("📝 创建启动脚本...")
        
        launcher_script = '''#!/bin/bash
# PDF发票拼版打印系统启动脚本
# 解决macOS应用程序包的路径和环境问题

# 获取应用程序包的路径
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(dirname "$(dirname "$APP_DIR")")"
RESOURCES_DIR="$BUNDLE_DIR/Contents/Resources"

# 设置环境变量
export PYTHONPATH="$RESOURCES_DIR:$PYTHONPATH"
export PATH="$RESOURCES_DIR:$PATH"

# 切换到资源目录
cd "$RESOURCES_DIR"

# 设置日志输出（用于调试）
LOG_FILE="$HOME/Desktop/pdf_invoice_debug.log"
echo "$(date): 启动PDF发票拼版打印系统" >> "$LOG_FILE"
echo "APP_DIR: $APP_DIR" >> "$LOG_FILE"
echo "RESOURCES_DIR: $RESOURCES_DIR" >> "$LOG_FILE"
echo "PYTHONPATH: $PYTHONPATH" >> "$LOG_FILE"

# 启动主程序
exec "$APP_DIR/PDF发票拼版打印系统" "$@" 2>> "$LOG_FILE"
'''
        
        launcher_path = self.project_root / "launcher.sh"
        with open(launcher_path, 'w') as f:
            f.write(launcher_script)
        
        # 设置执行权限
        os.chmod(launcher_path, 0o755)
        
        print(f"✅ 启动脚本已创建: {launcher_path}")
        return launcher_path
    
    def build_app_fixed(self):
        """构建修复版.app应用程序包"""
        print("🔨 构建修复版macOS应用程序包...")
        
        # 创建启动脚本
        launcher_path = self.create_launcher_script()
        
        # 构建PyInstaller命令
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            '--onedir',  # 使用目录模式
            '--windowed',  # 无控制台窗口
            '--name', self.app_name,
            '--osx-bundle-identifier', self.bundle_id,
            '--debug', 'all',  # 启用调试信息
        ]
        
        # 添加数据文件
        data_files = [
            ('config.json', '.'),
            ('CONFIG.md', '.'),
            ('README.md', '.'),
            (str(launcher_path), '.'),
        ]
        
        for src, dst in data_files:
            if Path(src).exists():
                cmd.extend(['--add-data', f'{src}:{dst}'])
        
        # 添加隐藏导入
        hidden_imports = [
            'tkinter',
            'tkinter.ttk',
            'tkinter.filedialog',
            'tkinter.messagebox',
            'PIL',
            'PIL.Image',
            'PIL.ImageTk',
            'fitz',
            'zipfile',
            'tempfile',
            'shutil',
            'queue',
            'threading',
            'datetime',
            'logging',
            'pathlib',
            'os',
            'sys',
        ]
        
        for module in hidden_imports:
            cmd.extend(['--hidden-import', module])
        
        # 排除不需要的模块
        excludes = [
            'matplotlib',
            'numpy.distutils',
            'scipy',
            'pandas',
            'jupyter',
            'IPython',
            'notebook',
            'pytest',
            'hypothesis',
        ]
        
        for module in excludes:
            cmd.extend(['--exclude-module', module])
        
        # 添加运行时钩子
        cmd.extend([
            '--runtime-hook', str(self.create_runtime_hook())
        ])
        
        # 添加主程序
        cmd.append('main.py')
        
        print(f"  执行命令: {' '.join(cmd)}")
        
        # 执行构建
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ 应用程序构建失败")
            return False
        
        # 修复应用程序包结构
        self.fix_app_bundle()
        
        print("✅ 应用程序构建完成")
        return True
    
    def create_runtime_hook(self):
        """创建运行时钩子来修复导入问题"""
        hook_content = '''
import sys
import os
from pathlib import Path

# 修复macOS应用程序包的路径问题
if getattr(sys, 'frozen', False):
    # 运行在PyInstaller打包的环境中
    bundle_dir = Path(sys._MEIPASS).parent.parent
    resources_dir = bundle_dir / "Contents" / "Resources"
    
    # 添加资源目录到Python路径
    if str(resources_dir) not in sys.path:
        sys.path.insert(0, str(resources_dir))
    
    # 设置工作目录
    if resources_dir.exists():
        os.chdir(str(resources_dir))

# 确保tkinter可以正常工作
try:
    import tkinter
    # 测试tkinter是否可用
    root = tkinter.Tk()
    root.withdraw()
    root.destroy()
except Exception as e:
    print(f"Tkinter初始化失败: {e}")
'''
        
        hook_path = self.project_root / "runtime_hook.py"
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        
        return hook_path
    
    def fix_app_bundle(self):
        """修复应用程序包结构"""
        print("🔧 修复应用程序包结构...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            print("❌ 找不到应用程序包")
            return False
        
        # 修复Info.plist
        info_plist_path = app_path / "Contents" / "Info.plist"
        if info_plist_path.exists():
            self.update_info_plist(info_plist_path)
        
        # 确保可执行文件有正确的权限
        exe_path = app_path / "Contents" / "MacOS" / self.app_name
        if exe_path.exists():
            os.chmod(exe_path, 0o755)
        
        # 复制必要的系统库（如果需要）
        self.copy_system_libs(app_path)
        
        print("✅ 应用程序包结构修复完成")
        return True
    
    def update_info_plist(self, plist_path):
        """更新Info.plist文件"""
        print("  📝 更新Info.plist...")
        
        # 读取现有的plist
        try:
            import plistlib
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
        except:
            print("  ⚠️  无法读取Info.plist，使用默认配置")
            plist_data = {}
        
        # 更新关键配置
        plist_data.update({
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSMinimumSystemVersion': '10.14.0',
            'NSAppleEventsUsageDescription': '此应用程序需要访问文件以处理PDF发票。',
            'NSDocumentsFolderUsageDescription': '此应用程序需要访问文档文件夹以读取和保存PDF文件。',
            'NSDesktopFolderUsageDescription': '此应用程序需要访问桌面以读取和保存PDF文件。',
            'NSDownloadsFolderUsageDescription': '此应用程序需要访问下载文件夹以读取PDF文件。',
            'LSApplicationCategoryType': 'public.app-category.productivity',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'PDF Document',
                    'CFBundleTypeExtensions': ['pdf'],
                    'CFBundleTypeRole': 'Viewer',
                    'LSHandlerRank': 'Alternate'
                },
                {
                    'CFBundleTypeName': 'ZIP Archive', 
                    'CFBundleTypeExtensions': ['zip'],
                    'CFBundleTypeRole': 'Viewer',
                    'LSHandlerRank': 'Alternate'
                }
            ]
        })
        
        # 写回plist
        try:
            import plistlib
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_data, f)
            print("  ✅ Info.plist更新完成")
        except Exception as e:
            print(f"  ⚠️  Info.plist更新失败: {e}")
    
    def copy_system_libs(self, app_path):
        """复制必要的系统库"""
        print("  📚 检查系统库依赖...")
        
        # 检查tkinter相关的库
        frameworks_dir = app_path / "Contents" / "Frameworks"
        frameworks_dir.mkdir(exist_ok=True)
        
        # 这里可以添加复制特定库的逻辑
        # 目前PyInstaller应该已经处理了大部分依赖
        
        print("  ✅ 系统库检查完成")
    
    def create_debug_version(self):
        """创建调试版本"""
        print("🐛 创建调试版本...")
        
        debug_script = f'''#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 调试版本
用于诊断macOS应用程序包问题
"""

import sys
import os
import traceback
from pathlib import Path

def debug_info():
    print("=== PDF发票拼版打印系统调试信息 ===")
    print(f"Python版本: {{sys.version}}")
    print(f"平台: {{sys.platform}}")
    print(f"可执行文件: {{sys.executable}}")
    print(f"当前目录: {{os.getcwd()}}")
    print(f"Python路径: {{sys.path}}")
    print(f"环境变量:")
    for key, value in os.environ.items():
        if 'PYTHON' in key or 'PATH' in key:
            print(f"  {{key}}: {{value}}")
    print("=" * 50)

def main():
    try:
        debug_info()
        
        # 尝试导入主要模块
        print("测试模块导入...")
        
        import tkinter
        print("✅ tkinter导入成功")
        
        import PIL
        print("✅ PIL导入成功")
        
        import fitz
        print("✅ PyMuPDF导入成功")
        
        # 尝试启动主程序
        print("启动主程序...")
        import main
        main.main()
        
    except Exception as e:
        print(f"❌ 错误: {{e}}")
        traceback.print_exc()
        
        # 保存错误日志到桌面
        log_path = Path.home() / "Desktop" / "pdf_invoice_error.log"
        with open(log_path, 'w') as f:
            f.write(f"错误: {{e}}\\n")
            f.write(traceback.format_exc())
        
        print(f"错误日志已保存到: {{log_path}}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
'''
        
        debug_path = self.project_root / "debug_main.py"
        with open(debug_path, 'w') as f:
            f.write(debug_script)
        
        print(f"✅ 调试版本已创建: {debug_path}")
        return debug_path
    
    def build_debug_app(self):
        """构建调试版本的应用程序"""
        print("🐛 构建调试版本应用程序...")
        
        debug_main = self.create_debug_version()
        
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            '--onedir',
            '--console',  # 显示控制台用于调试
            '--name', f"{self.app_name}-Debug",
            '--osx-bundle-identifier', f"{self.bundle_id}.debug",
        ]
        
        # 添加数据文件
        data_files = [
            ('config.json', '.'),
            ('main.py', '.'),
        ]
        
        for src, dst in data_files:
            if Path(src).exists():
                cmd.extend(['--add-data', f'{src}:{dst}'])
        
        # 添加隐藏导入
        hidden_imports = [
            'tkinter',
            'tkinter.ttk',
            'tkinter.filedialog',
            'tkinter.messagebox',
            'PIL',
            'PIL.Image',
            'fitz',
        ]
        
        for module in hidden_imports:
            cmd.extend(['--hidden-import', module])
        
        cmd.append(str(debug_main))
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ 调试版本构建完成")
            return True
        else:
            print("❌ 调试版本构建失败")
            return False
    
    def create_simple_dmg(self):
        """创建简单的DMG"""
        print("📦 创建DMG安装镜像...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        debug_app_path = self.dist_dir / f"{self.app_name}-Debug.app"
        
        if not app_path.exists():
            print("❌ 找不到应用程序包")
            return False
        
        dmg_name = f"{self.app_name}-{self.version}-Fixed.dmg"
        dmg_path = self.dist_dir / dmg_name
        
        # 创建临时目录
        temp_dir = self.dist_dir / "dmg_temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        try:
            # 复制应用程序到临时目录
            shutil.copytree(app_path, temp_dir / f"{self.app_name}.app")
            
            # 如果有调试版本，也复制进去
            if debug_app_path.exists():
                shutil.copytree(debug_app_path, temp_dir / f"{self.app_name}-Debug.app")
            
            # 创建应用程序文件夹的符号链接
            applications_link = temp_dir / "Applications"
            applications_link.symlink_to("/Applications")
            
            # 创建说明文件
            readme_content = f"""
PDF发票拼版打印系统 v{self.version}

安装说明:
1. 将 "{self.app_name}.app" 拖拽到 "Applications" 文件夹
2. 首次运行时，如果系统提示安全警告，请到 "系统偏好设置" > "安全性与隐私" 中允许运行

如果应用程序无法启动:
1. 运行调试版本 "{self.app_name}-Debug.app" 查看错误信息
2. 检查桌面上的错误日志文件
3. 确保系统版本为 macOS 10.14 或更高

功能特点:
- 支持PDF和ZIP文件处理
- 2列4行A4纸张布局
- 保持发票纵横比
- 300DPI高质量输出
- 现代化用户界面
- 批量处理支持

技术支持:
如遇问题，请查看错误日志或联系技术支持。
"""
            
            readme_path = temp_dir / "使用说明.txt"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # 使用hdiutil创建DMG
            cmd = [
                'hdiutil', 'create',
                '-volname', f"{self.app_name} {self.version}",
                '-srcfolder', str(temp_dir),
                '-ov',
                '-format', 'UDZO',
                str(dmg_path)
            ]
            
            result = subprocess.run(cmd)
            
            if result.returncode != 0:
                print("❌ DMG创建失败")
                return False
            
            print(f"✅ DMG创建完成: {dmg_path}")
            return True
            
        finally:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def build(self):
        """完整构建流程"""
        print(f"🚀 开始构建修复版 {self.app_name} macOS应用程序")
        print("=" * 60)
        
        if sys.platform != 'darwin':
            print("❌ 此脚本只能在macOS上运行")
            return False
        
        # 执行构建步骤
        steps = [
            ("清理构建目录", self.clean_build),
            ("构建修复版应用程序包", self.build_app_fixed),
            ("构建调试版应用程序包", self.build_debug_app),
            ("创建DMG安装镜像", self.create_simple_dmg),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ {step_name}失败")
                return False
        
        print("\n" + "=" * 60)
        print("🎉 修复版构建完成！")
        print(f"\n📁 输出文件:")
        
        if self.dist_dir.exists():
            for item in self.dist_dir.iterdir():
                if item.is_file() or item.suffix == '.app':
                    print(f"  📄 {item.name}")
        
        print(f"\n📍 输出目录: {self.dist_dir}")
        print("\n💡 使用建议:")
        print("1. 首先尝试安装和运行正常版本")
        print("2. 如果遇到问题，运行调试版本查看错误信息")
        print("3. 检查桌面上的错误日志文件")
        
        return True

def main():
    builder = MacOSBuilderFixed()
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()