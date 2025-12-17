# macOS应用程序问题修复指南

## 问题描述

如果您遇到以下问题：
- DMG安装后应用程序立即退出
- 双击应用程序没有反应
- 应用程序启动后立即崩溃

## 解决方案

### 方案1: 使用简化版构建

```bash
# 构建简化版应用程序（推荐）
make macos-simple
```

简化版特点：
- 使用单文件模式，避免路径问题
- 最小化依赖，提高兼容性
- 包含详细的安装说明

### 方案2: 使用修复版构建

```bash
# 构建修复版应用程序
make macos-fixed
```

修复版特点：
- 包含调试版本
- 自动修复常见问题
- 提供详细的错误日志

### 方案3: 故障排除工具

如果应用程序已经安装但无法运行：

```bash
# 运行故障排除工具
make macos-fix
```

故障排除工具会：
- 诊断常见问题
- 自动修复权限问题
- 移除隔离标记
- 创建调试启动器

## 手动修复步骤

### 1. 移除隔离标记

```bash
# 移除应用程序的隔离标记
xattr -cr /Applications/PDF发票拼版打印系统.app
```

### 2. 修复权限

```bash
# 修复应用程序权限
chmod -R 755 /Applications/PDF发票拼版打印系统.app
chmod +x /Applications/PDF发票拼版打印系统.app/Contents/MacOS/PDF发票拼版打印系统
```

### 3. 首次运行

1. 右键点击应用程序
2. 选择"打开"
3. 在安全提示中点击"打开"

## 常见问题

### Q: 应用程序显示"已损坏"

**A:** 这通常是隔离标记导致的，运行以下命令：
```bash
xattr -cr /Applications/PDF发票拼版打印系统.app
```

### Q: 提示"无法验证开发者"

**A:** 
1. 打开"系统偏好设置" > "安全性与隐私"
2. 在"通用"标签页中，点击"仍要打开"
3. 或者运行：`spctl --add /Applications/PDF发票拼版打印系统.app`

### Q: 应用程序启动后立即退出

**A:** 
1. 使用故障排除工具：`make macos-fix`
2. 查看生成的调试日志
3. 尝试简化版构建：`make macos-simple`

### Q: 缺少依赖库

**A:** 
1. 确保系统版本为macOS 10.14或更高
2. 安装Xcode命令行工具：`xcode-select --install`
3. 使用简化版构建，包含所有必要依赖

## 构建环境要求

- macOS 10.14或更高版本
- Python 3.8或更高版本
- PyInstaller: `pip install pyinstaller`
- 可选：create-dmg: `brew install create-dmg`

## 调试信息

如果问题仍然存在，请收集以下信息：

1. **系统信息**：
   ```bash
   sw_vers
   ```

2. **Python版本**：
   ```bash
   python3 --version
   ```

3. **应用程序信息**：
   ```bash
   ls -la /Applications/PDF发票拼版打印系统.app/Contents/MacOS/
   xattr -l /Applications/PDF发票拼版打印系统.app
   ```

4. **运行调试启动器**：
   - 运行桌面上的 `debug_pdf_invoice.sh`
   - 查看生成的 `pdf_invoice_debug.log`

## 技术支持

如果以上方法都无法解决问题，请提供：
- 系统版本信息
- 错误日志文件
- 具体的错误现象描述

## 构建脚本说明

### build_simple_fixed.py
- 最简单的构建方式
- 单文件模式，兼容性最好
- 适合大多数用户

### build_macos_fixed.py
- 完整的修复版本
- 包含调试功能
- 适合开发者和高级用户

### fix_macos_app.py
- 故障排除工具
- 自动诊断和修复
- 适合已安装应用程序的问题修复