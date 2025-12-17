#!/usr/bin/env python3
"""
跨平台兼容性测试脚本
测试系统在不同平台上的兼容性
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path

def test_python_version():
    """测试Python版本兼容性"""
    print("测试Python版本兼容性...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python版本不兼容: {version.major}.{version.minor}")
        return False
    
    print(f"✓ Python版本兼容: {version.major}.{version.minor}.{version.micro}")
    return True

def test_module_imports():
    """测试关键模块导入"""
    print("测试模块导入...")
    
    modules = [
        ('os', '标准库'),
        ('sys', '标准库'),
        ('pathlib', '标准库'),
        ('tkinter', 'GUI库'),
        ('json', '标准库'),
        ('logging', '标准库'),
    ]
    
    optional_modules = [
        ('fitz', 'PyMuPDF'),
        ('PIL', 'Pillow'),
        ('hypothesis', 'Hypothesis'),
        ('pytest', 'pytest'),
    ]
    
    all_ok = True
    
    # 测试必需模块
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {description} ({module_name})")
        except ImportError:
            print(f"✗ {description} ({module_name}) - 必需模块缺失")
            all_ok = False
    
    # 测试可选模块
    for module_name, description in optional_modules:
        try:
            __import__(module_name)
            print(f"✓ {description} ({module_name})")
        except ImportError:
            print(f"⚠ {description} ({module_name}) - 可选模块缺失")
    
    return all_ok

def test_file_operations():
    """测试文件操作兼容性"""
    print("测试文件操作兼容性...")
    
    try:
        # 测试临时文件创建
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            test_content = "测试内容\nTest content\n"
            f.write(test_content)
            temp_path = f.name
        
        # 测试文件读取
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content != test_content:
                print("✗ 文件读写内容不匹配")
                return False
        
        # 测试文件删除
        os.unlink(temp_path)
        
        print("✓ 文件操作兼容")
        return True
        
    except Exception as e:
        print(f"✗ 文件操作失败: {e}")
        return False

def test_path_operations():
    """测试路径操作兼容性"""
    print("测试路径操作兼容性...")
    
    try:
        # 测试Path对象
        current_dir = Path.cwd()
        parent_dir = current_dir.parent
        
        # 测试路径拼接
        test_path = current_dir / "test_file.txt"
        
        # 测试路径字符串转换
        path_str = str(test_path)
        
        # 测试路径存在性检查
        exists = current_dir.exists()
        
        if not exists:
            print("✗ 当前目录不存在（不应该发生）")
            return False
        
        print("✓ 路径操作兼容")
        return True
        
    except Exception as e:
        print(f"✗ 路径操作失败: {e}")
        return False

def test_encoding():
    """测试字符编码兼容性"""
    print("测试字符编码兼容性...")
    
    try:
        # 测试中文字符处理
        chinese_text = "PDF发票拼版打印系统"
        
        # 测试编码/解码
        encoded = chinese_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        
        if decoded != chinese_text:
            print("✗ UTF-8编码/解码失败")
            return False
        
        # 测试文件名中的中文字符
        with tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False, 
            encoding='utf-8',
            prefix='测试_',
            suffix='.txt'
        ) as f:
            f.write(chinese_text)
            temp_path = f.name
        
        # 读取并验证
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content != chinese_text:
                print("✗ 中文文件内容读写失败")
                return False
        
        # 清理
        os.unlink(temp_path)
        
        print("✓ 字符编码兼容")
        return True
        
    except Exception as e:
        print(f"✗ 字符编码测试失败: {e}")
        return False

def test_gui_availability():
    """测试GUI可用性"""
    print("测试GUI可用性...")
    
    try:
        import tkinter as tk
        
        # 尝试创建根窗口（但不显示）
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 测试基本组件
        label = tk.Label(root, text="测试")
        button = tk.Button(root, text="测试按钮")
        
        # 清理
        root.destroy()
        
        print("✓ GUI可用")
        return True
        
    except Exception as e:
        print(f"✗ GUI不可用: {e}")
        print("  提示: 在无头环境中GUI功能不可用")
        return False

def test_subprocess():
    """测试子进程功能"""
    print("测试子进程功能...")
    
    try:
        # 测试简单命令
        result = subprocess.run(
            [sys.executable, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("✗ 子进程执行失败")
            return False
        
        print("✓ 子进程功能正常")
        return True
        
    except Exception as e:
        print(f"✗ 子进程测试失败: {e}")
        return False

def get_system_info():
    """获取系统信息"""
    print("系统信息:")
    print(f"  操作系统: {platform.system()} {platform.release()}")
    print(f"  架构: {platform.machine()}")
    print(f"  Python版本: {platform.python_version()}")
    print(f"  Python实现: {platform.python_implementation()}")
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"  虚拟环境: 是")
    else:
        print(f"  虚拟环境: 否")

def main():
    """主函数"""
    print("PDF发票拼版打印系统 - 跨平台兼容性测试")
    print("=" * 60)
    
    get_system_info()
    print()
    
    tests = [
        ("Python版本", test_python_version),
        ("模块导入", test_module_imports),
        ("文件操作", test_file_operations),
        ("路径操作", test_path_operations),
        ("字符编码", test_encoding),
        ("GUI可用性", test_gui_availability),
        ("子进程功能", test_subprocess),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}测试:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有兼容性测试通过")
        return 0
    else:
        print("✗ 部分兼容性测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())