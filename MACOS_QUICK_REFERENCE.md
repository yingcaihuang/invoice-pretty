# macOS应用程序问题快速参考

## 🚨 应用程序立即退出？

### 🎯 一键解决（推荐）

```bash
make macos-solve
```

这个命令会自动：
- 检查环境
- 修复现有应用程序
- 构建新版本
- 提供详细指导

### 🔧 手动快速修复

```bash
# 1. 移除隔离标记
xattr -cr /Applications/PDF发票拼版打印系统*.app

# 2. 修复权限
chmod -R 755 /Applications/PDF发票拼版打印系统*.app

# 3. 右键点击应用程序，选择"打开"
```

### 🛠️ 构建新版本

按推荐顺序尝试：

```bash
# 最小化版本（最高兼容性）
make macos-minimal

# 简化版本
make macos-simple

# 终极调试版（显示详细错误）
make macos-debug-ultimate
```

## 📋 常见问题速查

| 问题现象 | 解决命令 |
|---------|---------|
| 应用程序立即退出 | `make macos-solve` |
| 提示"已损坏" | `xattr -cr /Applications/PDF发票拼版打印系统*.app` |
| 无法验证开发者 | 右键选择"打开" |
| 需要调试信息 | `make macos-debug-ultimate` |
| 权限问题 | `make macos-fix` |

## 🔍 诊断工具

```bash
# 故障排除工具
make macos-fix

# 终极调试版
make macos-debug-ultimate

# 检查构建环境
make macos-check
```

## 📁 文件位置

- **应用程序**: `/Applications/PDF发票拼版打印系统*.app`
- **调试日志**: `~/Desktop/pdf_invoice_*.log`
- **构建输出**: `./dist/`

## 🆘 紧急情况

如果所有方法都失败：

1. **收集信息**：
   ```bash
   sw_vers  # 系统版本
   python3 --version  # Python版本
   ```

2. **运行终极调试版**：
   ```bash
   make macos-debug-ultimate
   ```

3. **查看日志**：
   - 桌面上的调试日志文件
   - 控制台输出信息

4. **重新开始**：
   ```bash
   make clean
   make macos-minimal
   ```

## 💡 预防措施

- 使用最小化版本：`make macos-minimal`
- 定期运行故障排除：`make macos-fix`
- 保留调试版本以备不时之需

## 📞 技术支持

提供以下信息：
- 系统版本：`sw_vers`
- Python版本：`python3 --version`
- 错误日志文件
- 具体错误现象描述