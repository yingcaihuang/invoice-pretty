# Windows构建快速参考

## 🚀 一键构建

```batch
# 最简单的方式 - 双击运行
build_windows.bat

# 或者命令行
python build_windows.py
```

## 📋 常用命令

### 基础命令
```bash
# 检查环境
python build_windows.py --check

# 仅构建EXE
python build_windows.py --exe-only

# 完整构建
python build_windows.py
```

### Makefile命令 (需要安装make)
```bash
# 快速构建
make windows-quick

# 完整打包
make windows-package

# 清理文件
make windows-clean
```

## 📦 输出文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `PDF发票拼版打印系统.exe` | 单文件可执行程序 | 个人使用 |
| `PDF发票拼版打印系统-安装程序.exe` | Windows安装程序 | 正式部署 |
| `PDF发票拼版打印系统-便携版.zip` | 便携版压缩包 | 分发使用 |

## 🔧 构建选项

```bash
# 仅检查环境
python build_windows.py --check

# 仅构建EXE
python build_windows.py --exe-only

# 仅创建安装程序 (需要先有EXE)
python build_windows.py --installer-only

# 仅创建便携版 (需要先有EXE)
python build_windows.py --portable-only

# 不清理旧文件
python build_windows.py --no-clean
```

## ⚡ 快速故障排除

### 问题1: Python未找到
```bash
# 解决方案
1. 安装Python 3.8+
2. 添加Python到系统PATH
3. 重启命令行
```

### 问题2: PyInstaller未安装
```bash
# 解决方案
pip install pyinstaller
```

### 问题3: 模块导入错误
```bash
# 解决方案
pip install -r requirements.txt
```

### 问题4: 构建失败
```bash
# 解决方案
1. 清理旧文件: python build_windows.py --clean
2. 检查环境: python build_windows.py --check
3. 重新构建: python build_windows.py
```

## 📊 文件大小参考

| 版本 | 大小 | 说明 |
|------|------|------|
| 单文件EXE | 50-80MB | 包含所有依赖 |
| 安装程序 | 55-85MB | 包含EXE+安装逻辑 |
| 便携版ZIP | 45-75MB | 压缩后的便携版 |

## 🎯 使用建议

### 开发测试
- 使用 `--exe-only` 快速构建
- 文件小，构建快

### 个人使用
- 使用便携版ZIP
- 绿色软件，无需安装

### 企业部署
- 使用安装程序
- 标准化部署流程

## 💡 优化提示

1. **虚拟环境**: 使用venv减少依赖
2. **清理缓存**: 定期清理build目录
3. **更新工具**: 保持PyInstaller最新版本
4. **测试环境**: 在干净系统上测试

## 🔗 相关文件

- `build_windows.py` - 主构建脚本
- `build_windows.bat` - Windows批处理文件
- `WINDOWS_BUILD_GUIDE.md` - 详细构建指南
- `Makefile` - Make构建配置