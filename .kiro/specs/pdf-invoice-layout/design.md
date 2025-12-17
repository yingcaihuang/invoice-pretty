# 设计文档

## 概述

PDF发票拼版打印系统是一个桌面应用程序，专门用于处理12306电子发票PDF文件的批量拼版打印。系统采用Python开发，使用PyMuPDF进行PDF处理，tkinter提供用户界面，并可打包为单一可执行文件以便部署。

系统的核心功能是将多个单张发票PDF文件智能排列到A4纸张上，实现2列4行的布局，每页最多容纳8张发票，从而优化打印效果并节省纸张。

## 架构

系统采用分层架构设计：

```
┌─────────────────────────────────────┐
│           用户界面层 (UI Layer)        │
│         tkinter GUI / CLI           │
├─────────────────────────────────────┤
│         业务逻辑层 (Business Layer)    │
│    PDFProcessor, LayoutManager      │
├─────────────────────────────────────┤
│         数据访问层 (Data Layer)        │
│      FileHandler, PDFReader         │
├─────────────────────────────────────┤
│         基础设施层 (Infrastructure)    │
│     PyMuPDF, Pillow, pathlib       │
└─────────────────────────────────────┘
```

## 组件和接口

### 1. 文件处理组件 (FileHandler)
```python
class FileHandler:
    def validate_pdf_file(self, file_path: str) -> bool
    def get_pdf_files(self, directory: str) -> List[str]
    def generate_output_filename(self, input_files: List[str]) -> str
```

### 2. PDF读取组件 (PDFReader)
```python
class PDFReader:
    def read_pdf(self, file_path: str) -> PDFDocument
    def get_page_dimensions(self, pdf_doc: PDFDocument) -> Tuple[float, float]
    def extract_page_as_image(self, pdf_doc: PDFDocument, page_num: int) -> Image
```

### 3. 布局管理组件 (LayoutManager)
```python
class LayoutManager:
    def calculate_layout(self, invoice_count: int) -> LayoutConfig
    def calculate_scale_factor(self, original_size: Tuple[float, float], target_size: Tuple[float, float]) -> float
    def position_invoices(self, invoices: List[Image], layout: LayoutConfig) -> List[PositionedInvoice]
```

### 4. PDF处理组件 (PDFProcessor)
```python
class PDFProcessor:
    def process_invoices(self, input_files: List[str], output_path: str) -> ProcessResult
    def create_layout_pdf(self, positioned_invoices: List[PositionedInvoice]) -> PDFDocument
    def save_pdf(self, pdf_doc: PDFDocument, output_path: str) -> bool
```

### 5. 用户界面组件 (UIController)
```python
class UIController:
    def show_file_selection_dialog(self) -> List[str]
    def update_progress(self, progress: float, message: str) -> None
    def show_completion_message(self, result: ProcessResult) -> None
    def show_error_message(self, error: Exception) -> None
```

## 数据模型

### PDFDocument
```python
@dataclass
class PDFDocument:
    file_path: str
    page_count: int
    dimensions: Tuple[float, float]
    content: Any  # PyMuPDF document object
```

### LayoutConfig
```python
@dataclass
class LayoutConfig:
    page_width: float = 210  # A4 width in mm
    page_height: float = 297  # A4 height in mm
    columns: int = 2
    rows: int = 4
    margin: float = 10  # margin in mm
    spacing: float = 5  # spacing between invoices in mm
```

### PositionedInvoice
```python
@dataclass
class PositionedInvoice:
    image: Image
    x: float
    y: float
    width: float
    height: float
    page_number: int
```

### ProcessResult
```python
@dataclass
class ProcessResult:
    success: bool
    output_file: str
    processed_count: int
    total_pages: int
    errors: List[str]
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: PDF文件验证一致性
*对于任何*有效的PDF文件，文件验证函数应该返回true，系统应该接受该文件进行处理
**验证: 需求 1.1**

### 属性 2: 批量处理完整性
*对于任何*PDF文件列表，批量处理应该尝试处理列表中的每一个文件
**验证: 需求 1.2**

### 属性 3: 无效文件拒绝
*对于任何*无效的文件格式，系统应该拒绝该文件并返回适当的错误信息
**验证: 需求 1.3**

### 属性 4: 错误处理优雅性
*对于任何*损坏或无法读取的PDF文件，系统应该跳过该文件并继续处理其他文件，同时记录错误
**验证: 需求 1.4**

### 属性 5: 布局网格一致性
*对于任何*布局计算，系统应该始终生成2列4行共8个区域的网格布局
**验证: 需求 2.1**

### 属性 6: 纵横比保持不变性
*对于任何*发票图像，缩放操作前后的纵横比应该保持相等（在浮点精度范围内）
**验证: 需求 2.2**

### 属性 7: 填充顺序一致性
*对于任何*少于8张的发票集合，系统应该从左上角开始按行顺序填充位置
**验证: 需求 2.3**

### 属性 8: 分页逻辑正确性
*对于任何*发票数量n，生成的页面数量应该等于ceil(n/8)
**验证: 需求 2.4**

### 属性 9: PDF生成成功性
*对于任何*有效的拼版布局，系统应该成功生成一个有效的PDF文件
**验证: 需求 3.1**

### 属性 10: 输出质量保证
*对于任何*生成的PDF文件，其DPI设置应该大于或等于300
**验证: 需求 3.2**

### 属性 11: 文件命名规范性
*对于任何*输出文件，文件名应该包含处理日期和发票数量信息
**验证: 需求 3.3**

### 属性 12: 文件保存位置正确性
*对于任何*指定的输出路径，生成的文件应该保存在该路径下
**验证: 需求 3.4**

### 属性 13: 进度更新连续性
*对于任何*处理过程，进度回调应该被调用，且进度值应该在0到100之间单调递增
**验证: 需求 4.2**

### 属性 14: 成功完成信息完整性
*对于任何*成功的处理过程，完成回调应该包含输出文件路径和处理统计信息
**验证: 需求 4.3**

### 属性 15: 错误信息有用性
*对于任何*处理错误，错误回调应该包含具体的错误描述和建议的解决方案
**验证: 需求 4.4**

## 错误处理

### 文件处理错误
- **无效PDF文件**: 返回验证错误，提供文件格式建议
- **文件访问权限**: 返回权限错误，建议检查文件权限
- **磁盘空间不足**: 返回存储错误，建议清理磁盘空间
- **文件损坏**: 跳过文件，记录错误日志，继续处理其他文件

### 内存和性能错误
- **内存不足**: 实施分批处理，减少同时加载的文件数量
- **处理超时**: 提供进度反馈，允许用户取消操作
- **大文件处理**: 实施流式处理，避免一次性加载整个文件

### 输出错误
- **输出路径无效**: 验证路径存在性，提供路径选择建议
- **文件名冲突**: 自动添加序号后缀，避免覆盖现有文件
- **PDF生成失败**: 提供详细错误信息，建议检查输入文件

## 测试策略

### 双重测试方法

系统将采用单元测试和基于属性的测试相结合的方法：

**单元测试**:
- 验证具体示例和边缘情况
- 测试组件间的集成点
- 验证错误条件的处理

**基于属性的测试**:
- 使用Hypothesis库进行Python的基于属性测试
- 每个属性测试运行最少100次迭代
- 验证跨所有输入的通用属性
- 每个基于属性的测试必须用注释明确引用设计文档中的正确性属性
- 测试标签格式: '**Feature: pdf-invoice-layout, Property {number}: {property_text}**'

**测试覆盖范围**:
- 文件验证和处理逻辑
- 布局计算算法
- PDF生成和输出质量
- 错误处理和恢复机制
- 用户界面交互和反馈

**测试数据生成**:
- 生成各种尺寸和格式的测试PDF文件
- 创建边界条件测试用例（空文件、超大文件等）
- 模拟各种错误条件（权限问题、磁盘空间不足等）

### 性能测试
- 批量处理性能基准测试
- 内存使用监控
- 大文件处理能力验证