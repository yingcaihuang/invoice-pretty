"""
测试配置文件
设置测试环境的路径和配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录和src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))