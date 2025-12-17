#!/usr/bin/env python3
"""
macOS应用程序打包脚本
生成.app应用程序包和.dmg安装镜像
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

class MacOSBuilder:
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
                    # 尝试强制删除
                    import subprocess
                    subprocess.run(['rm', '-rf', str(dir_path)], check=False)
        
        # 清理PyInstaller缓存
        try:
            pycache_dirs = list(self.project_root.rglob("__pycache__"))
            for cache_dir in pycache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
        except Exception as e:
            print(f"  警告: 清理缓存时出错: {e}")
        
        print("✅ 清理完成")
    
    def check_dependencies(self):
        """检查构建依赖"""
        print("🔍 检查构建依赖...")
        
        required_tools = {
            'pyinstaller': 'PyInstaller',
            'create-dmg': 'create-dmg (用于生成DMG)'
        }
        
        missing_tools = []
        
        for tool, description in required_tools.items():
            try:
                result = subprocess.run([tool, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {description}")
                else:
                    missing_tools.append((tool, description))
            except FileNotFoundError:
                missing_tools.append((tool, description))
        
        if missing_tools:
            print("❌ 缺少以下工具:")
            for tool, description in missing_tools:
                print(f"  - {description}")
                if tool == 'pyinstaller':
                    print("    安装: pip install pyinstaller")
                elif tool == 'create-dmg':
                    print("    安装: brew install create-dmg")
            return False
        
        print("✅ 所有依赖检查通过")
        return True
    
    def create_app_icon(self):
        """创建应用程序图标"""
        print("🎨 创建应用程序图标...")
        
        # 创建图标目录
        icon_dir = self.project_root / "assets"
        icon_dir.mkdir(exist_ok=True)
        
        # 如果没有图标，创建一个简单的图标
        icon_path = icon_dir / "app_icon.icns"
        if not icon_path.exists():
            print("  📝 创建默认图标...")
            # 这里可以添加创建默认图标的逻辑
            # 暂时跳过，使用系统默认图标
            print("  ⚠️  使用系统默认图标")
        
        return icon_path if icon_path.exists() else None
    
    def build_app(self):
        """构建.app应用程序包"""
        print("🔨 构建macOS应用程序包...")
        
        # 创建图标
        icon_path = self.create_app_icon()
        
        # 构建PyInstaller命令
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            '--onedir',  # 使用目录模式而不是单文件
            '--windowed',  # 无控制台窗口
            '--name', self.app_name,
            '--osx-bundle-identifier', self.bundle_id,
        ]
        
        # 添加图标
        if icon_path:
            cmd.extend(['--icon', str(icon_path)])
        
        # 添加数据文件
        data_files = [
            ('config.json', '.'),
            ('CONFIG.md', '.'),
            ('README.md', '.'),
        ]
        
        for src, dst in data_files:
            if (self.project_root / src).exists():
                cmd.extend(['--add-data', f'{src}:{dst}'])
        
        # 添加隐藏导入
        hidden_imports = [
            'PIL._tkinter_finder',
            'tkinter',
            'tkinter.ttk',
            'tkinter.filedialog',
            'tkinter.messagebox',
            'fitz',
            'PIL',
            'PIL.Image',
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
        ]
        
        for module in excludes:
            cmd.extend(['--exclude-module', module])
        
        # 添加主程序
        cmd.append('main.py')
        
        print(f"  执行命令: {' '.join(cmd)}")
        
        # 执行构建
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ 应用程序构建失败")
            return False
        
        print("✅ 应用程序构建完成")
        return True
    
    def create_dmg(self):
        """创建DMG安装镜像"""
        print("📦 创建DMG安装镜像...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            print("❌ 找不到应用程序包")
            return False
        
        dmg_name = f"{self.app_name}-{self.version}.dmg"
        dmg_path = self.dist_dir / dmg_name
        
        # 删除已存在的DMG
        if dmg_path.exists():
            dmg_path.unlink()
        
        # 创建DMG
        cmd = [
            'create-dmg',
            '--volname', f"{self.app_name} {self.version}",
            '--volicon', str(app_path / "Contents" / "Resources" / "icon.icns") if (app_path / "Contents" / "Resources" / "icon.icns").exists() else "",
            '--window-pos', '200', '120',
            '--window-size', '600', '400',
            '--icon-size', '100',
            '--icon', f"{self.app_name}.app", '175', '120',
            '--hide-extension', f"{self.app_name}.app",
            '--app-drop-link', '425', '120',
            str(dmg_path),
            str(app_path)
        ]
        
        # 过滤空参数
        cmd = [arg for arg in cmd if arg]
        
        print(f"  执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ DMG创建失败")
            return False
        
        print(f"✅ DMG创建完成: {dmg_path}")
        return True
    
    def create_simple_dmg(self):
        """创建简单的DMG（不依赖create-dmg工具）"""
        print("📦 创建简单DMG安装镜像...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            print("❌ 找不到应用程序包")
            return False
        
        dmg_name = f"{self.app_name}-{self.version}.dmg"
        dmg_path = self.dist_dir / dmg_name
        
        # 创建临时目录
        temp_dir = self.dist_dir / "dmg_temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        try:
            # 复制应用程序到临时目录
            shutil.copytree(app_path, temp_dir / f"{self.app_name}.app")
            
            # 创建应用程序文件夹的符号链接
            applications_link = temp_dir / "Applications"
            applications_link.symlink_to("/Applications")
            
            # 使用hdiutil创建DMG
            cmd = [
                'hdiutil', 'create',
                '-volname', f"{self.app_name} {self.version}",
                '-srcfolder', str(temp_dir),
                '-ov',
                '-format', 'UDZO',
                str(dmg_path)
            ]
            
            print(f"  执行命令: {' '.join(cmd)}")
            
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
    
    def sign_app(self):
        """代码签名（可选）"""
        print("🔐 代码签名...")
        
        # 检查是否有开发者证书
        result = subprocess.run(['security', 'find-identity', '-v', '-p', 'codesigning'],
                              capture_output=True, text=True)
        
        if "0 valid identities found" in result.stdout:
            print("  ⚠️  未找到代码签名证书，跳过签名")
            return True
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        
        # 执行代码签名
        cmd = [
            'codesign',
            '--force',
            '--verify',
            '--verbose',
            '--sign', '-',  # 使用ad-hoc签名
            str(app_path)
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✅ 代码签名完成")
        else:
            print("⚠️  代码签名失败，但不影响应用程序运行")
        
        return True
    
    def create_installer_info(self):
        """创建安装信息文件"""
        print("📝 创建安装信息...")
        
        info = {
            "name": self.app_name,
            "version": self.version,
            "bundle_id": self.bundle_id,
            "description": "智能处理12306电子发票，支持PDF和ZIP文件，一键生成拼版打印文件",
            "requirements": {
                "macos": "10.14+",
                "architecture": ["x86_64", "arm64"]
            },
            "features": [
                "支持PDF和ZIP文件处理",
                "2列4行A4纸张布局",
                "保持发票纵横比",
                "300DPI高质量输出",
                "现代化用户界面",
                "批量处理支持"
            ]
        }
        
        info_path = self.dist_dir / "app_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 安装信息已保存: {info_path}")
    
    def build(self):
        """完整构建流程"""
        print(f"🚀 开始构建 {self.app_name} macOS应用程序")
        print("=" * 60)
        
        # 检查系统
        if sys.platform != 'darwin':
            print("❌ 此脚本只能在macOS上运行")
            return False
        
        # 执行构建步骤
        steps = [
            ("清理构建目录", self.clean_build),
            ("检查构建依赖", self.check_dependencies),
            ("构建应用程序包", self.build_app),
            ("代码签名", self.sign_app),
            ("创建安装信息", self.create_installer_info),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ {step_name}失败")
                return False
        
        # 尝试创建DMG
        print(f"\n📋 创建DMG安装镜像...")
        if not self.create_dmg():
            print("  尝试使用简单方法创建DMG...")
            if not self.create_simple_dmg():
                print("  ⚠️  DMG创建失败，但应用程序包已生成")
        
        print("\n" + "=" * 60)
        print("🎉 构建完成！")
        print(f"\n📁 输出文件:")
        
        # 列出生成的文件
        if self.dist_dir.exists():
            for item in self.dist_dir.iterdir():
                if item.is_file() or item.suffix == '.app':
                    size = self._get_size_str(item)
                    print(f"  📄 {item.name} ({size})")
        
        print(f"\n📍 输出目录: {self.dist_dir}")
        
        return True
    
    def _get_size_str(self, path):
        """获取文件/目录大小的字符串表示"""
        if path.is_file():
            size = path.stat().st_size
        else:
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

def main():
    """主函数"""
    builder = MacOSBuilder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'clean':
            builder.clean_build()
        elif command == 'check':
            builder.check_dependencies()
        elif command == 'app':
            builder.build_app()
        elif command == 'dmg':
            builder.create_simple_dmg()
        else:
            print(f"未知命令: {command}")
            print("可用命令: clean, check, app, dmg")
    else:
        # 完整构建
        success = builder.build()
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()