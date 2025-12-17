#!/usr/bin/env python3
"""
PDF发票拼版打印系统启动脚本
解决包导入问题的包装器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 设置包名以支持相对导入
if __name__ == '__main__':
    # 导入并运行main模块
    import main
    main.main()