#!/usr/bin/env python3
"""
发布管理脚本
用于本地测试构建和管理GitHub发布
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import argparse
from datetime import datetime

class ReleaseManager:
    def __init__(self):
        self.project_root = Path.cwd()
        self.version = self._get_version()
        
    def _get_version(self):
        """获取当前版本号"""
        # 尝试从git标签获取版本
        try:
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # 如果没有标签，使用默认版本
            return "v1.0.0"
    
    def check_environment(self):
        """检查发布环境"""
        print("🔍 检查发布环境...")
        
        # 检查git状态
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                print("⚠️  工作目录有未提交的更改")
                print("建议先提交所有更改再进行发布")
            else:
                print("✅ Git工作目录干净")
        except subprocess.CalledProcessError:
            print("❌ 无法检查Git状态")
            return False
        
        # 检查必要文件
        required_files = [
            'build_windows.py',
            'build_macos.py',
            'requirements.txt',
            '.github/workflows/build-and-release.yml'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ 缺少必要文件:")
            for file_path in missing_files:
                print(f"  - {file_path}")
            return False
        
        print("✅ 所有必要文件存在")
        return True
    
    def test_local_build(self, platform=None):
        """测试本地构建"""
        print(f"🔨 测试本地构建 (平台: {platform or '当前平台'})...")
        
        import platform as plt
        current_platform = plt.system().lower()
        
        if platform is None:
            platform = current_platform
        
        if platform == 'windows' or current_platform == 'windows':
            return self._test_windows_build()
        elif platform == 'darwin' or current_platform == 'darwin':
            return self._test_macos_build()
        else:
            print(f"⚠️  平台 {platform} 不支持本地构建测试")
            return True
    
    def _test_windows_build(self):
        """测试Windows构建"""
        print("  测试Windows构建环境...")
        
        try:
            result = subprocess.run([sys.executable, 'build_windows.py', '--check'], 
                                  check=True)
            print("✅ Windows构建环境检查通过")
            return True
        except subprocess.CalledProcessError:
            print("❌ Windows构建环境检查失败")
            return False
    
    def _test_macos_build(self):
        """测试macOS构建"""
        print("  测试macOS构建环境...")
        
        try:
            # 测试导入修复版构建脚本
            result = subprocess.run([sys.executable, 'build_import_fixed.py', '--help'], 
                                  capture_output=True, check=True)
            print("✅ macOS导入修复版构建脚本可用")
            return True
        except subprocess.CalledProcessError:
            print("❌ macOS导入修复版构建脚本检查失败")
            return False
    
    def create_tag(self, version, message=None):
        """创建Git标签"""
        print(f"🏷️  创建版本标签: {version}")
        
        if not version.startswith('v'):
            version = f'v{version}'
        
        if message is None:
            message = f"Release {version}"
        
        try:
            # 创建标签
            subprocess.run(['git', 'tag', '-a', version, '-m', message], check=True)
            print(f"✅ 标签 {version} 创建成功")
            
            # 推送标签
            push = input("是否推送标签到远程仓库? (y/N): ").lower().strip()
            if push == 'y':
                subprocess.run(['git', 'push', 'origin', version], check=True)
                print(f"✅ 标签 {version} 已推送到远程仓库")
                print("🚀 GitHub Actions将自动开始构建...")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建标签失败: {e}")
            return False
    
    def list_releases(self):
        """列出现有的发布版本"""
        print("📋 现有发布版本:")
        
        try:
            # 获取所有标签
            result = subprocess.run(['git', 'tag', '-l'], 
                                  capture_output=True, text=True, check=True)
            tags = result.stdout.strip().split('\n')
            
            if not tags or tags == ['']:
                print("  暂无发布版本")
                return
            
            # 按版本排序
            version_tags = [tag for tag in tags if tag.startswith('v')]
            version_tags.sort(reverse=True)
            
            for tag in version_tags[:10]:  # 显示最近10个版本
                # 获取标签信息
                try:
                    tag_info = subprocess.run(['git', 'show', '--format=%ci %s', '--no-patch', tag],
                                            capture_output=True, text=True, check=True)
                    info_lines = tag_info.stdout.strip().split('\n')
                    if info_lines:
                        date_msg = info_lines[0]
                        print(f"  {tag}: {date_msg}")
                except subprocess.CalledProcessError:
                    print(f"  {tag}")
                    
        except subprocess.CalledProcessError:
            print("❌ 无法获取版本信息")
    
    def generate_changelog(self, since_tag=None):
        """生成更新日志"""
        print("📝 生成更新日志...")
        
        try:
            if since_tag:
                cmd = ['git', 'log', f'{since_tag}..HEAD', '--oneline']
            else:
                cmd = ['git', 'log', '--oneline', '-10']  # 最近10次提交
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = result.stdout.strip().split('\n')
            
            if not commits or commits == ['']:
                print("  没有新的提交")
                return ""
            
            changelog = []
            changelog.append(f"## 更新内容 ({datetime.now().strftime('%Y-%m-%d')})")
            changelog.append("")
            
            for commit in commits:
                if commit.strip():
                    # 简单的提交信息格式化
                    hash_msg = commit.split(' ', 1)
                    if len(hash_msg) == 2:
                        commit_hash, message = hash_msg
                        changelog.append(f"- {message} ({commit_hash[:7]})")
            
            changelog_text = '\n'.join(changelog)
            print(changelog_text)
            
            return changelog_text
            
        except subprocess.CalledProcessError:
            print("❌ 无法生成更新日志")
            return ""
    
    def check_github_actions(self):
        """检查GitHub Actions状态"""
        print("🔍 检查GitHub Actions配置...")
        
        workflow_file = self.project_root / '.github' / 'workflows' / 'build-and-release.yml'
        
        if not workflow_file.exists():
            print("❌ 未找到GitHub Actions工作流文件")
            return False
        
        print("✅ GitHub Actions工作流文件存在")
        
        # 检查工作流语法 (简单检查)
        try:
            import yaml
            with open(workflow_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print("✅ 工作流文件语法正确")
        except ImportError:
            print("⚠️  无法验证YAML语法 (需要安装PyYAML)")
        except yaml.YAMLError as e:
            print(f"❌ 工作流文件语法错误: {e}")
            return False
        
        return True
    
    def interactive_release(self):
        """交互式发布流程"""
        print("🚀 PDF发票拼版打印系统 - 交互式发布")
        print("=" * 50)
        
        # 1. 检查环境
        if not self.check_environment():
            print("❌ 环境检查失败，请修复问题后重试")
            return False
        
        # 2. 显示当前版本
        print(f"\n📋 当前版本: {self.version}")
        
        # 3. 列出现有版本
        self.list_releases()
        
        # 4. 输入新版本号
        print(f"\n📝 输入新版本号:")
        new_version = input(f"版本号 (当前: {self.version}): ").strip()
        
        if not new_version:
            print("❌ 版本号不能为空")
            return False
        
        if not new_version.startswith('v'):
            new_version = f'v{new_version}'
        
        # 5. 生成更新日志
        changelog = self.generate_changelog(self.version)
        
        # 6. 确认发布
        print(f"\n📋 发布信息:")
        print(f"  版本: {new_version}")
        print(f"  当前分支: ", end="")
        try:
            branch = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=True)
            print(branch.stdout.strip())
        except subprocess.CalledProcessError:
            print("未知")
        
        print(f"\n更新内容:")
        if changelog:
            print(changelog)
        else:
            print("  (无新提交)")
        
        confirm = input(f"\n确认发布版本 {new_version}? (y/N): ").lower().strip()
        
        if confirm != 'y':
            print("❌ 发布已取消")
            return False
        
        # 7. 创建标签并推送
        message = f"Release {new_version}"
        if changelog:
            message += f"\n\n{changelog}"
        
        return self.create_tag(new_version, message)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='发布管理工具')
    parser.add_argument('--check', action='store_true', help='检查发布环境')
    parser.add_argument('--test-build', choices=['windows', 'macos'], help='测试本地构建')
    parser.add_argument('--list', action='store_true', help='列出现有版本')
    parser.add_argument('--changelog', help='生成更新日志 (指定起始标签)')
    parser.add_argument('--tag', help='创建版本标签')
    parser.add_argument('--interactive', action='store_true', help='交互式发布流程')
    
    args = parser.parse_args()
    
    manager = ReleaseManager()
    
    if args.check:
        success = manager.check_environment()
        success &= manager.check_github_actions()
        sys.exit(0 if success else 1)
    
    elif args.test_build:
        success = manager.test_local_build(args.test_build)
        sys.exit(0 if success else 1)
    
    elif args.list:
        manager.list_releases()
    
    elif args.changelog:
        manager.generate_changelog(args.changelog)
    
    elif args.tag:
        success = manager.create_tag(args.tag)
        sys.exit(0 if success else 1)
    
    elif args.interactive:
        success = manager.interactive_release()
        sys.exit(0 if success else 1)
    
    else:
        # 默认显示帮助
        parser.print_help()

if __name__ == '__main__':
    main()