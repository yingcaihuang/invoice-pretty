#!/usr/bin/env python3
"""
验证项目设置脚本
检查所有核心组件是否正确安装和配置
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_imports():
    """验证所有核心模块导入"""
    try:
        # 验证外部依赖
        import fitz
        print("✓ PyMuPDF 导入成功")
        
        from PIL import Image
        print("✓ Pillow 导入成功")
        
        import hypothesis
        print("✓ Hypothesis 导入成功")
        
        import pytest
        print("✓ Pytest 导入成功")
        
        # 验证核心数据模型
        from src.models.data_models import PDFDocument, LayoutConfig, PositionedInvoice, ProcessResult
        print("✓ 核心数据模型导入成功")
        
        # 验证接口定义
        from src.interfaces.base_interfaces import (
            IFileHandler, IPDFReader, ILayoutManager, 
            IPDFProcessor, IUIController
        )
        print("✓ 基础接口导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def verify_data_models():
    """验证数据模型功能"""
    try:
        from src.models.data_models import LayoutConfig, ProcessResult
        
        # 测试LayoutConfig
        config = LayoutConfig()
        assert config.total_slots == 8
        assert config.cell_width > 0
        assert config.cell_height > 0
        print("✓ LayoutConfig 功能验证成功")
        
        # 测试ProcessResult
        result = ProcessResult(
            success=True,
            output_file="test.pdf",
            processed_count=5,
            total_pages=1,
            errors=[]
        )
        assert result.success_rate == 1.0
        assert not result.has_errors
        print("✓ ProcessResult 功能验证成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据模型验证失败: {e}")
        return False

def verify_project_structure():
    """验证项目结构"""
    required_dirs = [
        'src',
        'src/models',
        'src/interfaces', 
        'src/services',
        'src/ui',
        'tests'
    ]
    
    required_files = [
        'main.py',
        'requirements.txt',
        'setup.py',
        'README.md',
        'config.py',
        'src/models/data_models.py',
        'src/interfaces/base_interfaces.py',
        'tests/test_data_models.py'
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"✗ 缺少目录: {directory}")
            return False
        print(f"✓ 目录存在: {directory}")
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"✗ 缺少文件: {file_path}")
            return False
        print(f"✓ 文件存在: {file_path}")
    
    return True

def main():
    """主验证函数"""
    print("PDF发票拼版打印系统 - 项目设置验证")
    print("=" * 50)
    
    success = True
    
    print("\n1. 验证项目结构...")
    if not verify_project_structure():
        success = False
    
    print("\n2. 验证模块导入...")
    if not verify_imports():
        success = False
    
    print("\n3. 验证数据模型功能...")
    if not verify_data_models():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有验证通过！项目设置成功。")
        print("\n下一步:")
        print("- 运行测试: python -m pytest tests/ -v")
        print("- 启动应用: python main.py")
    else:
        print("✗ 验证失败，请检查上述错误。")
        sys.exit(1)

if __name__ == "__main__":
    main()