#!/usr/bin/env python3
"""
验证发布配置脚本
确保GitHub Actions能正确上传EXE和DMG文件到Release
"""

import re
from pathlib import Path

def verify_github_actions_config():
    """验证GitHub Actions配置"""
    print("🔍 验证GitHub Actions发布配置...")
    
    workflow_file = Path('.github/workflows/build-and-release.yml')
    if not workflow_file.exists():
        print("❌ 未找到GitHub Actions工作流文件")
        return False
    
    content = workflow_file.read_text(encoding='utf-8')
    
    # 检查必要的作业
    required_jobs = [
        'build-windows',
        'build-macos-intel', 
        'build-macos-arm',
        'create-release'
    ]
    
    for job in required_jobs:
        if f'{job}:' in content:
            print(f"✅ 找到作业: {job}")
        else:
            print(f"❌ 缺少作业: {job}")
            return False
    
    # 检查文件上传配置
    files_section = re.search(r'files:\s*\|(.*?)fail_on_unmatched_files:', content, re.DOTALL)
    if not files_section:
        print("❌ 未找到文件上传配置")
        return False
    
    files_content = files_section.group(1)
    expected_files = [
        'invoice_pretty.exe',
        'invoice_pretty_portable.zip',
        'invoice_pretty_intel.dmg', 
        'invoice_pretty_arm64.dmg'
    ]
    
    print("\n📦 检查上传文件配置:")
    all_files_found = True
    for expected_file in expected_files:
        if expected_file in files_content:
            print(f"  ✅ {expected_file}")
        else:
            print(f"  ❌ 缺少: {expected_file}")
            all_files_found = False
    
    if not all_files_found:
        return False
    
    # 检查构建步骤
    print("\n🔨 检查构建步骤:")
    
    # Windows构建
    if 'python build_windows.py --exe-only' in content:
        print("  ✅ Windows EXE构建")
    else:
        print("  ❌ 缺少Windows EXE构建")
        return False
    
    if 'python build_windows.py --portable-only' in content:
        print("  ✅ Windows便携版构建")
    else:
        print("  ❌ 缺少Windows便携版构建")
        return False
    
    # macOS构建
    if 'python build_import_fixed.py' in content:
        print("  ✅ macOS构建 (导入修复版)")
    else:
        print("  ❌ 缺少macOS构建")
        return False
    
    # 检查文件重命名
    if 'invoice_pretty_intel.dmg' in content and 'invoice_pretty_arm64.dmg' in content:
        print("  ✅ macOS文件重命名配置")
    else:
        print("  ❌ 缺少macOS文件重命名配置")
        return False
    
    print("\n✅ GitHub Actions配置验证通过！")
    return True

def verify_build_scripts():
    """验证构建脚本"""
    print("\n🔧 验证构建脚本...")
    
    # 检查Windows构建脚本
    windows_script = Path('build_windows.py')
    if not windows_script.exists():
        print("❌ 缺少Windows构建脚本")
        return False
    
    content = windows_script.read_text(encoding='utf-8')
    
    # 检查关键函数
    required_functions = [
        'clean_build_files',
        'build_windows_exe', 
        'create_portable_package'
    ]
    
    for func in required_functions:
        if f'def {func}(' in content:
            print(f"  ✅ Windows脚本包含: {func}")
        else:
            print(f"  ❌ Windows脚本缺少: {func}")
            return False
    
    # 检查返回值修复
    if 'return True' in content and 'except Exception as e:' in content:
        print("  ✅ Windows脚本包含错误处理和返回值")
    else:
        print("  ❌ Windows脚本缺少错误处理")
        return False
    
    # 检查macOS构建脚本
    macos_script = Path('build_import_fixed.py')
    if not macos_script.exists():
        print("❌ 缺少macOS构建脚本")
        return False
    
    print("  ✅ macOS构建脚本存在")
    
    print("✅ 构建脚本验证通过！")
    return True

def verify_release_manager():
    """验证发布管理器"""
    print("\n📋 验证发布管理器...")
    
    release_script = Path('release.py')
    if not release_script.exists():
        print("❌ 缺少发布管理脚本")
        return False
    
    content = release_script.read_text(encoding='utf-8')
    
    # 检查关键功能
    required_methods = [
        'check_environment',
        'create_tag',
        'interactive_release'
    ]
    
    for method in required_methods:
        if f'def {method}(' in content:
            print(f"  ✅ 发布管理器包含: {method}")
        else:
            print(f"  ❌ 发布管理器缺少: {method}")
            return False
    
    print("✅ 发布管理器验证通过！")
    return True

def show_release_summary():
    """显示发布流程总结"""
    print("\n" + "="*60)
    print("🎉 发布配置验证完成！")
    print("="*60)
    
    print("\n📦 自动发布的文件:")
    files = [
        ("Windows EXE", "invoice_pretty.exe"),
        ("Windows 便携版", "invoice_pretty_portable.zip"),
        ("macOS Intel", "invoice_pretty_intel.dmg"),
        ("macOS ARM64", "invoice_pretty_arm64.dmg")
    ]
    
    for platform, filename in files:
        print(f"  ✅ {platform:15} → {filename}")
    
    print("\n🚀 发布命令:")
    print("  # 交互式发布 (推荐)")
    print("  python release.py --interactive")
    print()
    print("  # 手动发布")
    print("  git tag -a v1.1.0 -m 'Release v1.1.0'")
    print("  git push origin v1.1.0")
    
    print("\n📍 发布后检查:")
    print("  1. 访问GitHub仓库的Actions页面查看构建进度")
    print("  2. 构建完成后检查Releases页面")
    print("  3. 确认所有4个文件都已上传")
    print("  4. 验证Release Notes内容正确")
    
    print("\n💡 提示:")
    print("  - 构建时间约15-20分钟 (并行构建)")
    print("  - 推送标签后会自动触发构建")
    print("  - 可在GitHub Actions页面监控进度")

def main():
    """主函数"""
    print("🧪 PDF发票拼版打印系统 - 发布配置验证")
    print("="*60)
    
    checks = [
        ("GitHub Actions配置", verify_github_actions_config),
        ("构建脚本", verify_build_scripts),
        ("发布管理器", verify_release_manager)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        if not check_func():
            print(f"\n❌ {check_name}验证失败")
            all_passed = False
    
    if all_passed:
        show_release_summary()
        print("\n🎯 结论: 发布配置完全正确，可以开始发布！")
    else:
        print("\n⚠️  发现配置问题，请修复后重试。")
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)