# PDF发票拼版打印系统 - 配置说明

## 概述

本系统支持通过配置文件、环境变量等多种方式进行配置。配置文件采用JSON格式，支持热加载和验证。

## 配置文件位置

- 默认配置文件：`config.json`
- 用户可以通过命令行参数指定自定义配置文件路径

## 配置项说明

### 布局配置 (layout)

控制PDF拼版的布局参数：

- `page_width` (float): A4纸张宽度，单位毫米，默认210.0
- `page_height` (float): A4纸张高度，单位毫米，默认297.0
- `columns` (int): 每页列数，默认2
- `rows` (int): 每页行数，默认4
- `margin` (float): 页边距，单位毫米，默认10.0
- `spacing` (float): 发票间距，单位毫米，默认5.0

### 输出配置 (output)

控制PDF输出质量和格式：

- `dpi` (int): 输出分辨率，范围72-1200，默认300
- `quality` (int): 图像质量，范围1-100，默认95
- `format` (string): 输出格式，默认"PDF"

### 文件处理配置 (file_handling)

控制文件处理行为：

- `max_file_size_mb` (float): 最大文件大小限制，单位MB，默认50
- `supported_extensions` (array): 支持的文件扩展名，默认[".pdf"]
- `batch_size` (int): 批处理大小，默认100

### 用户界面配置 (ui)

控制图形界面外观：

- `window_width` (int): 窗口宽度，像素，默认800
- `window_height` (int): 窗口高度，像素，默认600
- `theme` (string): 界面主题，默认"default"

### 日志配置 (logging)

控制日志记录行为：

- `level` (string): 日志级别，可选值：DEBUG, INFO, WARNING, ERROR，默认"INFO"
- `file` (string): 日志文件名，默认"pdf_invoice_layout.log"
- `max_size_mb` (float): 日志文件最大大小，单位MB，默认10
- `backup_count` (int): 日志文件备份数量，默认3

## 环境变量覆盖

系统支持通过环境变量覆盖配置文件中的设置。环境变量命名规则：

```
PDF_INVOICE_<SECTION>_<KEY>
```

例如：
- `PDF_INVOICE_LAYOUT_PAGE_WIDTH=210` - 设置页面宽度
- `PDF_INVOICE_OUTPUT_DPI=600` - 设置输出DPI
- `PDF_INVOICE_UI_WINDOW_WIDTH=1024` - 设置窗口宽度

## 配置验证

系统会自动验证配置的有效性：

1. **数值范围检查**：确保数值在合理范围内
2. **类型检查**：确保配置项类型正确
3. **必需项检查**：确保必需的配置项存在
4. **逻辑一致性**：检查配置项之间的逻辑关系

如果配置验证失败，系统会显示详细的错误信息并拒绝启动。

## 配置示例

### 基本配置示例

```json
{
  "layout": {
    "page_width": 210.0,
    "page_height": 297.0,
    "columns": 2,
    "rows": 4,
    "margin": 15.0,
    "spacing": 8.0
  },
  "output": {
    "dpi": 600,
    "quality": 98
  }
}
```

### 高性能配置示例

```json
{
  "file_handling": {
    "max_file_size_mb": 100,
    "batch_size": 50
  },
  "output": {
    "dpi": 300,
    "quality": 85
  },
  "logging": {
    "level": "WARNING"
  }
}
```

## 故障排除

### 常见配置错误

1. **配置文件格式错误**
   - 确保JSON格式正确
   - 检查是否有多余的逗号或缺少引号

2. **数值超出范围**
   - DPI必须在72-1200之间
   - 质量必须在1-100之间
   - 尺寸必须为正数

3. **环境变量类型错误**
   - 确保数值型环境变量包含有效数字
   - 布尔值使用true/false

### 重置配置

如果配置出现问题，可以删除`config.json`文件，系统会使用默认配置重新创建。

## 配置最佳实践

1. **备份配置**：修改配置前先备份原文件
2. **渐进式修改**：一次只修改少量配置项
3. **测试验证**：修改后运行系统验证配置是否正确
4. **文档记录**：记录自定义配置的原因和用途