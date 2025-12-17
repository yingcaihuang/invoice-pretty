# 🚀 macOS打包快速开始

## 一键构建

```bash
# 方法1: 使用Python脚本（推荐）
python3 build_macos.py

# 方法2: 使用Shell脚本
./build_simple.sh

# 方法3: 手动构建
pyinstaller build.spec --clean --noconfirm
```

## 构建要求

- macOS 10.14+
- Python 3.8+
- PyInstaller (`pip3 install pyinstaller`)
- create-dmg (`brew install create-dmg`) - 可选

## 输出文件

构建完成后，在`dist/`目录中会生成：

- `PDF发票拼版打印系统.app` - macOS应用程序包
- `PDF发票拼版打印系统-1.0.0.dmg` - DMG安装镜像（如果create-dmg可用）

## 安装方式

### 方式1: 直接运行
```bash
open "dist/PDF发票拼版打印系统.app"
```

### 方式2: 安装到Applications
```bash
cp -R "dist/PDF发票拼版打印系统.app" /Applications/
```

### 方式3: 使用DMG
双击DMG文件，将应用拖拽到Applications文件夹

## 常见问题

### tkinter错误
```bash
# 安装tkinter支持
brew install python-tk
```

### 权限问题
```bash
# 移除隔离属性
xattr -cr "dist/PDF发票拼版打印系统.app"
```

### 构建失败
```bash
# 清理后重新构建
python3 build_macos.py clean
python3 build_macos.py
```

## 分步构建

```bash
# 1. 检查依赖
python3 build_macos.py check

# 2. 清理旧文件
python3 build_macos.py clean

# 3. 构建应用
python3 build_macos.py app

# 4. 创建DMG
python3 build_macos.py dmg
```

## 自定义配置

编辑`build.spec`文件来自定义：
- 应用程序名称
- Bundle ID
- 版本号
- 图标
- 支持的文件类型

详细说明请参考 [PACKAGING.md](PACKAGING.md)