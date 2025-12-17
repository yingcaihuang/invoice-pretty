#!/usr/bin/env python3
"""
配置验证工具
用于验证配置文件的有效性
"""

import sys
import argparse
from pathlib import Path
from config import ConfigManager

def main():
    parser = argparse.ArgumentParser(description="验证PDF发票拼版系统配置文件")
    parser.add_argument(
        "config_file", 
        nargs="?", 
        default="config.json",
        help="配置文件路径 (默认: config.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config_file)
    
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        return 1
    
    try:
        # 创建配置管理器并加载配置
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        print(f"✓ 配置文件验证成功: {config_path}")
        
        if args.verbose:
            print("\n配置内容:")
            print_config(config, indent=0)
            
    except ValueError as e:
        print(f"✗ 配置验证失败: {e}")
        
        if hasattr(config_manager, 'validation_errors'):
            print("\n详细错误:")
            for error in config_manager.validation_errors:
                print(f"  - {error.field}: {error.message} (当前值: {error.value})")
        
        return 1
    
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return 1
    
    return 0

def print_config(config, indent=0):
    """递归打印配置内容"""
    spaces = "  " * indent
    
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"{spaces}{key}:")
            print_config(value, indent + 1)
        else:
            print(f"{spaces}{key}: {value}")

if __name__ == "__main__":
    sys.exit(main())