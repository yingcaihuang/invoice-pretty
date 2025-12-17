"""
PDF发票拼版打印系统配置管理
提供配置加载、验证和管理功能
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 默认配置
DEFAULT_CONFIG = {
    # 布局配置
    "layout": {
        "page_width": 210.0,  # A4宽度(mm)
        "page_height": 297.0,  # A4高度(mm)
        "columns": 2,         # 列数
        "rows": 4,           # 行数
        "margin": 10.0,      # 页边距(mm)
        "spacing": 5.0,      # 发票间距(mm)
    },
    
    # 输出配置
    "output": {
        "dpi": 300,          # 输出DPI
        "quality": 95,       # JPEG质量(如果需要)
        "format": "PDF",     # 输出格式
    },
    
    # 文件处理配置
    "file_handling": {
        "max_file_size_mb": 50,      # 最大文件大小(MB)
        "supported_extensions": [".pdf"],  # 支持的文件扩展名
        "batch_size": 100,           # 批处理大小
    },
    
    # UI配置
    "ui": {
        "window_width": 800,
        "window_height": 600,
        "theme": "default",
    },
    
    # 日志配置
    "logging": {
        "level": "INFO",
        "file": "pdf_invoice_layout.log",
        "max_size_mb": 10,
        "backup_count": 3,
    }
}

@dataclass
class ValidationError:
    """配置验证错误"""
    field: str
    value: Any
    message: str

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or PROJECT_ROOT / "config.json"
        self.config = DEFAULT_CONFIG.copy()
        self.validation_errors = []
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(self.config, user_config)
                    logging.info(f"已加载配置文件: {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"配置文件加载失败: {e}, 使用默认配置")
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
        # 验证配置
        if not self.validate_config():
            raise ValueError(f"配置验证失败: {self.validation_errors}")
            
        return self.config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置到文件"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            logging.info(f"配置已保存到: {self.config_file}")
            return True
        except IOError as e:
            logging.error(f"配置保存失败: {e}")
            return False
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        self.validation_errors.clear()
        
        # 验证布局配置
        layout = self.config.get("layout", {})
        self._validate_positive_number("layout.page_width", layout.get("page_width"))
        self._validate_positive_number("layout.page_height", layout.get("page_height"))
        self._validate_positive_integer("layout.columns", layout.get("columns"))
        self._validate_positive_integer("layout.rows", layout.get("rows"))
        self._validate_non_negative_number("layout.margin", layout.get("margin"))
        self._validate_non_negative_number("layout.spacing", layout.get("spacing"))
        
        # 验证输出配置
        output = self.config.get("output", {})
        self._validate_range("output.dpi", output.get("dpi"), 72, 1200)
        self._validate_range("output.quality", output.get("quality"), 1, 100)
        
        # 验证文件处理配置
        file_handling = self.config.get("file_handling", {})
        self._validate_positive_number("file_handling.max_file_size_mb", file_handling.get("max_file_size_mb"))
        self._validate_positive_integer("file_handling.batch_size", file_handling.get("batch_size"))
        
        # 验证UI配置
        ui = self.config.get("ui", {})
        self._validate_positive_integer("ui.window_width", ui.get("window_width"))
        self._validate_positive_integer("ui.window_height", ui.get("window_height"))
        
        return len(self.validation_errors) == 0
    
    def get_config_value(self, key_path: str, default_value=None):
        """
        获取配置值
        key_path格式: "layout.page_width"
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default_value
        return value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            "PDF_INVOICE_LAYOUT_PAGE_WIDTH": "layout.page_width",
            "PDF_INVOICE_LAYOUT_PAGE_HEIGHT": "layout.page_height",
            "PDF_INVOICE_LAYOUT_COLUMNS": "layout.columns",
            "PDF_INVOICE_LAYOUT_ROWS": "layout.rows",
            "PDF_INVOICE_OUTPUT_DPI": "output.dpi",
            "PDF_INVOICE_UI_WINDOW_WIDTH": "ui.window_width",
            "PDF_INVOICE_UI_WINDOW_HEIGHT": "ui.window_height",
        }
        
        for env_key, config_path in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                try:
                    # 尝试转换类型
                    if '.' in env_value:
                        converted_value = float(env_value)
                    else:
                        converted_value = int(env_value)
                    
                    # 设置配置值
                    keys = config_path.split('.')
                    target = self.config
                    for key in keys[:-1]:
                        target = target.setdefault(key, {})
                    target[keys[-1]] = converted_value
                    
                except ValueError:
                    logging.warning(f"环境变量 {env_key} 值无效: {env_value}")
    
    def _validate_positive_number(self, field: str, value: Any):
        """验证正数"""
        if not isinstance(value, (int, float)) or value <= 0:
            self.validation_errors.append(
                ValidationError(field, value, "必须是正数")
            )
    
    def _validate_positive_integer(self, field: str, value: Any):
        """验证正整数"""
        if not isinstance(value, int) or value <= 0:
            self.validation_errors.append(
                ValidationError(field, value, "必须是正整数")
            )
    
    def _validate_non_negative_number(self, field: str, value: Any):
        """验证非负数"""
        if not isinstance(value, (int, float)) or value < 0:
            self.validation_errors.append(
                ValidationError(field, value, "必须是非负数")
            )
    
    def _validate_range(self, field: str, value: Any, min_val: Union[int, float], max_val: Union[int, float]):
        """验证数值范围"""
        if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
            self.validation_errors.append(
                ValidationError(field, value, f"必须在 {min_val} 到 {max_val} 之间")
            )

# 全局配置管理器实例
config_manager = ConfigManager()

# 向后兼容的函数
def get_config_value(key_path: str, default_value=None):
    """
    获取配置值，支持环境变量覆盖
    key_path格式: "layout.page_width"
    """
    return config_manager.get_config_value(key_path, default_value)