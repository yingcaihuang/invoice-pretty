# GitHub Actions 快速参考

## 🚀 快速发布

### 方法1: 推送标签 (推荐)
```bash
# 创建版本标签
git tag v1.0.0
git push origin v1.0.0

# 或使用发布脚本
python release.py --interactive
```

### 方法2: 手动触发
1. GitHub → Actions → "Build and Release"
2. "Run workflow" → 输入版本号 → "Run workflow"

## 📦 构建产物

| 平台 | 文件 | 说明 |
|------|------|------|
| Windows | `*-windows.exe` | 单文件可执行程序 |
| Windows | `*-windows-portable.zip` | 便携版压缩包 |
| macOS Intel | `*-macos-intel.dmg` | Intel Mac安装包 |
| macOS ARM | `*-macos-arm64.dmg` | Apple Silicon安装包 |

## 🔧 本地测试

```bash
# 检查发布环境
python release.py --check

# 测试Windows构建
python release.py --test-build windows

# 测试macOS构建  
python release.py --test-build macos

# 列出现有版本
python release.py --list

# 生成更新日志
python release.py --changelog v1.0.0
```

## 📋 工作流状态

### 构建和发布工作流
- **触发**: 推送版本标签或手动触发
- **平台**: Windows, macOS Intel, macOS ARM
- **输出**: GitHub Release + 安装包

### 测试构建工作流  
- **触发**: 推送到main/develop分支
- **功能**: 代码测试 + 构建环境验证
- **平台**: Ubuntu, Windows, macOS

## 🛠️ 故障排除

### 构建失败
1. 检查构建日志
2. 验证依赖文件 (`requirements.txt`)
3. 测试本地构建环境

### 发布失败
1. 确认版本标签格式 (`v1.0.0`)
2. 检查GitHub Token权限
3. 验证工作流文件语法

### 文件缺失
1. 确认构建脚本存在
2. 检查文件路径配置
3. 验证构建产物生成

## 📊 监控

### 构建状态徽章
```markdown
![Build](https://github.com/username/repo/workflows/Build%20and%20Release/badge.svg)
![Test](https://github.com/username/repo/workflows/Test%20Build/badge.svg)
```

### 查看构建日志
GitHub → Actions → 选择工作流 → 查看作业详情

## 🔐 安全

- 使用GitHub Secrets存储敏感信息
- 代码签名证书配置 (可选)
- 最小权限原则

## 💡 最佳实践

1. **版本管理**: 使用语义化版本 (`v1.0.0`)
2. **测试优先**: 推送前运行本地测试
3. **文档更新**: 及时更新Release Notes
4. **监控构建**: 关注构建状态和日志
5. **备份重要**: 保留关键版本的构建产物