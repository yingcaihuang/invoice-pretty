# GitHub Actions 运行器更新说明

## 🔄 更新原因

GitHub Actions 发出弃用警告：
```
The macOS-13 based runner images are being deprecated, consider switching to macOS-15 (macos-15-intel) or macOS 15 arm64 (macos-latest) instead.
```

## 📋 更新内容

### macOS 运行器版本更新

| 用途 | 旧版本 | 新版本 | 说明 |
|------|--------|--------|------|
| Intel Mac 构建 | `macos-13` | `macos-15-intel` | 专用Intel运行器 |
| ARM Mac 构建 | `macos-latest` | `macos-latest` | 保持不变 (最新ARM运行器) |

### 具体变更

**构建和发布工作流** (`.github/workflows/build-and-release.yml`):

**之前**:
```yaml
build-macos-intel:
  runs-on: macos-13  # Intel-based runner
```

**现在**:
```yaml
build-macos-intel:
  runs-on: macos-15-intel  # Intel-based runner (updated from deprecated macos-13)
```

## ✅ 更新优势

### 1. 最新系统支持
- **macOS 15 Sequoia**: 最新的macOS版本
- **更新的开发工具**: 最新版本的Xcode和系统工具
- **更好的性能**: 优化的运行器性能

### 2. 长期支持
- **避免弃用**: 使用官方推荐的运行器版本
- **稳定性**: 更稳定的构建环境
- **兼容性**: 与最新GitHub Actions平台兼容

### 3. 架构明确性
- **Intel专用**: `macos-15-intel` 明确指定Intel架构
- **ARM专用**: `macos-latest` 使用最新ARM运行器
- **避免混淆**: 清晰的架构区分

## 🔧 技术影响

### 构建环境变化
- **macOS版本**: 13.x → 15.x
- **Xcode版本**: 可能更新到最新版本
- **系统工具**: 更新的系统工具和库

### 兼容性考虑
- **Python版本**: 继续支持Python 3.11
- **PyInstaller**: 兼容最新macOS版本
- **依赖库**: 所有依赖库应该正常工作

### 构建产物
- **二进制兼容性**: 生成的应用程序向后兼容
- **最低系统要求**: 可能需要更新最低macOS版本要求
- **性能优化**: 可能获得更好的性能优化

## 📦 预期结果

### 构建产物保持不变
- `PDF发票拼版打印系统-{version}-macos-intel.dmg`
- `PDF发票拼版打印系统-{version}-macos-arm64.dmg`

### 功能保持完整
- ✅ 智能模块导入修复
- ✅ 现代化用户界面
- ✅ PDF和ZIP文件处理
- ✅ 跨架构兼容性

## 🚀 验证步骤

### 1. 本地验证
```bash
# 检查工作流语法
python -c "
import yaml
with open('.github/workflows/build-and-release.yml') as f:
    config = yaml.safe_load(f)
    intel_runner = config['jobs']['build-macos-intel']['runs-on']
    arm_runner = config['jobs']['build-macos-arm']['runs-on']
    print(f'Intel runner: {intel_runner}')
    print(f'ARM runner: {arm_runner}')
    assert intel_runner == 'macos-15-intel', f'Expected macos-15-intel, got {intel_runner}'
    assert arm_runner == 'macos-latest', f'Expected macos-latest, got {arm_runner}'
    print('✅ 运行器配置正确')
"
```

### 2. GitHub Actions 测试
```bash
# 创建测试标签
git tag v1.0.0-runner-test
git push origin v1.0.0-runner-test
```

### 3. 监控构建日志
- 检查新运行器的启动时间
- 验证依赖安装过程
- 确认构建产物生成

## 📋 运行器对比

| 特性 | macos-13 | macos-15-intel | macos-latest (ARM) |
|------|----------|----------------|-------------------|
| 架构 | Intel x86_64 | Intel x86_64 | Apple Silicon ARM64 |
| macOS版本 | 13.x | 15.x | 15.x |
| 状态 | 即将弃用 | 当前推荐 | 当前推荐 |
| 性能 | 标准 | 优化 | 最佳 |

## 🔍 监控要点

### 1. 构建时间
- 新运行器可能有不同的性能特征
- 监控整体构建时间变化
- 关注依赖下载和安装速度

### 2. 兼容性
- 验证PyInstaller在新环境中的工作
- 检查生成的应用程序兼容性
- 确认DMG创建过程正常

### 3. 错误处理
- 关注新环境特有的错误信息
- 验证错误恢复机制
- 检查日志输出格式

## 💡 最佳实践

### 1. 渐进式更新
- ✅ 先更新Intel运行器
- 保持ARM运行器不变
- 逐步验证和优化

### 2. 监控和回滚
- 密切监控首次构建
- 准备回滚方案
- 记录性能基准

### 3. 文档更新
- 更新系统要求文档
- 修订构建指南
- 通知用户可能的变化

## 🆘 故障排除

### 如果构建失败
1. **检查运行器可用性**
   ```yaml
   # 临时回滚到旧版本
   runs-on: macos-13
   ```

2. **验证依赖兼容性**
   - 检查PyInstaller版本兼容性
   - 验证系统依赖可用性
   - 确认Python版本支持

3. **调试构建环境**
   - 添加环境信息输出
   - 检查系统工具版本
   - 验证路径和权限

### 如果性能下降
1. 检查缓存配置
2. 优化依赖安装
3. 调整并行构建设置

## 📈 预期改进

### 1. 性能提升
- 更快的运行器启动时间
- 优化的系统性能
- 更好的并行处理能力

### 2. 稳定性增强
- 更稳定的构建环境
- 减少随机构建失败
- 更好的错误恢复

### 3. 未来兼容性
- 支持最新的开发工具
- 兼容未来的macOS版本
- 长期维护保证

这次更新确保了GitHub Actions工作流使用最新推荐的运行器版本，避免了弃用警告，并为未来的构建提供了更好的基础。