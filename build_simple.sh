#!/bin/bash
# 简单的macOS应用程序构建脚本

set -e

APP_NAME="PDF发票拼版打印系统"
VERSION="1.0.0"
BUNDLE_ID="com.pdfinvoicelayout.app"

echo "🚀 开始构建 $APP_NAME"
echo "=================================="

# 检查是否在macOS上运行
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此脚本只能在macOS上运行"
    exit 1
fi

# 检查Python和PyInstaller
echo "🔍 检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3"
    exit 1
fi

if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "📦 安装PyInstaller..."
    pip3 install pyinstaller
fi

# 清理旧的构建文件
echo "🧹 清理构建目录..."
rm -rf build dist *.spec

# 创建PyInstaller规格文件
echo "📝 创建构建配置..."
cat > app.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'fitz',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.distutils',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)

app = BUNDLE(
    coll,
    name='$APP_NAME.app',
    icon=None,
    bundle_identifier='$BUNDLE_ID',
    version='$VERSION',
    info_plist={
        'CFBundleName': '$APP_NAME',
        'CFBundleDisplayName': '$APP_NAME',
        'CFBundleVersion': '$VERSION',
        'CFBundleShortVersionString': '$VERSION',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
EOF

# 构建应用程序
echo "🔨 构建应用程序..."
pyinstaller app.spec --clean --noconfirm

# 检查构建结果
if [ -d "dist/$APP_NAME.app" ]; then
    echo "✅ 应用程序构建成功!"
    echo "📁 应用程序位置: dist/$APP_NAME.app"
    
    # 获取应用程序大小
    APP_SIZE=$(du -sh "dist/$APP_NAME.app" | cut -f1)
    echo "📏 应用程序大小: $APP_SIZE"
    
    # 创建DMG（如果可能）
    echo "📦 创建DMG安装包..."
    if command -v create-dmg &> /dev/null; then
        create-dmg \
            --volname "$APP_NAME $VERSION" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "$APP_NAME.app" 175 120 \
            --hide-extension "$APP_NAME.app" \
            --app-drop-link 425 120 \
            "dist/$APP_NAME-$VERSION.dmg" \
            "dist/$APP_NAME.app"
        
        if [ -f "dist/$APP_NAME-$VERSION.dmg" ]; then
            DMG_SIZE=$(du -sh "dist/$APP_NAME-$VERSION.dmg" | cut -f1)
            echo "✅ DMG创建成功: dist/$APP_NAME-$VERSION.dmg ($DMG_SIZE)"
        fi
    else
        echo "⚠️  create-dmg未安装，跳过DMG创建"
        echo "   安装方法: brew install create-dmg"
        
        # 使用hdiutil创建简单DMG
        echo "📦 使用hdiutil创建简单DMG..."
        mkdir -p "dist/dmg_temp"
        cp -R "dist/$APP_NAME.app" "dist/dmg_temp/"
        ln -s /Applications "dist/dmg_temp/Applications"
        
        hdiutil create -volname "$APP_NAME $VERSION" \
            -srcfolder "dist/dmg_temp" \
            -ov -format UDZO \
            "dist/$APP_NAME-$VERSION.dmg"
        
        rm -rf "dist/dmg_temp"
        
        if [ -f "dist/$APP_NAME-$VERSION.dmg" ]; then
            DMG_SIZE=$(du -sh "dist/$APP_NAME-$VERSION.dmg" | cut -f1)
            echo "✅ 简单DMG创建成功: dist/$APP_NAME-$VERSION.dmg ($DMG_SIZE)"
        fi
    fi
    
    echo ""
    echo "🎉 构建完成!"
    echo "=================================="
    echo "📁 输出文件:"
    ls -la dist/ | grep -E "\.(app|dmg)$" | awk '{print "   " $9 " (" $5 " bytes)"}'
    echo ""
    echo "📋 安装说明:"
    echo "   1. 双击 $APP_NAME.app 直接运行"
    echo "   2. 或将 $APP_NAME.app 拖拽到 Applications 文件夹"
    echo "   3. 如果有DMG文件，双击DMG文件进行安装"
    
else
    echo "❌ 应用程序构建失败"
    exit 1
fi