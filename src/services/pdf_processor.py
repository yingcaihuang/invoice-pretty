"""
PDF处理服务
实现发票处理的主要流程，包括拼版PDF创建和文件保存功能
"""

import logging
import os
from typing import List, Optional, Callable
import fitz
from PIL import Image
import io

from src.interfaces.base_interfaces import IPDFProcessor, ProgressCallback
from src.models.data_models import PDFDocument, LayoutConfig, PositionedInvoice, ProcessResult
from src.services.file_handler import FileHandler
from src.services.pdf_reader import PDFReader
from src.services.layout_manager import LayoutManager


class PDFProcessor(IPDFProcessor):
    """PDF处理器实现类"""
    
    def __init__(self):
        """初始化PDF处理器"""
        self.logger = logging.getLogger(__name__)
        self.file_handler = FileHandler()
        self.pdf_reader = PDFReader()
        self.layout_manager = LayoutManager()
        
        # 设置输出质量参数 (确保300DPI或更高)
        self.output_dpi = 300
        self.scale_factor = self.output_dpi / 72  # 从72 DPI缩放到300 DPI
    
    def process_invoices(self, input_files: List[str], output_path: str, 
                        progress_callback: Optional[ProgressCallback] = None) -> ProcessResult:
        """
        处理发票文件的主要流程
        
        Args:
            input_files: 输入PDF文件路径列表
            output_path: 输出文件路径
            progress_callback: 进度回调函数
            
        Returns:
            ProcessResult: 处理结果
        """
        self.logger.info(f"开始处理 {len(input_files)} 个发票文件")
        
        # 初始化结果对象
        result = ProcessResult(
            success=False,
            output_file=output_path,
            processed_count=0,
            total_pages=0,
            errors=[],
            skipped_files=[]
        )
        
        try:
            # 步骤1: 验证输入文件
            if progress_callback:
                progress_callback(10.0, "验证输入文件...")
            
            self.logger.info("开始验证输入文件...")
            valid_files = []
            for file_path in input_files:
                if self.file_handler.validate_pdf_file(file_path):
                    valid_files.append(file_path)
                    self.logger.info(f"✓ 验证通过: {os.path.basename(file_path)}")
                else:
                    result.skipped_files.append(file_path)
                    result.errors.append(f"无效的PDF文件: {file_path}")
                    self.logger.warning(f"✗ 验证失败: {os.path.basename(file_path)}")
            
            if not valid_files:
                result.errors.append("没有找到有效的PDF文件")
                self.logger.error("没有找到有效的PDF文件")
                return result
            
            result.processed_count = len(valid_files)
            self.logger.info(f"文件验证完成，有效文件: {len(valid_files)} 个")
            
            # 步骤2: 读取PDF文件并提取图像
            if progress_callback:
                progress_callback(30.0, "读取PDF文件...")
            
            self.logger.info("开始读取PDF文件并提取图像...")
            invoice_images = []
            pdf_documents = []
            
            for i, file_path in enumerate(valid_files):
                try:
                    filename = os.path.basename(file_path)
                    self.logger.info(f"正在读取文件: {filename}")
                    
                    # 读取PDF文档
                    pdf_doc = self.pdf_reader.read_pdf(file_path)
                    if pdf_doc is None:
                        result.skipped_files.append(file_path)
                        result.errors.append(f"无法读取PDF文件: {file_path}")
                        self.logger.error(f"✗ 无法读取PDF文件: {filename}")
                        continue
                    
                    pdf_documents.append(pdf_doc)
                    
                    # 提取第一页为图像
                    image = self.pdf_reader.extract_page_as_image(pdf_doc, 0)
                    if image is None:
                        result.skipped_files.append(file_path)
                        result.errors.append(f"无法提取PDF页面图像: {file_path}")
                        self.logger.error(f"✗ 无法提取图像: {filename}")
                        continue
                    
                    invoice_images.append(image)
                    self.logger.info(f"✓ 成功提取图像: {filename} (尺寸: {image.size})")
                    
                    # 更新进度
                    if progress_callback:
                        progress = 30.0 + (i + 1) / len(valid_files) * 30.0
                        progress_callback(progress, f"已读取 {i + 1}/{len(valid_files)} 个文件")
                
                except Exception as e:
                    self.logger.error(f"处理文件 {os.path.basename(file_path)} 时发生错误: {str(e)}")
                    result.skipped_files.append(file_path)
                    result.errors.append(f"处理文件失败 {file_path}: {str(e)}")
            
            if not invoice_images:
                result.errors.append("没有成功提取任何发票图像")
                return result
            
            # 步骤3: 计算布局和位置
            if progress_callback:
                progress_callback(60.0, "计算布局...")
            
            self.logger.info(f"开始计算布局，发票数量: {len(invoice_images)}")
            layout = self.layout_manager.calculate_layout(len(invoice_images))
            self.logger.info(f"布局配置: {layout.columns}列 x {layout.rows}行，页边距: {layout.margin}mm")
            
            positioned_invoices = self.layout_manager.position_invoices(
                invoice_images, layout, valid_files
            )
            
            result.total_pages = self.layout_manager.calculate_pages_needed(len(invoice_images))
            self.logger.info(f"布局计算完成，将生成 {result.total_pages} 页PDF")
            
            # 步骤4: 创建拼版PDF
            if progress_callback:
                progress_callback(80.0, "创建拼版PDF...")
            
            self.logger.info("开始创建拼版PDF...")
            output_pdf = self.create_layout_pdf(positioned_invoices)
            if output_pdf is None:
                result.errors.append("创建拼版PDF失败")
                self.logger.error("创建拼版PDF失败")
                return result
            
            self.logger.info(f"拼版PDF创建成功，共 {output_pdf.page_count} 页")
            
            # 步骤5: 保存PDF文件
            if progress_callback:
                progress_callback(90.0, "保存PDF文件...")
            
            self.logger.info(f"开始保存PDF文件: {os.path.basename(output_path)}")
            if not self.save_pdf(output_pdf, output_path):
                result.errors.append("保存PDF文件失败")
                self.logger.error("保存PDF文件失败")
                return result
            
            self.logger.info(f"PDF文件保存成功: {output_path}")
            
            # 清理资源
            for pdf_doc in pdf_documents:
                self.pdf_reader.close_document(pdf_doc)
            
            if output_pdf.content:
                output_pdf.content.close()
            
            # 完成
            if progress_callback:
                progress_callback(100.0, "处理完成")
            
            result.success = True
            self.logger.info(f"成功处理 {len(invoice_images)} 张发票，生成 {result.total_pages} 页PDF")
            
        except Exception as e:
            self.logger.error(f"处理发票时发生错误: {str(e)}")
            result.errors.append(f"处理过程中发生错误: {str(e)}")
        
        return result
    
    def create_layout_pdf(self, positioned_invoices: List[PositionedInvoice]) -> Optional[PDFDocument]:
        """
        创建拼版PDF文档
        
        Args:
            positioned_invoices: 定位后的发票列表
            
        Returns:
            Optional[PDFDocument]: 创建的PDF文档，失败时返回None
        """
        try:
            if not positioned_invoices:
                self.logger.error("没有发票可以创建PDF")
                return None
            
            # 创建新的PDF文档
            doc = fitz.open()
            
            # 计算A4页面尺寸 (单位: 点, 1mm = 2.834645669 points)
            mm_to_points = 2.834645669
            page_width = 210 * mm_to_points  # A4宽度
            page_height = 297 * mm_to_points  # A4高度
            
            # 按页面分组发票
            pages_dict = {}
            for invoice in positioned_invoices:
                page_num = invoice.page_number
                if page_num not in pages_dict:
                    pages_dict[page_num] = []
                pages_dict[page_num].append(invoice)
            
            # 为每个页面创建PDF页面
            for page_num in sorted(pages_dict.keys()):
                page_invoices = pages_dict[page_num]
                
                # 创建新页面
                page = doc.new_page(width=page_width, height=page_height)
                
                # 在页面上放置每张发票
                for invoice in page_invoices:
                    try:
                        # 将发票图像转换为字节流
                        img_bytes = self._image_to_bytes(invoice.image)
                        if img_bytes is None:
                            continue
                        
                        # 计算位置和尺寸 (转换mm到点)
                        x = invoice.x * mm_to_points
                        y = invoice.y * mm_to_points
                        width = invoice.width * mm_to_points
                        height = invoice.height * mm_to_points
                        
                        # 创建矩形区域
                        rect = fitz.Rect(x, y, x + width, y + height)
                        
                        # 插入图像到页面
                        page.insert_image(rect, stream=img_bytes)
                        
                    except Exception as e:
                        self.logger.error(f"插入发票图像失败: {str(e)}")
                        continue
            
            # 创建PDFDocument对象
            pdf_document = PDFDocument(
                file_path="",  # 输出文件路径稍后设置
                page_count=doc.page_count,
                dimensions=(page_width, page_height),
                content=doc
            )
            
            self.logger.info(f"成功创建拼版PDF，共 {doc.page_count} 页")
            return pdf_document
            
        except Exception as e:
            self.logger.error(f"创建拼版PDF失败: {str(e)}")
            return None
    
    def save_pdf(self, pdf_doc: PDFDocument, output_path: str) -> bool:
        """
        保存PDF文件到指定路径
        
        Args:
            pdf_doc: PDF文档对象
            output_path: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if pdf_doc.content is None:
                self.logger.error("PDF文档内容为空")
                return False
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 保存PDF文件
            pdf_doc.content.save(output_path)
            
            # 验证文件是否成功保存
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.logger.info(f"成功保存PDF文件: {output_path}")
                return True
            else:
                self.logger.error(f"PDF文件保存失败或文件为空: {output_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存PDF文件失败: {str(e)}")
            return False
    
    def _image_to_bytes(self, image: Image.Image) -> Optional[bytes]:
        """
        将PIL图像转换为字节流
        
        Args:
            image: PIL图像对象
            
        Returns:
            Optional[bytes]: 图像字节流，失败时返回None
        """
        try:
            # 确保图像为RGB模式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 将图像保存到字节流
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95, dpi=(self.output_dpi, self.output_dpi))
            img_bytes = img_buffer.getvalue()
            img_buffer.close()
            
            return img_bytes
            
        except Exception as e:
            self.logger.error(f"图像转换为字节流失败: {str(e)}")
            return None
    
    def get_output_quality_dpi(self) -> int:
        """
        获取输出质量DPI设置
        
        Returns:
            int: DPI值
        """
        return self.output_dpi
    
    def set_output_quality_dpi(self, dpi: int) -> None:
        """
        设置输出质量DPI
        
        Args:
            dpi: DPI值，最小为300
        """
        if dpi < 300:
            self.logger.warning(f"DPI值 {dpi} 低于最小要求300，设置为300")
            dpi = 300
        
        self.output_dpi = dpi
        self.scale_factor = dpi / 72
        self.logger.info(f"输出质量DPI设置为: {dpi}")