# 📦 发布指南 - PDF发票拼版打印系统

## 🎯 发布文件说明

当你推送版本标签后，GitHub Actions会自动构建并发布以下文件到GitHub Release：

### Windows版本
- **`PDF发票拼版打印系统.exe`** - 单文件可执行程序，双击即可运行
- **`PDF发票拼版打印系统-便携版.zip`** - 绿色便携版，解压即用

### macOS版本  
- **`PDF发票拼版打印系统-intel.dmg`** - Intel Mac (x86_64) 安装包
- **`PDF发票拼版打印系统-arm64.dmg`** - Apple Silicon Mac (M1/M2) 安装包

## 🚀 发布步骤

### 方法1: 交互式发布 (推荐)
```bash
# 使用交互式发布工具
python release.py --interactive
```

这会引导你完成：
1. 检查发布环境
2. 显示当前版本和提交历史
3. 输入新版本号
4. 生成更新日志
5. 确认并推送标签

### 方法2: 手动发布
```bash
# 1. 确保所有更改已提交
git add .
git commit -m "准备发布 v1.1.0"
git push

# 2. 创建并推送版本标签
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### 方法3: GitHub界面手动触发
1. 访问GitHub仓库的Actions页面
2. 选择"Build and Release"工作流
3. 点击"Run workflow"
4. 输入版本号 (如: v1.1.0)
5. 点击"Run workflow"

## 📋 发布流程监控

### 1. GitHub Actions页面
推送标签后，访问仓库的Actions页面查看构建进度：
- `build-windows` - Windows EXE构建
- `build-macos-intel` - macOS Intel DMG构建  
- `build-macos-arm` - macOS ARM64 DMG构建
- `create-release` - 创建GitHub Release

### 2. 构建时间预估
- Windows构建: ~5-10分钟
- macOS Intel构建: ~10-15分钟
- macOS ARM64构建: ~10-15分钟
- 总时间: ~15-20分钟 (并行构建)

### 3. 发布完成标志
✅ 所有构建作业显示绿色勾号
✅ GitHub Releases页面出现新版本
✅ 所有4个文件都已上传到Release

## 🔍 发布前检查

### 环境检查
```bash
# 检查发布环境
python release.py --check

# 检查构建环境
python build_windows.py --check
```

### 必要文件检查
确保以下文件存在：
- ✅ `build_windows.py` - Windows构建脚本
- ✅ `build_import_fixed.py` - macOS构建脚本  
- ✅ `requirements.txt` - 依赖列表
- ✅ `.github/workflows/build-and-release.yml` - GitHub Actions配置

## 🎉 发布成功后

### 1. 验证Release
- 检查GitHub Releases页面
- 确认所有4个文件都已上传
- 验证Release Notes内容正确

### 2. 测试下载
- 下载并测试Windows EXE文件
- 下载并测试便携版ZIP文件
- 如有Mac设备，测试DMG安装包

### 3. 通知用户
- 更新README.md中的下载链接
- 发布更新公告
- 通知相关用户群体

## 🆘 故障排除

### 构建失败
1. 检查GitHub Actions运行日志
2. 确认所有依赖都在requirements.txt中
3. 验证构建脚本语法正确

### 文件上传失败
1. 检查文件路径是否正确
2. 确认GitHub Token权限
3. 验证文件大小是否超限

### Release创建失败
1. 检查标签格式 (必须是v开头，如v1.0.0)
2. 确认Release Notes格式正确
3. 验证仓库权限设置

## 📞 技术支持

如遇问题，请检查：
1. **GitHub Actions日志** - 详细的构建错误信息
2. **本地构建测试** - `python build_windows.py --check`
3. **相关文档**:
   - `WINDOWS_BUILD_FIX.md` - Windows构建问题
   - `GITHUB_ACTIONS_VERSION_UPDATE.md` - Actions版本更新
   - `GITHUB_ACTIONS_FINAL_STATUS.md` - 完整状态报告

---

**🎯 总结**: 推送版本标签后，GitHub Actions会自动构建Windows EXE、便携版ZIP、macOS Intel DMG和ARM64 DMG，并发布到GitHub Release。整个过程完全自动化，无需手动干预。