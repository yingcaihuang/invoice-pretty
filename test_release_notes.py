#!/usr/bin/env python3
"""
测试Release Notes格式和截图链接
"""

import re
from pathlib import Path

def test_release_notes():
    """测试Release Notes配置"""
    print("🧪 测试GitHub Actions Release Notes配置")
    print("=" * 60)
    
    workflow_file = Path('.github/workflows/build-and-release.yml')
    if not workflow_file.exists():
        print("❌ 未找到GitHub Actions工作流文件")
        return False
    
    content = workflow_file.read_text(encoding='utf-8')
    
    # 检查Release Notes部分
    release_notes_section = re.search(r'cat > release_notes\.md << \'EOF\'(.*?)EOF', content, re.DOTALL)
    if not release_notes_section:
        print("❌ 未找到Release Notes配置")
        return False
    
    release_notes_content = release_notes_section.group(1)
    print("✅ 找到Release Notes配置")
    
    # 检查截图链接
    screenshot_patterns = [
        r'!\[.*?\]\(https://raw\.githubusercontent\.com/yingcaihuang/invoice-pretty/main/img/assets/img1\.png\)',
        r'!\[.*?\]\(https://raw\.githubusercontent\.com/yingcaihuang/invoice-pretty/main/img/assets/img2\.png\)'
    ]
    
    print("\n📸 检查截图链接:")
    for i, pattern in enumerate(screenshot_patterns, 1):
        if re.search(pattern, release_notes_content):
            print(f"  ✅ 截图{i}链接配置正确")
        else:
            print(f"  ❌ 截图{i}链接缺失")
            return False
    
    # 检查必要的部分
    required_sections = [
        "界面预览",
        "下载说明", 
        "主要功能",
        "系统要求",
        "使用方法",
        "技术特性",
        "功能展示"
    ]
    
    print("\n📋 检查Release Notes部分:")
    for section in required_sections:
        if section in release_notes_content:
            print(f"  ✅ {section}")
        else:
            print(f"  ❌ 缺少: {section}")
            return False
    
    # 检查文件名
    expected_files = [
        'invoice_pretty.exe',
        'invoice_pretty_portable.zip',
        'invoice_pretty_intel.dmg',
        'invoice_pretty_arm64.dmg'
    ]
    
    print("\n📦 检查文件名:")
    for filename in expected_files:
        if filename in release_notes_content:
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ 缺少: {filename}")
            return False
    
    return True

def preview_release_notes():
    """预览Release Notes内容"""
    print("\n" + "="*60)
    print("📋 Release Notes 预览")
    print("="*60)
    
    workflow_file = Path('.github/workflows/build-and-release.yml')
    content = workflow_file.read_text(encoding='utf-8')
    
    # 提取Release Notes内容
    release_notes_section = re.search(r'cat > release_notes\.md << \'EOF\'(.*?)EOF', content, re.DOTALL)
    if release_notes_section:
        release_notes = release_notes_section.group(1).strip()
        
        # 替换变量为示例值
        release_notes = release_notes.replace('${{ steps.get_version.outputs.version }}', 'v1.1.0')
        
        print(release_notes)
    else:
        print("❌ 无法提取Release Notes内容")

def check_image_accessibility():
    """检查图片文件的可访问性"""
    print("\n" + "="*60)
    print("🖼️ 检查图片文件")
    print("="*60)
    
    img_dir = Path('img/assets')
    if not img_dir.exists():
        print("❌ img/assets目录不存在")
        return False
    
    required_images = ['img1.png', 'img2.png']
    
    for img_name in required_images:
        img_path = img_dir / img_name
        if img_path.exists():
            size_kb = img_path.stat().st_size / 1024
            print(f"  ✅ {img_name} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ 缺少: {img_name}")
            return False
    
    print("\n📍 GitHub Raw链接:")
    base_url = "https://raw.githubusercontent.com/yingcaihuang/invoice-pretty/main/img/assets"
    for img_name in required_images:
        print(f"  🔗 {base_url}/{img_name}")
    
    return True

def main():
    """主函数"""
    print("🧪 PDF发票拼版打印系统 - Release Notes测试")
    print("="*60)
    
    tests = [
        ("Release Notes配置", test_release_notes),
        ("图片文件检查", check_image_accessibility)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        if not test_func():
            print(f"\n❌ {test_name} - 失败")
            all_passed = False
        else:
            print(f"\n✅ {test_name} - 通过")
    
    if all_passed:
        preview_release_notes()
        print("\n🎉 所有测试通过！Release Notes配置正确。")
        print("\n💡 提示:")
        print("  - 推送版本标签后，Release页面将显示项目截图")
        print("  - 截图使用GitHub Raw链接，确保在Release中正确显示")
        print("  - Release Notes包含完整的功能介绍和使用说明")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)