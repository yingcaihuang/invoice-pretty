"""
基础接口定义
定义系统各组件的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable
from PIL import Image

from src.models.data_models import PDFDocument, LayoutConfig, PositionedInvoice, ProcessResult


class IFileHandler(ABC):
    """文件处理接口"""
    
    @abstractmethod
    def validate_pdf_file(self, file_path: str) -> bool:
        """验证PDF文件格式"""
        pass
    
    @abstractmethod
    def get_pdf_files(self, directory: str) -> List[str]:
        """获取目录中的PDF文件列表"""
        pass
    
    @abstractmethod
    def generate_output_filename(self, input_files: List[str]) -> str:
        """生成输出文件名"""
        pass
    
    @abstractmethod
    def validate_zip_file(self, file_path: str) -> bool:
        """验证ZIP文件格式"""
        pass
    
    @abstractmethod
    def extract_pdfs_from_zip(self, zip_path: str) -> List[str]:
        """从ZIP文件中提取PDF文件"""
        pass
    
    @abstractmethod
    def cleanup_temp_dirs(self):
        """清理临时目录"""
        pass


class IPDFReader(ABC):
    """PDF读取接口"""
    
    @abstractmethod
    def read_pdf(self, file_path: str) -> Optional[PDFDocument]:
        """读取PDF文件"""
        pass
    
    @abstractmethod
    def get_page_dimensions(self, pdf_doc: PDFDocument) -> Tuple[float, float]:
        """获取页面尺寸"""
        pass
    
    @abstractmethod
    def extract_page_as_image(self, pdf_doc: PDFDocument, page_num: int = 0) -> Optional[Image.Image]:
        """将PDF页面提取为图像"""
        pass


class ILayoutManager(ABC):
    """布局管理接口"""
    
    @abstractmethod
    def calculate_layout(self, invoice_count: int) -> LayoutConfig:
        """计算布局配置"""
        pass
    
    @abstractmethod
    def calculate_scale_factor(self, original_size: Tuple[float, float], target_size: Tuple[float, float]) -> float:
        """计算缩放因子，保持纵横比"""
        pass
    
    @abstractmethod
    def position_invoices(self, invoices: List[Image.Image], layout: LayoutConfig, file_paths: List[str]) -> List[PositionedInvoice]:
        """计算发票位置"""
        pass


class IPDFProcessor(ABC):
    """PDF处理接口"""
    
    @abstractmethod
    def process_invoices(self, input_files: List[str], output_path: str, 
                        progress_callback: Optional[Callable[[float, str], None]] = None) -> ProcessResult:
        """处理发票文件"""
        pass
    
    @abstractmethod
    def create_layout_pdf(self, positioned_invoices: List[PositionedInvoice]) -> Optional[PDFDocument]:
        """创建拼版PDF"""
        pass
    
    @abstractmethod
    def save_pdf(self, pdf_doc: PDFDocument, output_path: str) -> bool:
        """保存PDF文件"""
        pass


class IUIController(ABC):
    """用户界面控制接口"""
    
    @abstractmethod
    def show_file_selection_dialog(self) -> List[str]:
        """显示文件选择对话框"""
        pass
    
    @abstractmethod
    def update_progress(self, progress: float, message: str) -> None:
        """更新进度显示"""
        pass
    
    @abstractmethod
    def show_completion_message(self, result: ProcessResult) -> None:
        """显示完成消息"""
        pass
    
    @abstractmethod
    def show_error_message(self, error: Exception) -> None:
        """显示错误消息"""
        pass


# 进度回调类型定义
ProgressCallback = Callable[[float, str], None]

# 错误处理回调类型定义
ErrorCallback = Callable[[Exception], None]