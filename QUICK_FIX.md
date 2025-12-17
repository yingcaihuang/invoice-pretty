# 快速修复指南 - DMG安装后应用立即退出

## 🚀 快速解决方案

### 方法1: 重新构建简化版（推荐）

```bash
# 构建简化版应用程序
make macos-simple
```

或者：

```bash
python3 build_simple_fixed.py
```

### 方法2: 修复已安装的应用程序

```bash
# 运行自动修复工具
make macos-fix
```

或者：

```bash
python3 fix_macos_app.py
```

### 方法3: 手动修复（如果自动修复失败）

```bash
# 移除隔离标记
xattr -cr /Applications/PDF发票拼版打印系统.app

# 修复权限
chmod -R 755 /Applications/PDF发票拼版打印系统.app
```

然后右键点击应用程序，选择"打开"。

## 🔍 问题诊断

如果应用程序仍然无法启动，运行调试工具：

1. 运行故障排除：`python3 fix_macos_app.py`
2. 查看桌面上的调试日志文件
3. 使用调试启动器获取详细错误信息

## 📋 常见错误及解决方案

| 错误现象 | 解决方案 |
|---------|---------|
| 应用程序立即退出 | 运行 `xattr -cr /Applications/PDF发票拼版打印系统.app` |
| 提示"已损坏" | 移除隔离标记，右键选择"打开" |
| 无法验证开发者 | 在系统偏好设置中允许运行 |
| 缺少权限 | 运行 `chmod -R 755 /Applications/PDF发票拼版打印系统.app` |

## 🛠️ 构建新版本

如果修复无效，重新构建：

```bash
# 清理旧文件
make clean

# 构建简化版（最稳定）
make macos-simple

# 或构建修复版（包含调试功能）
make macos-fixed
```

## 💡 预防措施

为避免类似问题：

1. 使用简化版构建：`make macos-simple`
2. 构建后立即测试：`make macos-fix`
3. 保留调试版本以便故障排除

## 📞 需要帮助？

如果问题仍然存在：

1. 运行 `python3 fix_macos_app.py`
2. 收集桌面上的调试日志
3. 提供系统版本信息：`sw_vers`