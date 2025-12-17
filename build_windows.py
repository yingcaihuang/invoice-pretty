#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows EXE打包构建脚本
使用PyInstaller创建Windows可执行文件和安装包
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil
import platform

# 设置Windows控制台编码
if sys.platform == 'win32':
    import locale
    try:
        # 尝试设置UTF-8编码
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # 如果失败，使用系统默认编码
        pass

def safe_print(message):
    """安全的打印函数，处理编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 如果包含无法编码的字符，使用ASCII替代
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(safe_message)

def check_windows_environment():
    """检查Windows构建环境"""
    safe_print("[INFO] 检查Windows构建环境...")
    
    # 检查操作系统
    if platform.system() != 'Windows':
        safe_print("[WARN] 警告: 当前不是Windows系统，但可以创建Windows构建配置")
        return True
    
    # 检查Python版本
    python_version = sys.version_info
    safe_print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        safe_print("[ERROR] Python版本过低，建议使用Python 3.8+")
        return False
    
    # 检查PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, check=True)
        safe_print(f"[OK] PyInstaller版本: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        safe_print("[ERROR] PyInstaller未安装，请运行: pip install pyinstaller")
        return False
    
    # 检查必要的依赖
    required_packages = ['tkinter', 'PIL', 'fitz']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'PIL':
                import PIL
            elif package == 'fitz':
                import fitz
            safe_print(f"[OK] {package}已安装")
        except ImportError:
            missing_packages.append(package)
            safe_print(f"[ERROR] {package}未安装")
    
    if missing_packages:
        safe_print(f"请安装缺失的包: {', '.join(missing_packages)}")
        return False
    
    return True

def clean_build_files():
    """清理构建文件"""
    safe_print("[INFO] 清理旧的构建文件...")
    
    try:
        dirs_to_clean = ['build', 'dist']
        for dir_name in dirs_to_clean:
            if Path(dir_name).exists():
                shutil.rmtree(dir_name)
                safe_print(f"已清理: {dir_name}/")
        
        # 清理spec文件
        spec_files = list(Path('.').glob('*.spec'))
        for spec_file in spec_files:
            if 'windows' in spec_file.name.lower():
                spec_file.unlink()
                safe_print(f"已清理: {spec_file}")
        
        safe_print("[OK] 构建文件清理完成")
        return True
        
    except Exception as e:
        safe_print(f"[WARN] 清理构建文件时遇到问题: {e}")
        safe_print("[INFO] 继续构建过程...")
        return True  # 即使清理失败也继续构建

def create_windows_icon():
    """创建Windows图标文件"""
    safe_print("[INFO] 准备Windows图标...")
    
    # 检查是否有图标文件
    icon_paths = [
        'assets/icon.ico',
        'assets/app_icon.ico', 
        'icon.ico'
    ]
    
    for icon_path in icon_paths:
        if Path(icon_path).exists():
            safe_print(f"[OK] 找到图标文件: {icon_path}")
            return icon_path
    
    safe_print("[WARN] 未找到.ico图标文件，将使用默认图标")
    return None

def build_windows_exe():
    """构建Windows EXE文件"""
    safe_print("[INFO] 构建Windows EXE文件...")
    
    # 获取图标文件
    icon_file = create_windows_icon()
    
    # 检测平台并设置正确的分隔符
    if platform.system() == 'Windows':
        data_separator = ';'
    else:
        data_separator = ':'
    
    # 构建PyInstaller命令
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        '--onefile',  # 单文件模式
        '--windowed',  # 无控制台窗口
        '--name', 'PDF发票拼版打印系统',
        
        # 添加数据文件
        '--add-data', f'src{data_separator}src',
        '--add-data', f'config.json{data_separator}.',
        
        # 添加隐藏导入
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
        
        # 主程序文件
        'main.py'
    ]
    
    # 添加图标
    if icon_file:
        cmd.extend(['--icon', icon_file])
    
    safe_print("执行构建命令...")
    safe_print(f"命令: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        safe_print("[OK] Windows EXE构建完成")
        return True
    else:
        safe_print("[ERROR] Windows EXE构建失败")
        return False

def create_windows_installer():
    """创建Windows安装程序"""
    safe_print("[INFO] 创建Windows安装程序...")
    
    exe_path = Path("dist/PDF发票拼版打印系统.exe")
    if not exe_path.exists():
        safe_print("[ERROR] 找不到EXE文件")
        return False
    
    # 检查是否有NSIS或Inno Setup
    installer_tools = {
        'nsis': ['makensis', '/VERSION'],
        'inno': ['iscc', '/?']
    }
    
    available_tool = None
    for tool_name, test_cmd in installer_tools.items():
        try:
            subprocess.run(test_cmd, capture_output=True, check=True)
            available_tool = tool_name
            safe_print(f"[OK] 找到安装程序工具: {tool_name}")
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not available_tool:
        safe_print("[WARN] 未找到NSIS或Inno Setup，跳过安装程序创建")
        safe_print("[INFO] 提示: 可以手动创建安装程序或使用便携版EXE")
        return True
    
    # 创建简单的安装脚本
    if available_tool == 'nsis':
        return create_nsis_installer(exe_path)
    elif available_tool == 'inno':
        return create_inno_installer(exe_path)
    
    return True

def create_nsis_installer(exe_path):
    """创建NSIS安装脚本"""
    nsis_script = f'''
; PDF发票拼版打印系统 NSIS安装脚本
!define APPNAME "PDF发票拼版打印系统"
!define APPVERSION "1.0.0"
!define APPEXE "PDF发票拼版打印系统.exe"

Name "${{APPNAME}}"
OutFile "dist\\PDF发票拼版打印系统-安装程序.exe"
InstallDir "$PROGRAMFILES\\${{APPNAME}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File "{exe_path}"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPEXE}}"
    CreateShortCut "$SMPROGRAMS\\${{APPNAME}}\\卸载.lnk" "$INSTDIR\\uninstall.exe"
    
    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPEXE}}"
    
    ; 写入卸载信息
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\${{APPEXE}}"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk"
    Delete "$SMPROGRAMS\\${{APPNAME}}\\卸载.lnk"
    RMDir "$SMPROGRAMS\\${{APPNAME}}"
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
SectionEnd
'''
    
    script_path = Path("installer.nsi")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    try:
        result = subprocess.run(['makensis', str(script_path)], check=True)
        safe_print("[OK] NSIS安装程序创建完成")
        script_path.unlink()  # 删除临时脚本
        return True
    except subprocess.CalledProcessError:
        safe_print("[ERROR] NSIS安装程序创建失败")
        return False

def create_inno_installer(exe_path):
    """创建Inno Setup安装脚本"""
    inno_script = f'''
[Setup]
AppName=PDF发票拼版打印系统
AppVersion=1.0.0
DefaultDirName={{pf}}\\PDF发票拼版打印系统
DefaultGroupName=PDF发票拼版打印系统
OutputDir=dist
OutputBaseFilename=PDF发票拼版打印系统-安装程序
Compression=lzma
SolidCompression=yes

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\PDF发票拼版打印系统"; Filename: "{{app}}\\PDF发票拼版打印系统.exe"
Name: "{{commondesktop}}\\PDF发票拼版打印系统"; Filename: "{{app}}\\PDF发票拼版打印系统.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\PDF发票拼版打印系统.exe"; Description: "启动PDF发票拼版打印系统"; Flags: nowait postinstall skipifsilent
'''
    
    script_path = Path("installer.iss")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(inno_script)
    
    try:
        result = subprocess.run(['iscc', str(script_path)], check=True)
        safe_print("[OK] Inno Setup安装程序创建完成")
        script_path.unlink()  # 删除临时脚本
        return True
    except subprocess.CalledProcessError:
        safe_print("[ERROR] Inno Setup安装程序创建失败")
        return False

def create_portable_package():
    """创建便携版打包"""
    safe_print("[INFO] 创建便携版打包...")
    
    exe_path = Path("dist/PDF发票拼版打印系统.exe")
    if not exe_path.exists():
        safe_print("[ERROR] 找不到EXE文件")
        return False
    
    # 创建便携版目录
    portable_dir = Path("dist/PDF发票拼版打印系统-便携版")
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir()
    
    # 复制EXE文件
    shutil.copy2(exe_path, portable_dir / "PDF发票拼版打印系统.exe")
    
    # 创建说明文件
    readme_content = """PDF发票拼版打印系统 - 便携版

使用说明:
1. 双击"PDF发票拼版打印系统.exe"启动程序
2. 选择PDF发票文件或ZIP压缩包
3. 选择输出目录
4. 点击"开始拼版处理"

功能特点:
- 支持12306电子发票PDF文件
- 支持ZIP压缩包批量处理
- 2列4行拼版布局，节省纸张
- 现代化图形界面
- 实时处理进度显示

系统要求:
- Windows 7/8/10/11
- 无需安装，直接运行

技术支持:
如有问题，请查看程序界面中的处理日志信息。
"""
    
    readme_path = portable_dir / "使用说明.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建ZIP压缩包
    try:
        import zipfile
        zip_path = Path("dist/PDF发票拼版打印系统-便携版.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in portable_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(portable_dir.parent)
                    zipf.write(file_path, arcname)
        
        safe_print(f"[OK] 便携版ZIP创建完成: {zip_path}")
        return True
        
    except Exception as e:
        safe_print(f"[ERROR] 创建便携版ZIP失败: {e}")
        return False

def show_build_results():
    """显示构建结果"""
    safe_print("\n" + "="*60)
    safe_print("Windows构建完成！")
    safe_print("="*60)
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        safe_print("[ERROR] 未找到dist目录")
        return
    
    safe_print("\n生成的文件:")
    
    # 检查EXE文件
    exe_file = dist_dir / "PDF发票拼版打印系统.exe"
    if exe_file.exists():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        safe_print(f"  [OK] EXE文件: {exe_file} ({size_mb:.1f} MB)")
    
    # 检查安装程序
    installer_files = list(dist_dir.glob("*安装程序*"))
    for installer in installer_files:
        if installer.is_file():
            size_mb = installer.stat().st_size / (1024 * 1024)
            safe_print(f"  [OK] 安装程序: {installer} ({size_mb:.1f} MB)")
    
    # 检查便携版
    portable_zip = dist_dir / "PDF发票拼版打印系统-便携版.zip"
    if portable_zip.exists():
        size_mb = portable_zip.stat().st_size / (1024 * 1024)
        safe_print(f"  [OK] 便携版: {portable_zip} ({size_mb:.1f} MB)")
    
    portable_dir = dist_dir / "PDF发票拼版打印系统-便携版"
    if portable_dir.exists():
        safe_print(f"  [OK] 便携版目录: {portable_dir}")
    
    safe_print("\n使用建议:")
    safe_print("  - EXE文件: 适合个人使用，双击即可运行")
    safe_print("  - 安装程序: 适合正式部署，包含开始菜单和桌面快捷方式")
    safe_print("  - 便携版: 适合分发和移动使用，无需安装")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Windows EXE构建工具')
    parser.add_argument('--check', action='store_true', help='仅检查构建环境')
    parser.add_argument('--exe-only', action='store_true', help='仅构建EXE文件')
    parser.add_argument('--installer-only', action='store_true', help='仅创建安装程序')
    parser.add_argument('--portable-only', action='store_true', help='仅创建便携版')
    parser.add_argument('--no-clean', action='store_true', help='不清理旧文件')
    args = parser.parse_args()
    
    safe_print("PDF发票拼版打印系统 - Windows构建")
    safe_print("=" * 60)
    
    # 检查构建环境
    if not check_windows_environment():
        safe_print("[ERROR] 构建环境检查失败")
        return False
    
    if args.check:
        safe_print("[OK] 构建环境检查通过")
        return True
    
    # 构建步骤
    steps = []
    
    if not args.no_clean and not args.installer_only and not args.portable_only:
        steps.append(("清理构建文件", clean_build_files))
    
    if not args.installer_only and not args.portable_only:
        steps.append(("构建Windows EXE", build_windows_exe))
    
    if args.installer_only or (not args.exe_only and not args.portable_only):
        steps.append(("创建安装程序", create_windows_installer))
    
    if args.portable_only or (not args.exe_only and not args.installer_only):
        steps.append(("创建便携版", create_portable_package))
    
    # 执行构建步骤
    for step_name, step_func in steps:
        safe_print(f"\n[INFO] {step_name}...")
        if not step_func():
            safe_print(f"[ERROR] {step_name}失败")
            return False
    
    # 显示构建结果
    show_build_results()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)