"""
PDF读取服务
实现PDF文件的读取、页面尺寸获取和页面转图像功能
"""

import logging
from typing import Optional, Tuple
import fitz
from PIL import Image
import io

from src.interfaces.base_interfaces import IPDFReader
from src.models.data_models import PDFDocument


class PDFReader(IPDFReader):
    """PDF读取实现类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def read_pdf(self, file_path: str) -> Optional[PDFDocument]:
        """
        读取PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            Optional[PDFDocument]: PDF文档对象，如果读取失败返回None
        """
        try:
            # 打开PDF文件
            doc = fitz.open(file_path)
            
            # 获取页面数量
            page_count = doc.page_count
            
            if page_count == 0:
                self.logger.warning(f"PDF文件没有页面: {file_path}")
                doc.close()
                return None
            
            # 获取第一页的尺寸作为文档尺寸
            first_page = doc[0]
            rect = first_page.rect
            dimensions = (rect.width, rect.height)
            
            # 创建PDFDocument对象
            pdf_document = PDFDocument(
                file_path=file_path,
                page_count=page_count,
                dimensions=dimensions,
                content=doc  # 保持文档打开状态，由调用者负责关闭
            )
            
            self.logger.info(f"成功读取PDF文件: {file_path}, 页数: {page_count}, 尺寸: {dimensions}")
            return pdf_document
            
        except Exception as e:
            self.logger.error(f"读取PDF文件失败 {file_path}: {str(e)}")
            return None
    
    def get_page_dimensions(self, pdf_doc: PDFDocument) -> Tuple[float, float]:
        """
        获取页面尺寸
        
        Args:
            pdf_doc: PDF文档对象
            
        Returns:
            Tuple[float, float]: 页面尺寸 (宽度, 高度) 单位为点
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF文档内容为空")
                return (0.0, 0.0)
            
            # 返回已存储的尺寸信息
            return pdf_doc.dimensions
            
        except Exception as e:
            self.logger.error(f"获取页面尺寸失败: {str(e)}")
            return (0.0, 0.0)
    
    def extract_page_as_image(self, pdf_doc: PDFDocument, page_num: int = 0) -> Optional[Image.Image]:
        """
        将PDF页面提取为图像
        
        Args:
            pdf_doc: PDF文档对象
            page_num: 页面编号，默认为0（第一页）
            
        Returns:
            Optional[Image.Image]: PIL图像对象，如果提取失败返回None
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF文档内容为空")
                return None
            
            doc = pdf_doc.content
            
            # 检查页面编号是否有效
            if page_num < 0 or page_num >= doc.page_count:
                self.logger.error(f"页面编号无效: {page_num}, 文档总页数: {doc.page_count}")
                return None
            
            # 获取指定页面
            page = doc[page_num]
            
            # 设置渲染参数，确保高质量输出
            # 使用2.0的缩放因子以获得更高的分辨率（约300 DPI）
            matrix = fitz.Matrix(2.0, 2.0)
            
            # 渲染页面为像素图
            pix = page.get_pixmap(matrix=matrix)
            
            # 将像素图转换为PIL图像
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            
            # 清理资源
            pix = None
            
            self.logger.info(f"成功提取页面 {page_num} 为图像，尺寸: {img.size}")
            return img
            
        except Exception as e:
            self.logger.error(f"提取页面为图像失败 (页面 {page_num}): {str(e)}")
            return None
    
    def close_document(self, pdf_doc: PDFDocument) -> None:
        """
        关闭PDF文档
        
        Args:
            pdf_doc: PDF文档对象
        """
        try:
            if pdf_doc.content is not None:
                pdf_doc.content.close()
                self.logger.debug(f"已关闭PDF文档: {pdf_doc.file_path}")
        except Exception as e:
            self.logger.error(f"关闭PDF文档失败: {str(e)}")