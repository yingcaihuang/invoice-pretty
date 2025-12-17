# 📦 macOS打包方案总结

## 🎯 打包目标

将PDF发票拼版打印系统打包为macOS原生应用程序，支持：
- ✅ .app应用程序包
- ✅ .dmg安装镜像
- ✅ 文件关联（PDF、ZIP）
- ✅ 现代化界面
- ✅ 代码签名支持

## 🛠️ 构建工具

### 核心工具
- **PyInstaller**: Python应用程序打包
- **create-dmg**: DMG安装镜像创建
- **hdiutil**: macOS系统DMG工具（备选）

### 自动化脚本
1. `build_macos.py` - 完整的Python构建脚本
2. `build_simple.sh` - 简化的Shell脚本
3. `Makefile` - Make构建任务

## 📁 文件结构

```
项目根目录/
├── build_macos.py          # 主构建脚本
├── build_simple.sh         # 简化构建脚本
├── build.spec              # PyInstaller配置
├── Makefile                # Make任务定义
├── PACKAGING.md            # 详细打包文档
├── BUILD_QUICK_START.md    # 快速开始指南
└── dist/                   # 构建输出目录
    ├── PDF发票拼版打印系统.app
    └── PDF发票拼版打印系统-1.0.0.dmg
```

## 🚀 使用方法

### 方法1: 一键构建（推荐）
```bash
make macos-package
```

### 方法2: Python脚本
```bash
python3 build_macos.py
```

### 方法3: Shell脚本
```bash
./build_simple.sh
```

### 方法4: 分步构建
```bash
make macos-check    # 检查环境
make macos-clean    # 清理旧文件
make macos-app      # 构建应用
make macos-dmg      # 创建DMG
make macos-install  # 安装到系统
```

## 📋 构建流程

1. **环境检查** - 验证Python、PyInstaller等依赖
2. **清理构建** - 删除旧的构建文件和缓存
3. **应用构建** - 使用PyInstaller生成.app包
4. **代码签名** - 自动检测并应用代码签名
5. **DMG创建** - 生成安装镜像文件
6. **信息生成** - 创建应用程序信息文件

## 🎨 应用程序特性

### 基本信息
- **名称**: PDF发票拼版打印系统
- **Bundle ID**: com.pdfinvoicelayout.app
- **版本**: 1.0.0
- **最低系统**: macOS 10.14+

### 支持的文件类型
- PDF文档 (.pdf)
- ZIP压缩包 (.zip)

### 权限说明
- 文档文件夹访问
- 桌面文件夹访问
- 下载文件夹访问

## 🔧 自定义配置

### 修改应用信息
编辑 `build.spec` 文件：
```python
app = BUNDLE(
    coll,
    name='你的应用名称.app',
    bundle_identifier='com.yourcompany.yourapp',
    version='2.0.0',
    # ...
)
```

### 添加应用图标
1. 创建 `assets/app_icon.icns` 文件
2. 在 `build.spec` 中设置 `icon='assets/app_icon.icns'`

### 修改支持的文件类型
在 `build.spec` 的 `CFBundleDocumentTypes` 中添加新类型

## 📦 分发方式

### 方式1: 直接分发.app
- 压缩应用程序包
- 用户解压后拖拽到Applications

### 方式2: DMG安装镜像
- 专业的macOS安装体验
- 自动创建Applications链接
- 支持自定义背景和图标

### 方式3: 在线分发
- 上传到云存储服务
- 提供下载链接
- 包含安装说明

## 🛡️ 代码签名

### 开发者签名
```bash
# 查看可用证书
security find-identity -v -p codesigning

# 手动签名
codesign --force --sign "Developer ID" "dist/PDF发票拼版打印系统.app"
```

### 公证（Notarization）
```bash
# 上传公证
xcrun notarytool submit "app.zip" --keychain-profile "notary-profile"

# 装订公证票据
xcrun stapler staple "PDF发票拼版打印系统.app"
```

## 🔍 故障排除

### 常见问题
1. **tkinter错误**: `brew install python-tk`
2. **权限问题**: `xattr -cr "app.app"`
3. **构建失败**: `make macos-clean && make macos-package`
4. **DMG创建失败**: 检查create-dmg安装

### 调试技巧
```bash
# 详细构建日志
pyinstaller --log-level DEBUG build.spec

# 测试应用启动
./dist/PDF发票拼版打印系统.app/Contents/MacOS/PDF发票拼版打印系统

# 检查依赖
otool -L dist/PDF发票拼版打印系统.app/Contents/MacOS/PDF发票拼版打印系统
```

## 📊 构建统计

### 典型构建时间
- 首次构建: 2-5分钟
- 增量构建: 30秒-2分钟
- DMG创建: 10-30秒

### 文件大小
- .app包: ~50-100MB
- .dmg镜像: ~30-70MB
- 压缩后: ~20-40MB

## 🎉 完成检查清单

- [ ] 环境依赖已安装
- [ ] 构建脚本可执行
- [ ] 应用程序正常启动
- [ ] 文件关联正常工作
- [ ] DMG安装流程正常
- [ ] 代码签名完成（可选）
- [ ] 在不同macOS版本测试
- [ ] 准备分发材料

## 📚 相关文档

- [PACKAGING.md](PACKAGING.md) - 详细打包指南
- [BUILD_QUICK_START.md](BUILD_QUICK_START.md) - 快速开始
- [README.md](README.md) - 项目说明
- [CONFIG.md](CONFIG.md) - 配置说明

---

**提示**: 首次构建可能需要较长时间，因为PyInstaller需要分析和打包所有依赖项。后续构建会更快。