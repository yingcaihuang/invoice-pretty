"""
文件处理器ZIP功能测试
验证FileHandler的ZIP文件处理功能
"""

import pytest
import tempfile
import zipfile
import os
from pathlib import Path
import fitz

from src.services.file_handler import FileHandler


class TestFileHandlerZip:
    """FileHandler ZIP功能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.handler = FileHandler()
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """测试后清理"""
        self.handler.cleanup_temp_dirs()
        # 清理测试目录
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_pdf(self, path: Path, content: str) -> None:
        """创建测试PDF文件"""
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), content, fontsize=20)
        doc.save(str(path))
        doc.close()
    
    def test_validate_zip_file_valid(self):
        """测试有效ZIP文件验证"""
        # 创建测试PDF
        pdf_path = self.temp_dir / 'test.pdf'
        self.create_test_pdf(pdf_path, 'Test PDF')
        
        # 创建ZIP文件
        zip_path = self.temp_dir / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(pdf_path, 'test.pdf')
        
        # 测试验证
        assert self.handler.validate_zip_file(str(zip_path)) is True
    
    def test_validate_zip_file_invalid(self):
        """测试无效ZIP文件验证"""
        # 测试不存在的文件
        assert self.handler.validate_zip_file('nonexistent.zip') is False
        
        # 测试非ZIP文件
        txt_path = self.temp_dir / 'test.txt'
        txt_path.write_text('Not a zip file')
        assert self.handler.validate_zip_file(str(txt_path)) is False
        
        # 测试损坏的ZIP文件
        bad_zip = self.temp_dir / 'bad.zip'
        bad_zip.write_bytes(b'Not a real zip file')
        assert self.handler.validate_zip_file(str(bad_zip)) is False
    
    def test_extract_pdfs_from_zip_success(self):
        """测试成功从ZIP中提取PDF"""
        # 创建测试PDF文件
        pdf1_path = self.temp_dir / 'invoice1.pdf'
        pdf2_path = self.temp_dir / 'invoice2.pdf'
        ofd_path = self.temp_dir / 'invoice.ofd'
        
        self.create_test_pdf(pdf1_path, 'Invoice 1')
        self.create_test_pdf(pdf2_path, 'Invoice 2')
        ofd_path.write_text('OFD file content')
        
        # 创建ZIP文件
        zip_path = self.temp_dir / 'invoices.zip'
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(pdf1_path, 'invoice1.pdf')
            zip_file.write(pdf2_path, 'invoice2.pdf')
            zip_file.write(ofd_path, 'invoice.ofd')
        
        # 提取PDF文件
        extracted_pdfs = self.handler.extract_pdfs_from_zip(str(zip_path))
        
        # 验证结果
        assert len(extracted_pdfs) == 2
        
        # 验证提取的文件是有效的PDF
        for pdf_path in extracted_pdfs:
            assert self.handler.validate_pdf_file(pdf_path)
    
    def test_extract_pdfs_from_zip_no_pdfs(self):
        """测试从不包含PDF的ZIP中提取"""
        # 创建只包含OFD文件的ZIP
        ofd_path = self.temp_dir / 'invoice.ofd'
        txt_path = self.temp_dir / 'readme.txt'
        
        ofd_path.write_text('OFD file content')
        txt_path.write_text('Text file content')
        
        zip_path = self.temp_dir / 'no_pdfs.zip'
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(ofd_path, 'invoice.ofd')
            zip_file.write(txt_path, 'readme.txt')
        
        # 提取PDF文件
        extracted_pdfs = self.handler.extract_pdfs_from_zip(str(zip_path))
        
        # 验证结果
        assert len(extracted_pdfs) == 0
    
    def test_get_pdf_files_with_zip(self):
        """测试从包含ZIP文件的目录获取PDF"""
        # 创建测试目录结构
        test_dir = self.temp_dir / 'test_files'
        test_dir.mkdir()
        
        # 创建直接的PDF文件
        direct_pdf = test_dir / 'direct.pdf'
        self.create_test_pdf(direct_pdf, 'Direct PDF')
        
        # 创建ZIP文件中的PDF
        zip_pdf1 = self.temp_dir / 'zip_invoice1.pdf'
        zip_pdf2 = self.temp_dir / 'zip_invoice2.pdf'
        self.create_test_pdf(zip_pdf1, 'ZIP Invoice 1')
        self.create_test_pdf(zip_pdf2, 'ZIP Invoice 2')
        
        zip_path = test_dir / 'invoices.zip'
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(zip_pdf1, 'invoice1.pdf')
            zip_file.write(zip_pdf2, 'invoice2.pdf')
        
        # 获取PDF文件列表
        pdf_files = self.handler.get_pdf_files(str(test_dir))
        
        # 验证结果：应该包含1个直接PDF + 2个从ZIP提取的PDF
        assert len(pdf_files) == 3
        
        # 验证所有文件都是有效的PDF
        for pdf_path in pdf_files:
            assert self.handler.validate_pdf_file(pdf_path)
    
    def test_cleanup_temp_dirs(self):
        """测试临时目录清理"""
        # 创建ZIP文件并提取PDF（这会创建临时目录）
        pdf_path = self.temp_dir / 'test.pdf'
        self.create_test_pdf(pdf_path, 'Test PDF')
        
        zip_path = self.temp_dir / 'test.zip'
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(pdf_path, 'test.pdf')
        
        # 提取PDF（创建临时目录）
        extracted_pdfs = self.handler.extract_pdfs_from_zip(str(zip_path))
        assert len(extracted_pdfs) == 1
        
        # 验证临时目录存在
        assert len(self.handler.temp_dirs) > 0
        temp_dir_path = self.handler.temp_dirs[0]
        assert os.path.exists(temp_dir_path)
        
        # 清理临时目录
        self.handler.cleanup_temp_dirs()
        
        # 验证临时目录已被清理
        assert len(self.handler.temp_dirs) == 0
        assert not os.path.exists(temp_dir_path)