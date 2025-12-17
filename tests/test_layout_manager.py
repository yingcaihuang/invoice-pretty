"""
布局管理器测试
验证LayoutManager的核心功能
"""

import pytest
import math
from PIL import Image
from src.services.layout_manager import LayoutManager
from src.models.data_models import LayoutConfig


class TestLayoutManager:
    """LayoutManager测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.manager = LayoutManager()
    
    def test_calculate_layout(self):
        """测试布局计算"""
        layout = self.manager.calculate_layout(5)
        
        # 验证默认2列4行配置
        assert layout.columns == 2
        assert layout.rows == 4
        assert layout.total_slots == 8
        assert layout.page_width == 210.0
        assert layout.page_height == 297.0
        assert layout.margin == 10.0
        assert layout.spacing == 5.0
    
    def test_calculate_scale_factor_normal(self):
        """测试正常缩放因子计算"""
        # 测试需要缩小的情况
        scale = self.manager.calculate_scale_factor((100, 150), (50, 75))
        assert scale == 0.5
        
        # 测试需要放大的情况
        scale = self.manager.calculate_scale_factor((50, 75), (100, 150))
        assert scale == 2.0
        
        # 测试保持纵横比的情况 (宽度限制)
        scale = self.manager.calculate_scale_factor((100, 100), (50, 200))
        assert scale == 0.5  # 受宽度限制
        
        # 测试保持纵横比的情况 (高度限制)
        scale = self.manager.calculate_scale_factor((100, 100), (200, 50))
        assert scale == 0.5  # 受高度限制
    
    def test_calculate_scale_factor_edge_cases(self):
        """测试缩放因子计算的边界情况"""
        # 测试零尺寸
        scale = self.manager.calculate_scale_factor((0, 100), (50, 75))
        assert scale == 1.0
        
        scale = self.manager.calculate_scale_factor((100, 0), (50, 75))
        assert scale == 1.0
        
        scale = self.manager.calculate_scale_factor((100, 100), (0, 75))
        assert scale == 1.0
        
        scale = self.manager.calculate_scale_factor((100, 100), (50, 0))
        assert scale == 1.0
        
        # 测试负数尺寸
        scale = self.manager.calculate_scale_factor((-100, 100), (50, 75))
        assert scale == 1.0
    
    def test_calculate_pages_needed(self):
        """测试页面数量计算"""
        # 测试0张发票
        assert self.manager.calculate_pages_needed(0) == 0
        
        # 测试1-8张发票 (1页)
        for i in range(1, 9):
            assert self.manager.calculate_pages_needed(i) == 1
        
        # 测试9-16张发票 (2页)
        for i in range(9, 17):
            assert self.manager.calculate_pages_needed(i) == 2
        
        # 测试17张发票 (3页)
        assert self.manager.calculate_pages_needed(17) == 3
    
    def test_position_invoices_empty_list(self):
        """测试空发票列表的位置计算"""
        layout = LayoutConfig()
        positioned = self.manager.position_invoices([], layout, [])
        assert len(positioned) == 0
    
    def test_position_invoices_single_page(self):
        """测试单页发票位置计算"""
        layout = LayoutConfig()
        
        # 创建3张测试发票
        invoices = []
        file_paths = []
        for i in range(3):
            img = Image.new('RGB', (100, 150), color='white')
            invoices.append(img)
            file_paths.append(f'test_{i}.pdf')
        
        positioned = self.manager.position_invoices(invoices, layout, file_paths)
        
        # 验证基本属性
        assert len(positioned) == 3
        
        # 验证所有发票都在第0页
        for pos in positioned:
            assert pos.page_number == 0
        
        # 验证位置顺序 (从左上角开始按行填充)
        # 第一张: (0,0)
        assert positioned[0].x == layout.margin + (layout.cell_width - positioned[0].width) / 2
        assert positioned[0].y == layout.margin + (layout.cell_height - positioned[0].height) / 2
        
        # 第二张: (0,1)
        expected_x = layout.margin + 1 * (layout.cell_width + layout.spacing) + (layout.cell_width - positioned[1].width) / 2
        assert positioned[1].x == expected_x
        assert positioned[1].y == layout.margin + (layout.cell_height - positioned[1].height) / 2
        
        # 第三张: (1,0)
        assert positioned[2].x == layout.margin + (layout.cell_width - positioned[2].width) / 2
        expected_y = layout.margin + 1 * (layout.cell_height + layout.spacing) + (layout.cell_height - positioned[2].height) / 2
        assert positioned[2].y == expected_y
    
    def test_position_invoices_multiple_pages(self):
        """测试多页发票位置计算"""
        layout = LayoutConfig()
        
        # 创建10张测试发票 (需要2页)
        invoices = []
        file_paths = []
        for i in range(10):
            img = Image.new('RGB', (100, 150), color='white')
            invoices.append(img)
            file_paths.append(f'test_{i}.pdf')
        
        positioned = self.manager.position_invoices(invoices, layout, file_paths)
        
        # 验证总数
        assert len(positioned) == 10
        
        # 验证页面分配
        page_0_count = sum(1 for pos in positioned if pos.page_number == 0)
        page_1_count = sum(1 for pos in positioned if pos.page_number == 1)
        
        assert page_0_count == 8  # 第一页满8张
        assert page_1_count == 2  # 第二页2张
    
    def test_position_invoices_file_paths_mismatch(self):
        """测试文件路径数量不匹配的情况"""
        layout = LayoutConfig()
        
        # 创建3张发票但只提供2个文件路径
        invoices = []
        for i in range(3):
            img = Image.new('RGB', (100, 150), color='white')
            invoices.append(img)
        
        file_paths = ['test_0.pdf', 'test_1.pdf']  # 只有2个路径
        
        positioned = self.manager.position_invoices(invoices, layout, file_paths)
        
        # 验证处理成功
        assert len(positioned) == 3
        
        # 验证文件路径
        assert positioned[0].original_file_path == 'test_0.pdf'
        assert positioned[1].original_file_path == 'test_1.pdf'
        assert positioned[2].original_file_path == ''  # 应该用空字符串填充
    
    def test_get_invoice_positions_for_page(self):
        """测试获取页面发票网格位置"""
        layout = LayoutConfig()
        positions = self.manager.get_invoice_positions_for_page(0, layout)
        
        # 验证2列4行的位置
        expected_positions = [
            (0, 0), (0, 1),  # 第一行
            (1, 0), (1, 1),  # 第二行
            (2, 0), (2, 1),  # 第三行
            (3, 0), (3, 1)   # 第四行
        ]
        
        assert positions == expected_positions
    
    def test_aspect_ratio_preservation(self):
        """测试纵横比保持"""
        layout = LayoutConfig()
        
        # 创建一个特定纵横比的发票 (2:3)
        original_width, original_height = 200, 300
        img = Image.new('RGB', (original_width, original_height), color='white')
        
        positioned = self.manager.position_invoices([img], layout, ['test.pdf'])
        
        # 计算原始纵横比
        original_aspect_ratio = original_width / original_height
        
        # 计算缩放后的纵横比 (需要转换回像素)
        pixels_per_mm = 72 / 25.4
        scaled_width_px = positioned[0].width * pixels_per_mm
        scaled_height_px = positioned[0].height * pixels_per_mm
        scaled_aspect_ratio = scaled_width_px / scaled_height_px
        
        # 验证纵横比保持不变 (允许小的浮点误差)
        assert abs(original_aspect_ratio - scaled_aspect_ratio) < 0.001