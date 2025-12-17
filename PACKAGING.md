# macOS应用程序打包指南

本文档详细说明如何将PDF发票拼版打印系统打包为macOS应用程序。

## 📋 目录

- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [打包选项](#打包选项)
- [故障排除](#故障排除)
- [分发说明](#分发说明)

## 🚀 快速开始

### 方法1: 使用自动化脚本（推荐）

```bash
# 简单构建
./build_simple.sh

# 或使用Python脚本（功能更全）
python3 build_macos.py
```

### 方法2: 手动构建

```bash
# 1. 安装依赖
pip3 install pyinstaller

# 2. 构建应用程序
pyinstaller build.spec --clean --noconfirm

# 3. 查看结果
open dist/
```

## 📖 详细步骤

### 1. 环境准备

#### 系统要求
- macOS 10.14+ (Mojave或更高版本)
- Python 3.8+
- Xcode Command Line Tools

#### 安装构建工具

```bash
# 安装PyInstaller
pip3 install pyinstaller

# 安装DMG创建工具（可选）
brew install create-dmg

# 验证安装
pyinstaller --version
```

### 2. 项目准备

#### 检查依赖
```bash
# 运行兼容性测试
python3 test_compatibility.py

# 运行项目测试
python3 -m pytest tests/ -v
```

#### 清理项目
```bash
# 清理缓存文件
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# 清理旧的构建文件
rm -rf build/ dist/ *.spec
```

### 3. 构建配置

#### PyInstaller配置文件 (build.spec)

项目已包含预配置的`build.spec`文件，主要配置包括：

- **应用程序名称**: PDF发票拼版打印系统
- **Bundle ID**: com.pdfinvoicelayout.app
- **版本**: 1.0.0
- **图标**: 自动生成或使用默认图标
- **数据文件**: 配置文件、说明文档等

#### 自定义配置

如需修改配置，编辑`build.spec`文件：

```python
# 修改应用程序信息
app = BUNDLE(
    exe,
    name='你的应用名称.app',
    bundle_identifier='com.yourcompany.yourapp',
    version='1.0.0',
    # ... 其他配置
)
```

### 4. 执行构建

#### 选项A: 使用自动化脚本

```bash
# 完整构建（推荐）
python3 build_macos.py

# 仅构建应用程序
python3 build_macos.py app

# 仅创建DMG
python3 build_macos.py dmg

# 清理构建文件
python3 build_macos.py clean
```

#### 选项B: 使用Shell脚本

```bash
# 一键构建
./build_simple.sh
```

#### 选项C: 手动构建

```bash
# 使用PyInstaller
pyinstaller build.spec --clean --noconfirm

# 或使用自定义参数
pyinstaller \
    --name "PDF发票拼版打印系统" \
    --windowed \
    --onedir \
    --osx-bundle-identifier com.pdfinvoicelayout.app \
    main.py
```

## 🎛️ 打包选项

### 构建模式

| 模式 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| `--onefile` | 单文件模式 | 分发简单 | 启动较慢，体积较大 |
| `--onedir` | 目录模式 | 启动快速 | 文件较多 |

### 优化选项

```bash
# 启用UPX压缩（减小体积）
pyinstaller --upx-dir /usr/local/bin build.spec

# 排除不需要的模块
pyinstaller --exclude-module matplotlib build.spec

# 添加图标
pyinstaller --icon assets/app_icon.icns build.spec
```

### 代码签名

```bash
# 查看可用的签名身份
security find-identity -v -p codesigning

# 签名应用程序
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/PDF发票拼版打印系统.app"

# 验证签名
codesign --verify --deep --strict --verbose=2 "dist/PDF发票拼版打印系统.app"
```

## 🔧 故障排除

### 常见问题

#### 1. tkinter导入错误
```
ModuleNotFoundError: No module named '_tkinter'
```

**解决方案:**
```bash
# 重新安装Python（包含tkinter）
brew install python-tk

# 或使用pyenv安装完整Python
pyenv install 3.11.0
```

#### 2. PyMuPDF导入错误
```
ImportError: No module named 'fitz'
```

**解决方案:**
```bash
pip3 install PyMuPDF
```

#### 3. 应用程序无法启动
```
"PDF发票拼版打印系统.app" is damaged and can't be opened
```

**解决方案:**
```bash
# 移除隔离属性
xattr -cr "dist/PDF发票拼版打印系统.app"

# 或在系统偏好设置中允许运行
```

#### 4. 构建体积过大

**解决方案:**
```bash
# 排除不需要的模块
pyinstaller --exclude-module numpy --exclude-module scipy build.spec

# 启用UPX压缩
pyinstaller --upx-dir /usr/local/bin build.spec
```

### 调试技巧

```bash
# 启用详细输出
pyinstaller --log-level DEBUG build.spec

# 保留构建目录
pyinstaller --debug build.spec

# 测试导入
python3 -c "import sys; sys.path.insert(0, 'src'); import main"
```

## 📦 分发说明

### 文件结构

构建完成后，`dist/`目录包含：

```
dist/
├── PDF发票拼版打印系统.app/          # macOS应用程序包
├── PDF发票拼版打印系统-1.0.0.dmg     # DMG安装镜像（可选）
└── app_info.json                    # 应用程序信息
```

### 安装方式

#### 方式1: 直接运行
```bash
# 双击应用程序
open "dist/PDF发票拼版打印系统.app"
```

#### 方式2: 安装到Applications
```bash
# 拖拽到Applications文件夹
cp -R "dist/PDF发票拼版打印系统.app" /Applications/
```

#### 方式3: 使用DMG安装
1. 双击DMG文件
2. 将应用程序拖拽到Applications文件夹
3. 弹出DMG镜像

### 系统要求

- **操作系统**: macOS 10.14+ (Mojave或更高版本)
- **架构**: Intel x86_64 或 Apple Silicon (M1/M2)
- **内存**: 512MB+ (推荐2GB+)
- **磁盘空间**: 100MB+

### 权限说明

应用程序需要以下权限：
- **文件访问**: 读取PDF文件和ZIP压缩包
- **文件写入**: 保存生成的拼版PDF文件
- **网络**: 无需网络权限

## 🔄 自动化构建

### GitHub Actions

创建`.github/workflows/build-macos.yml`：

```yaml
name: Build macOS App

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build app
      run: python3 build_macos.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: macos-app
        path: dist/
```

### 本地自动化

创建`Makefile`：

```makefile
.PHONY: build clean test package

build:
	python3 build_macos.py

clean:
	python3 build_macos.py clean

test:
	python3 -m pytest tests/ -v

package: clean test build
	@echo "✅ 打包完成"

install:
	cp -R "dist/PDF发票拼版打印系统.app" /Applications/
```

使用方法：
```bash
make package  # 完整打包流程
make build    # 仅构建
make clean    # 清理
make install  # 安装到系统
```

## 📚 参考资源

- [PyInstaller官方文档](https://pyinstaller.readthedocs.io/)
- [macOS应用程序打包指南](https://developer.apple.com/documentation/xcode/distributing_your_app_for_beta_testing_and_releases)
- [代码签名指南](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

## 🆘 获取帮助

如果遇到问题：

1. 查看[故障排除](#故障排除)部分
2. 运行`python3 test_compatibility.py`检查环境
3. 查看PyInstaller日志文件
4. 在项目Issues中搜索相关问题

---

**注意**: 首次运行可能需要较长时间，因为PyInstaller需要分析和打包所有依赖项。后续构建会更快。