"""
布局管理服务
实现发票拼版布局计算和位置分配逻辑
"""

import math
from typing import List, Tuple
from PIL import Image

from src.interfaces.base_interfaces import ILayoutManager
from src.models.data_models import LayoutConfig, PositionedInvoice


class LayoutManager(ILayoutManager):
    """布局管理器实现类"""
    
    def __init__(self):
        """初始化布局管理器"""
        self.default_config = LayoutConfig()
    
    def calculate_layout(self, invoice_count: int) -> LayoutConfig:
        """
        计算布局配置
        
        Args:
            invoice_count: 发票数量
            
        Returns:
            LayoutConfig: 布局配置对象
        """
        # 使用默认的2列4行配置
        return LayoutConfig(
            page_width=210.0,  # A4 width in mm
            page_height=297.0,  # A4 height in mm
            columns=2,
            rows=4,
            margin=10.0,
            spacing=5.0
        )
    
    def calculate_scale_factor(self, original_size: Tuple[float, float], target_size: Tuple[float, float]) -> float:
        """
        计算缩放因子，保持纵横比不变
        
        Args:
            original_size: 原始尺寸 (width, height)
            target_size: 目标尺寸 (width, height)
            
        Returns:
            float: 缩放因子
        """
        if original_size[0] <= 0 or original_size[1] <= 0:
            return 1.0
        
        if target_size[0] <= 0 or target_size[1] <= 0:
            return 1.0
        
        # 计算宽度和高度的缩放比例
        width_scale = target_size[0] / original_size[0]
        height_scale = target_size[1] / original_size[1]
        
        # 选择较小的缩放比例以保持纵横比
        scale_factor = min(width_scale, height_scale)
        
        return scale_factor
    
    def position_invoices(self, invoices: List[Image.Image], layout: LayoutConfig, file_paths: List[str]) -> List[PositionedInvoice]:
        """
        计算发票位置分配
        
        Args:
            invoices: 发票图像列表
            layout: 布局配置
            file_paths: 对应的文件路径列表
            
        Returns:
            List[PositionedInvoice]: 定位后的发票列表
        """
        positioned_invoices = []
        
        if not invoices:
            return positioned_invoices
        
        # 确保文件路径列表长度匹配
        if len(file_paths) != len(invoices):
            # 如果路径不够，用空字符串填充
            file_paths = file_paths + [''] * (len(invoices) - len(file_paths))
        
        # 计算每页的发票数量
        invoices_per_page = layout.total_slots  # 2 * 4 = 8
        total_pages = math.ceil(len(invoices) / invoices_per_page)
        
        for page_num in range(total_pages):
            # 计算当前页的发票范围
            start_idx = page_num * invoices_per_page
            end_idx = min(start_idx + invoices_per_page, len(invoices))
            page_invoices = invoices[start_idx:end_idx]
            page_file_paths = file_paths[start_idx:end_idx]
            
            # 为当前页的每张发票计算位置
            for i, (invoice_image, file_path) in enumerate(zip(page_invoices, page_file_paths)):
                # 计算网格位置 (从左上角开始，按行填充)
                row = i // layout.columns
                col = i % layout.columns
                
                # 计算目标单元格尺寸
                cell_width = layout.cell_width
                cell_height = layout.cell_height
                
                # 获取原始图像尺寸 (转换为mm，假设72 DPI)
                original_width_px, original_height_px = invoice_image.size
                # 将像素转换为mm (72 DPI = 72/25.4 pixels per mm)
                pixels_per_mm = 72 / 25.4
                original_width_mm = original_width_px / pixels_per_mm
                original_height_mm = original_height_px / pixels_per_mm
                
                # 计算缩放因子
                scale_factor = self.calculate_scale_factor(
                    (original_width_mm, original_height_mm),
                    (cell_width, cell_height)
                )
                
                # 计算缩放后的尺寸
                scaled_width = original_width_mm * scale_factor
                scaled_height = original_height_mm * scale_factor
                
                # 计算位置 (居中对齐)
                cell_x = layout.margin + col * (cell_width + layout.spacing)
                cell_y = layout.margin + row * (cell_height + layout.spacing)
                
                # 在单元格内居中
                x = cell_x + (cell_width - scaled_width) / 2
                y = cell_y + (cell_height - scaled_height) / 2
                
                # 创建定位发票对象
                positioned_invoice = PositionedInvoice(
                    image=invoice_image,
                    x=x,
                    y=y,
                    width=scaled_width,
                    height=scaled_height,
                    page_number=page_num,
                    original_file_path=file_path
                )
                
                positioned_invoices.append(positioned_invoice)
        
        return positioned_invoices
    
    def calculate_pages_needed(self, invoice_count: int) -> int:
        """
        计算需要的页面数量
        
        Args:
            invoice_count: 发票数量
            
        Returns:
            int: 需要的页面数量
        """
        if invoice_count <= 0:
            return 0
        
        layout = self.calculate_layout(invoice_count)
        return math.ceil(invoice_count / layout.total_slots)
    
    def get_invoice_positions_for_page(self, page_number: int, layout: LayoutConfig) -> List[Tuple[int, int]]:
        """
        获取指定页面的发票网格位置
        
        Args:
            page_number: 页面编号 (从0开始)
            layout: 布局配置
            
        Returns:
            List[Tuple[int, int]]: 网格位置列表 [(row, col), ...]
        """
        positions = []
        invoices_per_page = layout.total_slots
        
        for i in range(invoices_per_page):
            row = i // layout.columns
            col = i % layout.columns
            positions.append((row, col))
        
        return positions