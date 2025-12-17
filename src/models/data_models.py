"""
核心数据模型定义
定义系统中使用的主要数据结构
"""

from dataclasses import dataclass
from typing import Any, List, Tuple, Optional
from PIL import Image


@dataclass
class PDFDocument:
    """PDF文档数据模型"""
    file_path: str
    page_count: int
    dimensions: Tuple[float, float]  # (width, height) in points
    content: Any  # PyMuPDF document object


@dataclass
class LayoutConfig:
    """布局配置数据模型"""
    page_width: float = 210.0  # A4 width in mm
    page_height: float = 297.0  # A4 height in mm
    columns: int = 2
    rows: int = 4
    margin: float = 10.0  # margin in mm
    spacing: float = 5.0  # spacing between invoices in mm
    
    @property
    def total_slots(self) -> int:
        """计算总的发票位置数量"""
        return self.columns * self.rows
    
    @property
    def cell_width(self) -> float:
        """计算每个单元格的宽度"""
        available_width = self.page_width - 2 * self.margin - (self.columns - 1) * self.spacing
        return available_width / self.columns
    
    @property
    def cell_height(self) -> float:
        """计算每个单元格的高度"""
        available_height = self.page_height - 2 * self.margin - (self.rows - 1) * self.spacing
        return available_height / self.rows


@dataclass
class PositionedInvoice:
    """定位后的发票数据模型"""
    image: Image.Image
    x: float  # position in mm
    y: float  # position in mm
    width: float  # size in mm
    height: float  # size in mm
    page_number: int  # which output page this invoice belongs to
    original_file_path: str  # source file path for tracking


@dataclass
class ProcessResult:
    """处理结果数据模型"""
    success: bool
    output_file: str
    processed_count: int
    total_pages: int
    errors: List[str]
    skipped_files: List[str] = None
    
    def __post_init__(self):
        if self.skipped_files is None:
            self.skipped_files = []
    
    @property
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.processed_count == 0:
            return 0.0
        return (self.processed_count - len(self.skipped_files)) / self.processed_count