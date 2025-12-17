# GitHub Actions 自动构建和发布指南

## 🎯 概述

本项目配置了完整的GitHub Actions工作流，支持自动构建和发布Windows、macOS (Intel和ARM)的安装包。

## 📁 工作流文件

### 1. 构建和发布工作流 (`.github/workflows/build-and-release.yml`)
- **触发条件**: 推送版本标签 (如 `v1.0.0`) 或手动触发
- **功能**: 构建所有平台的安装包并创建GitHub Release

### 2. 测试构建工作流 (`.github/workflows/test-build.yml`)
- **触发条件**: 推送到main/develop分支或Pull Request
- **功能**: 测试代码质量和构建环境

## 🚀 使用方法

### 自动发布新版本

#### 方法1: 推送版本标签 (推荐)
```bash
# 创建并推送版本标签
git tag v1.0.0
git push origin v1.0.0
```

#### 方法2: 手动触发
1. 进入GitHub仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build and Release" 工作流
4. 点击 "Run workflow"
5. 输入版本号 (如 `v1.0.0`)
6. 点击 "Run workflow" 按钮

### 测试构建

每次推送代码到main或develop分支时，会自动运行测试构建工作流。

## 📦 构建产物

### Windows
- **PDF发票拼版打印系统-{version}-windows.exe** - 单文件可执行程序
- **PDF发票拼版打印系统-{version}-windows-portable.zip** - 便携版压缩包

### macOS
- **PDF发票拼版打印系统-{version}-macos-intel.dmg** - Intel Mac安装包
- **PDF发票拼版打印系统-{version}-macos-arm64.dmg** - Apple Silicon Mac安装包

## 🔧 工作流详解

### 构建矩阵

| 平台 | 运行器 | 架构 | Python版本 |
|------|--------|------|------------|
| Windows | `windows-latest` | x64 | 3.11 |
| macOS Intel | `macos-13` | x86_64 | 3.11 |
| macOS ARM | `macos-latest` | arm64 | 3.11 |

### 构建步骤

#### Windows构建
1. **环境准备** - 设置Python 3.11环境
2. **依赖安装** - 安装requirements.txt中的依赖
3. **EXE构建** - 使用PyInstaller创建单文件EXE
4. **便携版** - 创建ZIP便携版包
5. **上传产物** - 保存构建结果

#### macOS构建 (Intel/ARM)
1. **环境准备** - 设置Python 3.11环境
2. **系统依赖** - 安装create-dmg工具
3. **Python依赖** - 安装requirements.txt中的依赖
4. **APP构建** - 使用PyInstaller创建.app包
5. **DMG创建** - 生成macOS安装镜像
6. **架构标记** - 重命名文件以区分Intel/ARM版本
7. **上传产物** - 保存构建结果

#### 发布流程
1. **下载产物** - 获取所有平台的构建结果
2. **版本获取** - 从标签或输入获取版本号
3. **发布说明** - 自动生成详细的Release Notes
4. **创建Release** - 在GitHub上创建新的Release
5. **上传文件** - 将所有安装包上传到Release

## 🛠️ 自定义配置

### 修改Python版本
编辑工作流文件中的环境变量：
```yaml
env:
  PYTHON_VERSION: '3.11'  # 修改为所需版本
```

### 添加新平台
在构建矩阵中添加新的运行器：
```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        platform: linux
```

### 自定义构建脚本
修改构建步骤中的命令：
```yaml
- name: Build Windows EXE
  run: |
    python build_windows.py --custom-options
```

## 📋 环境要求

### GitHub仓库设置
- 确保仓库有Actions权限
- 确保GITHUB_TOKEN有创建Release的权限

### 依赖文件
- `requirements.txt` - Python依赖列表
- `build_windows.py` - Windows构建脚本
- `build_macos.py` - macOS构建脚本

## 🔍 监控和调试

### 查看构建日志
1. 进入GitHub仓库的Actions页面
2. 选择对应的工作流运行
3. 点击具体的作业查看详细日志

### 常见问题

#### 1. 构建失败
- 检查依赖是否正确安装
- 查看构建日志中的错误信息
- 确认构建脚本是否正常工作

#### 2. 文件上传失败
- 检查文件路径是否正确
- 确认文件是否成功生成
- 验证GitHub Token权限

#### 3. Release创建失败
- 确认版本标签格式正确
- 检查是否有重复的Release
- 验证仓库权限设置

## 🚦 状态徽章

在README.md中添加构建状态徽章：

```markdown
![Build Status](https://github.com/your-username/your-repo/workflows/Build%20and%20Release/badge.svg)
![Test Status](https://github.com/your-username/your-repo/workflows/Test%20Build/badge.svg)
```

## 📈 性能优化

### 缓存策略
- **pip缓存** - 缓存Python包下载
- **构建缓存** - 缓存PyInstaller构建结果

### 并行构建
- 所有平台同时构建，提高效率
- 使用GitHub Actions的并行作业功能

### 资源限制
- 每个作业最多运行6小时
- 每月有免费的构建时间配额
- 私有仓库可能有不同的限制

## 🔐 安全考虑

### 代码签名
- Windows: 可配置代码签名证书
- macOS: 支持开发者证书签名

### 密钥管理
- 使用GitHub Secrets存储敏感信息
- 不在日志中暴露密钥信息

### 权限控制
- 最小权限原则
- 仅授予必要的仓库权限

## 📚 参考资料

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyInstaller 文档](https://pyinstaller.readthedocs.io/)
- [create-dmg 工具](https://github.com/sindresorhus/create-dmg)

## 💡 最佳实践

1. **版本管理** - 使用语义化版本号
2. **测试优先** - 在发布前进行充分测试
3. **文档更新** - 及时更新Release Notes
4. **监控构建** - 定期检查构建状态
5. **备份策略** - 保留重要版本的构建产物