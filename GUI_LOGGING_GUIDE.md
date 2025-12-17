# GUI日志同步功能使用指南

## 功能概述

PDF发票拼版打印系统现在支持在GUI界面中实时显示处理日志，让用户可以清楚地看到处理进度和详细信息。

## 功能特点

### 🔄 实时日志同步
- 所有后台处理的日志信息都会实时显示在GUI界面上
- 包括文件验证、图像提取、布局计算、PDF生成等各个步骤的详细信息
- 自动添加时间戳，方便跟踪处理时间

### 📊 详细进度信息
- 文件验证结果（✓ 成功 / ✗ 失败）
- 图像提取详情（文件名、尺寸信息）
- 布局计算参数（列数、行数、页边距）
- PDF生成状态（页数、保存路径）

### 🎯 用户友好的显示
- 日志信息显示在界面底部的"处理结果"区域
- 支持滚动查看历史日志
- 自动滚动到最新消息
- 清晰的时间戳格式

## 使用方法

### 1. 启动应用
```bash
python main.py
```

### 2. 选择文件和输出目录
- 点击"选择文件"或"选择文件夹"添加PDF文件
- 点击"选择输出目录"设置保存位置

### 3. 开始处理
- 点击"开始拼版处理"按钮
- 在"处理结果"区域实时查看处理日志
- 进度条显示整体进度，日志显示详细步骤

## 日志信息说明

### 文件验证阶段
```
[16:22:23] src.services.file_handler - INFO - ✓ 验证通过: 发票001.pdf
[16:22:23] src.services.file_handler - INFO - ✗ 验证失败: 无效文件.txt
```

### 图像提取阶段
```
[16:22:24] src.services.pdf_processor - INFO - 正在读取文件: 发票001.pdf
[16:22:24] src.services.pdf_processor - INFO - ✓ 成功提取图像: 发票001.pdf (尺寸: (595, 842))
```

### 布局计算阶段
```
[16:22:25] src.services.layout_manager - INFO - 开始计算布局，发票数量: 8
[16:22:25] src.services.layout_manager - INFO - 布局配置: 2列 x 4行，页边距: 10mm
[16:22:25] src.services.layout_manager - INFO - 布局计算完成，将生成 1 页PDF
```

### PDF生成阶段
```
[16:22:26] src.services.pdf_processor - INFO - 开始创建拼版PDF...
[16:22:26] src.services.pdf_processor - INFO - 拼版PDF创建成功，共 1 页
[16:22:27] src.services.pdf_processor - INFO - PDF文件保存成功: /path/to/output.pdf
```

## 技术实现

### 日志处理器
- 使用自定义的 `GUILogHandler` 类
- 通过 `queue.Queue` 在后台线程和GUI线程间传递日志消息
- 自动格式化日志消息并添加时间戳

### 实时更新
- 每100ms检查一次日志队列
- 使用 `tkinter.after()` 方法确保线程安全
- 自动滚动到最新消息

### 监控的日志源
- `src.services.pdf_processor` - PDF处理核心逻辑
- `src.services.file_handler` - 文件操作和验证
- `src.services.pdf_reader` - PDF读取和图像提取
- `src.services.layout_manager` - 布局计算
- `src.ui.gui_controller` - GUI控制器

## 演示和测试

### 运行功能演示
```bash
python demo_gui_logging.py
```
这将启动一个演示，模拟处理过程并显示日志信息。

### 运行功能测试
```bash
python test_gui_logging.py
```
这将测试日志同步功能是否正常工作。

## 故障排除

### 日志不显示
1. 检查是否正确启动了GUI应用
2. 确认处理过程已经开始
3. 查看控制台是否有错误信息

### 界面卡顿
1. 日志队列处理是异步的，不应该影响界面响应
2. 如果出现卡顿，可能是处理的文件过大或数量过多
3. 可以通过控制台查看详细的错误信息

## 配置选项

目前日志同步功能使用默认配置：
- 日志级别：INFO
- 检查间隔：100ms
- 时间戳格式：HH:MM:SS

如需自定义配置，可以修改 `src/ui/gui_controller.py` 中的相关参数。