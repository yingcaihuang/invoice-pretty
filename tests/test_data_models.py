"""
数据模型测试
验证核心数据模型的基本功能
"""

import pytest
from PIL import Image
from src.models.data_models import PDFDocument, LayoutConfig, PositionedInvoice, ProcessResult


class TestPDFDocument:
    """PDFDocument模型测试"""
    
    def test_pdf_document_creation(self):
        """测试PDFDocument创建"""
        doc = PDFDocument(
            file_path="/test/path.pdf",
            page_count=1,
            dimensions=(595.0, 842.0),
            content=None
        )
        
        assert doc.file_path == "/test/path.pdf"
        assert doc.page_count == 1
        assert doc.dimensions == (595.0, 842.0)


class TestLayoutConfig:
    """LayoutConfig模型测试"""
    
    def test_layout_config_defaults(self):
        """测试LayoutConfig默认值"""
        config = LayoutConfig()
        
        assert config.page_width == 210.0
        assert config.page_height == 297.0
        assert config.columns == 2
        assert config.rows == 4
        assert config.margin == 10.0
        assert config.spacing == 5.0
    
    def test_total_slots_calculation(self):
        """测试总位置数计算"""
        config = LayoutConfig()
        assert config.total_slots == 8
        
        config = LayoutConfig(columns=3, rows=3)
        assert config.total_slots == 9
    
    def test_cell_dimensions_calculation(self):
        """测试单元格尺寸计算"""
        config = LayoutConfig()
        
        # 计算预期值
        available_width = 210.0 - 2 * 10.0 - (2 - 1) * 5.0  # 185.0
        expected_cell_width = available_width / 2  # 92.5
        
        available_height = 297.0 - 2 * 10.0 - (4 - 1) * 5.0  # 262.0
        expected_cell_height = available_height / 4  # 65.5
        
        assert config.cell_width == expected_cell_width
        assert config.cell_height == expected_cell_height


class TestPositionedInvoice:
    """PositionedInvoice模型测试"""
    
    def test_positioned_invoice_creation(self):
        """测试PositionedInvoice创建"""
        # 创建一个测试图像
        test_image = Image.new('RGB', (100, 100), color='white')
        
        invoice = PositionedInvoice(
            image=test_image,
            x=10.0,
            y=20.0,
            width=50.0,
            height=70.0,
            page_number=1,
            original_file_path="/test/invoice.pdf"
        )
        
        assert invoice.x == 10.0
        assert invoice.y == 20.0
        assert invoice.width == 50.0
        assert invoice.height == 70.0
        assert invoice.page_number == 1
        assert invoice.original_file_path == "/test/invoice.pdf"


class TestProcessResult:
    """ProcessResult模型测试"""
    
    def test_process_result_creation(self):
        """测试ProcessResult创建"""
        result = ProcessResult(
            success=True,
            output_file="/output/result.pdf",
            processed_count=5,
            total_pages=2,
            errors=[]
        )
        
        assert result.success is True
        assert result.output_file == "/output/result.pdf"
        assert result.processed_count == 5
        assert result.total_pages == 2
        assert result.errors == []
        assert result.skipped_files == []  # 应该自动初始化为空列表
    
    def test_has_errors_property(self):
        """测试has_errors属性"""
        result_no_errors = ProcessResult(
            success=True,
            output_file="test.pdf",
            processed_count=1,
            total_pages=1,
            errors=[]
        )
        assert result_no_errors.has_errors is False
        
        result_with_errors = ProcessResult(
            success=False,
            output_file="test.pdf",
            processed_count=1,
            total_pages=1,
            errors=["Error 1", "Error 2"]
        )
        assert result_with_errors.has_errors is True
    
    def test_success_rate_calculation(self):
        """测试成功率计算"""
        # 无跳过文件的情况
        result = ProcessResult(
            success=True,
            output_file="test.pdf",
            processed_count=10,
            total_pages=2,
            errors=[],
            skipped_files=[]
        )
        assert result.success_rate == 1.0
        
        # 有跳过文件的情况
        result = ProcessResult(
            success=True,
            output_file="test.pdf",
            processed_count=10,
            total_pages=2,
            errors=[],
            skipped_files=["file1.pdf", "file2.pdf"]
        )
        assert result.success_rate == 0.8  # (10-2)/10
        
        # 处理数量为0的情况
        result = ProcessResult(
            success=False,
            output_file="",
            processed_count=0,
            total_pages=0,
            errors=["No files processed"]
        )
        assert result.success_rate == 0.0