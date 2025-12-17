#!/usr/bin/env python3
"""
PDF发票拼版打印系统主入口
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入配置管理
from config import ConfigManager

def setup_logging(level=logging.INFO, config=None):
    """设置日志配置"""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # 如果有配置，添加文件日志处理器
    if config:
        log_config = config.get('logging', {})
        log_file = log_config.get('file', 'pdf_invoice_layout.log')
        
        try:
            from logging.handlers import RotatingFileHandler
            max_bytes = int(log_config.get('max_size_mb', 10)) * 1024 * 1024
            backup_count = int(log_config.get('backup_count', 3))
            
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding='utf-8'
            )
            handlers.append(file_handler)
        except Exception as e:
            print(f"文件日志设置失败: {e}")
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # 强制重新配置
    )

def check_gui_availability():
    """检查GUI是否可用"""
    try:
        import tkinter
        import _tkinter
        return True
    except ImportError:
        return False

def run_cli_interface(config=None):
    """运行命令行界面"""
    print("PDF发票拼版打印系统 - 命令行模式")
    print("=" * 50)
    print("由于包导入问题，请使用简化命令行版本:")
    print("python cli_main.py <输入路径> -o <输出路径>")
    print("例如: python cli_main.py test_files -o output.pdf")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='PDF发票拼版打印系统')
    parser.add_argument('--cli', action='store_true', help='强制使用命令行界面')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', '-c', help='指定配置文件路径')
    parser.add_argument('input', nargs='?', help='输入PDF文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    args = parser.parse_args()
    
    # 加载配置
    try:
        config_file = Path(args.config) if args.config else None
        config_manager = ConfigManager(config_file)
        config = config_manager.load_config()
        
        # 从配置中获取日志级别
        log_level_str = config.get('logging', {}).get('level', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        # 如果指定了debug参数，覆盖配置文件中的日志级别
        if args.debug:
            log_level = logging.DEBUG
            
        setup_logging(log_level, config)
        
    except Exception as e:
        print(f"配置加载失败: {e}")
        print("使用默认配置继续运行...")
        setup_logging(logging.DEBUG if args.debug else logging.INFO)
        config = None
    
    logger = logging.getLogger(__name__)
    logger.info("PDF发票拼版打印系统启动")
    
    # 检查是否有命令行参数或强制CLI模式
    use_cli = args.cli or args.input is not None
    
    # 如果没有强制CLI且GUI可用，尝试启动GUI
    if not use_cli and check_gui_availability():
        try:
            logger.info("启动图形用户界面...")
            # 尝试不同的导入路径以兼容不同的运行环境
            gui_controller = None
            
            # 方法1: 尝试相对导入
            try:
                from ui.gui_controller import GUIController
                gui_controller = GUIController
                logger.debug("使用相对导入成功")
            except ImportError as e1:
                logger.debug(f"相对导入失败: {e1}")
                
                # 方法2: 尝试src路径导入
                try:
                    from src.ui.gui_controller import GUIController
                    gui_controller = GUIController
                    logger.debug("使用src路径导入成功")
                except ImportError as e2:
                    logger.debug(f"src路径导入失败: {e2}")
                    
                    # 方法3: 尝试直接导入模块
                    try:
                        import sys
                        import importlib.util
                        
                        # 查找gui_controller模块
                        gui_path = None
                        for path in sys.path:
                            potential_paths = [
                                os.path.join(path, 'ui', 'gui_controller.py'),
                                os.path.join(path, 'src', 'ui', 'gui_controller.py')
                            ]
                            for p in potential_paths:
                                if os.path.exists(p):
                                    gui_path = p
                                    break
                            if gui_path:
                                break
                        
                        if gui_path:
                            spec = importlib.util.spec_from_file_location("gui_controller", gui_path)
                            gui_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(gui_module)
                            gui_controller = gui_module.GUIController
                            logger.debug("使用直接模块导入成功")
                        else:
                            raise ImportError("无法找到gui_controller模块")
                            
                    except Exception as e3:
                        logger.error(f"所有导入方法都失败: {e1}, {e2}, {e3}")
                        raise ImportError("无法导入GUI模块")
            
            if gui_controller:
                app = gui_controller()
                app.run()
                return
            else:
                raise ImportError("GUI控制器未成功导入")
            
        except Exception as e:
            logger.error(f"GUI启动失败: {str(e)}")
            print(f"GUI启动失败: {str(e)}")
            print("切换到命令行模式...")
            use_cli = True
    
    # 使用命令行界面
    if use_cli:
        logger.info("启动命令行界面...")
        if args.input:
            # 直接处理命令行参数
            # 由于包导入问题，重定向到简化命令行版本
            print("由于包导入问题，重定向到简化命令行版本...")
            
            # 构建cli_main.py的命令
            cli_args = ['python', 'cli_main.py', args.input]
            if args.output:
                cli_args.extend(['-o', args.output])
            if args.debug:
                cli_args.append('--debug')
            
            print(f"执行: {' '.join(cli_args)}")
            
            # 执行cli_main.py
            import subprocess
            result = subprocess.run(cli_args)
            sys.exit(result.returncode)
        else:
            # 交互式命令行界面
            run_cli_interface(config)
    else:
        # GUI不可用且没有命令行参数
        print("错误: GUI不可用 (tkinter未安装)")
        print("解决方案:")
        print("1. 安装tkinter支持:")
        print("   - macOS: brew install python-tk")
        print("   - Ubuntu: sudo apt-get install python3-tk")
        print("   - 或重新安装Python并包含tkinter支持")
        print("2. 使用命令行模式:")
        print("   python main.py --cli")
        print("   python main.py input.pdf -o output.pdf")
        print("3. 使用简化命令行版本:")
        print("   python cli_main.py input.pdf -o output.pdf")
        sys.exit(1)


if __name__ == "__main__":
    main()