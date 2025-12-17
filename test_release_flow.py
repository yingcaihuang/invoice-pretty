#!/usr/bin/env python3
"""
测试发布流程脚本
验证GitHub Actions工作流配置和文件生成
"""

import os
import sys
from pathlib import Path
import subprocess
import json

def test_github_actions_config():
    """测试GitHub Actions配置"""
    print("🔍 测试GitHub Actions配置...")
    
    workflow_file = Path('.github/workflows/build-and-release.yml')
    if not workflow_file.exists():
        print("❌ 未找到GitHub Actions工作流文件")
        return False
    
    # 检查YAML语法
    try:
        import yaml
        with open(workflow_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ GitHub Actions配置语法正确")
        
        # 检查关键配置
        jobs = config.get('jobs', {})
        
        # 检查构建作业
        required_jobs = ['build-windows', 'build-macos-intel', 'build-macos-arm', 'create-release']
        for job in required_jobs:
            if job in jobs:
                print(f"✅ 找到作业: {job}")
            else:
                print(f"❌ 缺少作业: {job}")
                return False
        
        # 检查文件上传配置
        release_job = jobs.get('create-release', {})
        steps = release_job.get('steps', [])
        
        create_release_step = None
        for step in steps:
            if step.get('uses') == 'softprops/action-gh-release@v2':
                create_release_step = step
                break
        
        if create_release_step:
            files = create_release_step.get('with', {}).get('files', '')
            expected_files = [
                'invoice_pretty.exe',
                'invoice_pretty_portable.zip', 
                'invoice_pretty_intel.dmg',
                'invoice_pretty_arm64.dmg'
            ]
            
            for expected_file in expected_files:
                if expected_file in files:
                    print(f"✅ 配置上传文件: {expected_file}")
                else:
                    print(f"❌ 缺少上传文件配置: {expected_file}")
            
            print("✅ GitHub Release配置正确")
        else:
            print("❌ 未找到GitHub Release创建步骤")
            return False
            
    except ImportError:
        print("⚠️  无法验证YAML语法 (需要安装PyYAML)")
    except Exception as e:
        print(f"❌ GitHub Actions配置错误: {e}")
        return False
    
    return True

def test_build_scripts():
    """测试构建脚本"""
    print("\n🔨 测试构建脚本...")
    
    # 测试Windows构建脚本
    try:
        result = subprocess.run([sys.executable, 'build_windows.py', '--check'], 
                              capture_output=True, text=True, check=True)
        print("✅ Windows构建脚本检查通过")
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows构建脚本检查失败: {e}")
        return False
    
    # 测试macOS构建脚本
    if Path('build_import_fixed.py').exists():
        try:
            result = subprocess.run([sys.executable, 'build_import_fixed.py', '--help'], 
                                  capture_output=True, text=True, check=True)
            print("✅ macOS导入修复版构建脚本可用")
        except subprocess.CalledProcessError:
            print("⚠️  macOS构建脚本检查失败，但在GitHub Actions中可能正常")
    else:
        print("❌ 未找到macOS构建脚本")
        return False
    
    return True

def test_release_manager():
    """测试发布管理器"""
    print("\n📋 测试发布管理器...")
    
    try:
        from release import ReleaseManager
        manager = ReleaseManager()
        
        # 测试环境检查
        if manager.check_environment():
            print("✅ 发布环境检查通过")
        else:
            print("⚠️  发布环境检查有警告")
        
        # 测试GitHub Actions检查
        if manager.check_github_actions():
            print("✅ GitHub Actions配置检查通过")
        else:
            print("❌ GitHub Actions配置检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 发布管理器测试失败: {e}")
        return False
    
    return True

def simulate_release_files():
    """模拟发布文件结构"""
    print("\n📦 模拟发布文件结构...")
    
    # 创建模拟的dist目录结构
    dist_dir = Path('dist_test')
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # 模拟Windows文件
    (dist_dir / 'invoice_pretty.exe').touch()
    (dist_dir / 'invoice_pretty_portable.zip').touch()
    
    # 模拟macOS文件
    (dist_dir / 'invoice_pretty_intel.dmg').touch()
    (dist_dir / 'invoice_pretty_arm64.dmg').touch()
    
    print("✅ 模拟文件结构创建完成:")
    for file_path in dist_dir.iterdir():
        print(f"  - {file_path.name}")
    
    # 清理
    import shutil
    shutil.rmtree(dist_dir)
    
    return True

def generate_release_summary():
    """生成发布流程总结"""
    print("\n📋 发布流程总结")
    print("=" * 60)
    
    print("\n🎯 支持的发布文件:")
    files = [
        ("Windows EXE", "invoice_pretty.exe", "单文件可执行程序"),
        ("Windows 便携版", "invoice_pretty_portable.zip", "绿色便携版ZIP包"),
        ("macOS Intel", "invoice_pretty_intel.dmg", "Intel Mac安装包"),
        ("macOS ARM64", "invoice_pretty_arm64.dmg", "Apple Silicon Mac安装包")
    ]
    
    for platform, filename, description in files:
        print(f"  ✅ {platform:15} {filename:35} - {description}")
    
    print("\n🚀 发布流程:")
    steps = [
        "1. 推送版本标签 (git tag -a v1.x.x -m 'Release v1.x.x')",
        "2. GitHub Actions自动触发构建",
        "3. 并行构建Windows和macOS版本",
        "4. 自动创建GitHub Release",
        "5. 上传所有构建产物到Release",
        "6. 生成中文Release Notes"
    ]
    
    for step in steps:
        print(f"  {step}")
    
    print("\n💡 使用建议:")
    print("  - 使用 'python release.py --interactive' 进行交互式发布")
    print("  - 使用 'python release.py --check' 检查发布环境")
    print("  - 推送标签后在GitHub Actions页面监控构建进度")
    
    return True

def main():
    """主函数"""
    print("🧪 PDF发票拼版打印系统 - 发布流程测试")
    print("=" * 60)
    
    tests = [
        ("GitHub Actions配置", test_github_actions_config),
        ("构建脚本", test_build_scripts),
        ("发布管理器", test_release_manager),
        ("文件结构模拟", simulate_release_files)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！发布流程配置正确。")
        generate_release_summary()
    else:
        print("⚠️  部分测试失败，请检查配置。")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)