# Windows构建指南

## 🎯 概述

本指南介绍如何在Windows系统上构建PDF发票拼版打印系统的可执行文件。

## 📋 系统要求

### 必需软件
- **Windows 7/8/10/11** (64位推荐)
- **Python 3.8+** 
- **PyInstaller** (自动安装)

### 可选软件 (用于创建安装程序)
- **NSIS** - 创建Windows安装程序
- **Inno Setup** - 创建Windows安装程序

## 🚀 快速开始

### 方法1: 使用批处理文件 (推荐)

```batch
# 双击运行或在命令行执行
build_windows.bat
```

### 方法2: 使用Python脚本

```bash
# 完整构建流程
python build_windows.py

# 或使用Makefile (需要安装make)
make windows-package
```

### 方法3: 使用Makefile命令

```bash
# 检查构建环境
make windows-check

# 快速构建EXE
make windows-quick

# 完整打包流程
make windows-package
```

## 📦 构建选项

### 1. 基础EXE文件
- **文件**: `dist/PDF发票拼版打印系统.exe`
- **特点**: 单文件，无需安装，双击运行
- **大小**: 约50-80MB
- **适用**: 个人使用，快速部署

### 2. Windows安装程序
- **文件**: `dist/PDF发票拼版打印系统-安装程序.exe`
- **特点**: 标准Windows安装程序
- **功能**: 
  - 安装到Program Files
  - 创建开始菜单快捷方式
  - 创建桌面快捷方式
  - 支持卸载
- **适用**: 正式部署，企业环境

### 3. 便携版
- **文件**: `dist/PDF发票拼版打印系统-便携版.zip`
- **特点**: 绿色软件，解压即用
- **包含**: EXE文件 + 使用说明
- **适用**: 移动使用，无管理员权限环境

## 🔧 构建过程详解

### 环境检查
脚本会自动检查：
- ✅ Python版本 (需要3.8+)
- ✅ PyInstaller安装状态
- ✅ 必要依赖包 (tkinter, PIL, PyMuPDF)
- ✅ 可选工具 (NSIS, Inno Setup)

### 构建步骤
1. **清理旧文件** - 删除之前的构建结果
2. **准备资源** - 检查图标文件等资源
3. **PyInstaller打包** - 创建单文件EXE
4. **创建安装程序** - 使用NSIS或Inno Setup
5. **制作便携版** - 创建ZIP压缩包

### PyInstaller配置
```python
# 主要配置选项
--onefile          # 单文件模式
--windowed         # 无控制台窗口
--add-data         # 添加数据文件
--hidden-import    # 添加隐藏导入
--icon             # 设置图标
```

## 🛠️ 高级配置

### 自定义图标
将图标文件放在以下位置之一：
- `assets/icon.ico`
- `assets/app_icon.ico`
- `icon.ico`

### 修改构建参数
编辑 `build_windows.py` 文件中的构建命令：

```python
cmd = [
    'pyinstaller',
    '--onefile',        # 改为 --onedir 创建目录版本
    '--windowed',       # 删除此行显示控制台
    # ... 其他参数
]
```

### 添加文件关联
在安装程序脚本中添加文件关联：

```nsis
; 注册PDF文件关联
WriteRegStr HKCR ".pdf" "" "PDFInvoiceLayout.PDF"
WriteRegStr HKCR "PDFInvoiceLayout.PDF" "" "PDF发票文件"
WriteRegStr HKCR "PDFInvoiceLayout.PDF\shell\open\command" "" '"$INSTDIR\PDF发票拼版打印系统.exe" "%1"'
```

## 🐛 常见问题

### 1. PyInstaller导入错误
**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**: 添加隐藏导入
```python
'--hidden-import', 'missing_module_name'
```

### 2. 文件过大
**问题**: EXE文件太大 (>100MB)

**解决**: 
- 使用 `--onedir` 模式
- 排除不必要的模块
- 使用UPX压缩

### 3. 启动缓慢
**问题**: 程序启动需要很长时间

**解决**:
- 使用 `--onedir` 模式
- 减少隐藏导入
- 优化代码导入

### 4. 杀毒软件误报
**问题**: 杀毒软件报告病毒

**解决**:
- 使用代码签名证书
- 提交到杀毒软件厂商白名单
- 使用官方Python打包

## 📊 性能优化

### 减小文件大小
```python
# 排除不需要的模块
--exclude-module matplotlib
--exclude-module numpy
--exclude-module pandas
```

### 加快启动速度
```python
# 使用目录模式
--onedir

# 启用优化
--optimize 2
```

### UPX压缩 (可选)
```bash
# 安装UPX
# 下载: https://upx.github.io/

# 压缩EXE
upx --best dist/PDF发票拼版打印系统.exe
```

## 🔐 代码签名 (可选)

如果有代码签名证书，可以对EXE文件进行签名：

```batch
# 使用signtool签名
signtool sign /f certificate.p12 /p password /t http://timestamp.digicert.com dist/PDF发票拼版打印系统.exe
```

## 📋 构建清单

构建完成后，检查以下文件：

- [ ] `dist/PDF发票拼版打印系统.exe` - 主程序
- [ ] `dist/PDF发票拼版打印系统-安装程序.exe` - 安装程序 (可选)
- [ ] `dist/PDF发票拼版打印系统-便携版.zip` - 便携版
- [ ] `dist/PDF发票拼版打印系统-便携版/` - 便携版目录

## 🎉 分发建议

### 个人用户
- 推荐使用 **便携版ZIP** 
- 解压后直接运行，无需安装

### 企业部署
- 推荐使用 **安装程序**
- 支持静默安装: `/S` 参数
- 集成到软件分发系统

### 开发测试
- 推荐使用 **单文件EXE**
- 快速部署，便于测试

## 💡 提示

1. **首次构建** 可能需要较长时间下载依赖
2. **虚拟环境** 可以减少不必要的依赖打包
3. **定期更新** PyInstaller到最新版本
4. **测试运行** 在干净的Windows系统上测试
5. **备份构建** 保存成功的构建配置

## 🆘 获取帮助

如果遇到问题：

1. 查看构建日志输出
2. 检查 `build/` 目录中的警告文件
3. 在干净环境中重新构建
4. 参考PyInstaller官方文档