# PDF发票拼版打印系统 - 安装说明

## 系统要求

### 最低要求
- **操作系统**: Windows 10+, macOS 10.14+, 或 Linux (Ubuntu 18.04+)
- **Python版本**: Python 3.8 或更高版本
- **内存**: 至少 512MB 可用内存
- **磁盘空间**: 至少 100MB 可用空间

### 推荐配置
- **内存**: 2GB 或更多
- **磁盘空间**: 500MB 或更多（用于处理大量PDF文件）
- **显示器**: 1024x768 或更高分辨率

## 安装方式

### 方式一：使用预编译可执行文件（推荐）

1. **下载安装包**
   - Windows: 下载 `pdf-invoice-layout-windows.zip`
   - macOS: 下载 `pdf-invoice-layout-macos.zip`
   - Linux: 下载 `pdf-invoice-layout-linux.tar.gz`

2. **解压安装包**
   ```bash
   # Windows (使用文件管理器或命令行)
   unzip pdf-invoice-layout-windows.zip
   
   # macOS
   unzip pdf-invoice-layout-macos.zip
   
   # Linux
   tar -xzf pdf-invoice-layout-linux.tar.gz
   ```

3. **运行程序**
   - Windows: 双击 `pdf-invoice-layout.exe`
   - macOS: 双击 `PDF发票拼版打印系统.app`
   - Linux: 在终端中运行 `./pdf-invoice-layout`

### 方式二：从源代码安装

1. **克隆或下载源代码**
   ```bash
   git clone <repository-url>
   cd pdf-invoice-layout
   ```

2. **运行自动安装脚本**
   ```bash
   python install.py
   ```

3. **手动安装（如果自动安装失败）**
   ```bash
   # 创建虚拟环境（推荐）
   python -m venv venv
   
   # 激活虚拟环境
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 运行程序
   python main.py
   ```

## 验证安装

运行以下命令验证安装是否成功：

```bash
# 检查版本信息
python main.py --help

# 验证配置
python validate_config.py

# 运行测试（如果需要）
pytest tests/
```

## 配置

### 首次运行配置

1. 程序首次运行时会创建默认配置文件 `config.json`
2. 可以根据需要修改配置文件中的参数
3. 详细配置说明请参考 `CONFIG.md`

### 自定义配置

```bash
# 使用自定义配置文件
python main.py --config my_config.json

# 启用调试模式
python main.py --debug
```

## 故障排除

### 常见问题

1. **Python版本过低**
   ```
   错误: Python版本过低
   解决: 升级到Python 3.8或更高版本
   ```

2. **依赖模块缺失**
   ```
   错误: ModuleNotFoundError: No module named 'fitz'
   解决: 运行 pip install -r requirements.txt
   ```

3. **权限问题（Linux/macOS）**
   ```bash
   # 给可执行文件添加执行权限
   chmod +x pdf-invoice-layout
   ```

4. **macOS安全警告**
   - 右键点击应用程序，选择"打开"
   - 或在系统偏好设置中允许运行未签名的应用程序

### 日志文件

程序运行时会生成日志文件 `pdf_invoice_layout.log`，包含详细的运行信息和错误信息。

### 获取帮助

如果遇到问题，请：

1. 检查日志文件中的错误信息
2. 确认系统要求是否满足
3. 尝试重新安装依赖包
4. 使用调试模式运行程序获取更多信息

## 卸载

### 卸载预编译版本
直接删除程序文件夹即可。

### 卸载源代码版本
```bash
# 如果使用了虚拟环境
rm -rf venv

# 删除程序文件
rm -rf pdf-invoice-layout

# 删除配置文件（可选）
rm config.json
rm pdf_invoice_layout.log
```

## 更新

### 更新预编译版本
1. 下载新版本的安装包
2. 备份现有配置文件
3. 解压新版本覆盖旧版本
4. 恢复配置文件

### 更新源代码版本
```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 重新运行程序
python main.py
```

## 开发环境设置

如果需要参与开发或修改代码：

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install black mypy pytest-cov

# 运行代码格式化
black src/ tests/

# 运行类型检查
mypy src/

# 运行测试
pytest tests/ --cov=src

# 构建可执行文件
python build.py
```