#!/usr/bin/env python3
"""
检查GitHub Actions工作流文件中的Unicode字符
避免Windows编码问题
"""

import re
from pathlib import Path

def check_unicode_characters():
    """检查工作流文件中的Unicode字符"""
    print("🔍 检查GitHub Actions工作流中的Unicode字符")
    print("=" * 60)
    
    workflow_dir = Path('.github/workflows')
    if not workflow_dir.exists():
        print("❌ .github/workflows目录不存在")
        return False
    
    workflow_files = list(workflow_dir.glob('*.yml'))
    if not workflow_files:
        print("❌ 未找到工作流文件")
        return False
    
    issues_found = False
    
    for workflow_file in workflow_files:
        print(f"\n📄 检查文件: {workflow_file.name}")
        
        try:
            content = workflow_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # 检查可能有问题的Unicode字符
            problematic_chars = {
                '✅': '[OK]',
                '❌': '[ERROR]', 
                '⚠️': '[WARN]',
                '🔍': '[INFO]',
                '📦': '[INFO]',
                '🚀': '',
                '🎉': '',
                '💡': '[INFO]',
                '🔧': '[INFO]',
                '📋': '[INFO]',
                '📸': '[INFO]',
                '🖼️': '[INFO]'
            }
            
            file_issues = []
            
            for line_num, line in enumerate(lines, 1):
                for char, replacement in problematic_chars.items():
                    if char in line:
                        file_issues.append({
                            'line': line_num,
                            'char': char,
                            'replacement': replacement,
                            'content': line.strip()
                        })
            
            if file_issues:
                issues_found = True
                print(f"  ⚠️  发现 {len(file_issues)} 个潜在问题:")
                
                for issue in file_issues:
                    print(f"    行 {issue['line']}: '{issue['char']}' -> '{issue['replacement']}'")
                    print(f"      内容: {issue['content'][:80]}...")
            else:
                print("  ✅ 未发现Unicode字符问题")
                
        except Exception as e:
            print(f"  ❌ 读取文件失败: {e}")
            issues_found = True
    
    return not issues_found

def suggest_fixes():
    """建议修复方案"""
    print("\n" + "=" * 60)
    print("🔧 修复建议")
    print("=" * 60)
    
    print("\n📋 常见问题字符替换:")
    replacements = [
        ("✅", "[OK]", "成功标记"),
        ("❌", "[ERROR]", "错误标记"), 
        ("⚠️", "[WARN]", "警告标记"),
        ("🔍", "[INFO]", "信息标记"),
        ("📦", "[INFO]", "包/文件标记"),
        ("🚀", "移除", "装饰性emoji"),
        ("🎉", "移除", "庆祝emoji"),
        ("💡", "[INFO]", "提示标记")
    ]
    
    for original, replacement, description in replacements:
        print(f"  {original} → {replacement:8} ({description})")
    
    print("\n💡 修复原则:")
    print("  1. 将功能性emoji替换为ASCII标记")
    print("  2. 移除装饰性emoji")
    print("  3. 保持信息的可读性")
    print("  4. 确保Windows兼容性")
    
    print("\n🔧 自动修复命令:")
    print("  python check_unicode_in_workflows.py --fix")

def auto_fix_workflows():
    """自动修复工作流文件中的Unicode字符"""
    print("🔧 自动修复GitHub Actions工作流文件")
    print("=" * 60)
    
    workflow_dir = Path('.github/workflows')
    workflow_files = list(workflow_dir.glob('*.yml'))
    
    # 替换映射
    replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]', 
        '⚠️': '[WARN]',
        '🔍': '[INFO]',
        '📦': '[INFO]',
        '🚀': '',
        '🎉': '',
        '💡': '[INFO]',
        '🔧': '[INFO]',
        '📋': '[INFO]',
        '📸': '[INFO]',
        '🖼️': '[INFO]'
    }
    
    fixed_files = 0
    
    for workflow_file in workflow_files:
        try:
            content = workflow_file.read_text(encoding='utf-8')
            original_content = content
            
            # 应用替换
            for char, replacement in replacements.items():
                content = content.replace(char, replacement)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                workflow_file.write_text(content, encoding='utf-8')
                print(f"✅ 修复文件: {workflow_file.name}")
                fixed_files += 1
            else:
                print(f"✅ 文件无需修复: {workflow_file.name}")
                
        except Exception as e:
            print(f"❌ 修复文件失败 {workflow_file.name}: {e}")
    
    print(f"\n🎉 修复完成！共修复 {fixed_files} 个文件")
    return fixed_files > 0

def main():
    """主函数"""
    import sys
    
    print("🧪 GitHub Actions Unicode字符检查工具")
    print("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        success = auto_fix_workflows()
        print("\n🔍 修复后重新检查...")
        success = check_unicode_characters()
    else:
        success = check_unicode_characters()
        if not success:
            suggest_fixes()
    
    if success:
        print("\n🎉 所有工作流文件都兼容Windows编码！")
    else:
        print("\n⚠️  发现编码兼容性问题，建议修复。")
    
    return success

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)