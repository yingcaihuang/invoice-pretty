# PDF发票拼版打印系统 Makefile
# 提供常用的开发和构建任务

.PHONY: help install test build clean run format lint validate

# 默认目标
help:
	@echo "PDF发票拼版打印系统 - 可用命令:"
	@echo ""
	@echo "基本命令:"
	@echo "  install        - 安装依赖"
	@echo "  test           - 运行测试"
	@echo "  build          - 构建可执行文件"
	@echo "  clean          - 清理构建文件"
	@echo "  run            - 运行程序"
	@echo "  format         - 格式化代码"
	@echo "  lint           - 代码检查"
	@echo "  validate       - 验证配置"
	@echo "  compat         - 兼容性测试"
	@echo ""
	@echo "macOS打包命令:"
	@echo "  macos-check    - 检查macOS构建环境"
	@echo "  macos-clean    - 清理macOS构建文件"
	@echo "  macos-app      - 构建macOS应用程序"
	@echo "  macos-dmg      - 创建DMG安装镜像"
	@echo "  macos-package  - 完整macOS打包流程"
	@echo "  macos-install  - 安装应用到系统"
	@echo "  macos-quick    - 快速构建和安装"
	@echo ""
	@echo "macOS问题修复:"
	@echo "  macos-fixed    - 构建修复版应用程序"
	@echo "  macos-simple   - 构建简化版应用程序"
	@echo "  macos-minimal  - 构建最小化版本（推荐）"
	@echo "  macos-debug-ultimate - 构建终极调试版"
	@echo "  macos-import-fix - 构建导入修复版（针对当前问题）"
	@echo "  macos-fix      - 故障排除工具"
	@echo "  macos-solve    - 一键解决所有问题（推荐）"
	@echo ""
	@echo "Windows打包命令:"
	@echo "  windows-check  - 检查Windows构建环境"
	@echo "  windows-clean  - 清理Windows构建文件"
	@echo "  windows-exe    - 构建Windows EXE文件"
	@echo "  windows-installer - 创建Windows安装程序"
	@echo "  windows-portable - 创建便携版"
	@echo "  windows-package - 完整Windows打包流程"
	@echo "  windows-quick  - 快速构建EXE文件"

# 安装依赖
install:
	python install.py

# 运行测试
test:
	pytest tests/ -v

# 构建可执行文件
build:
	python build.py

# 清理构建文件
clean:
	rm -rf build/ dist/ __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# 运行程序
run:
	python main.py

# 格式化代码
format:
	black src/ tests/ *.py

# 代码检查
lint:
	mypy src/
	black --check src/ tests/ *.py

# 验证配置
validate:
	python validate_config.py --verbose

# 兼容性测试
compat:
	python test_compatibility.py

# 完整测试（包括兼容性）
test-all: test compat validate
	@echo "所有测试完成"

# 开发环境设置
dev-setup: install
	pip install black mypy pytest-cov
	@echo "开发环境设置完成"

# 发布准备
release: clean format lint test build
	@echo "发布准备完成"

# macOS打包相关命令
.PHONY: macos-check macos-clean macos-app macos-dmg macos-package macos-install

# 检查macOS构建环境
macos-check:
	python3 build_macos.py check

# 清理macOS构建文件
macos-clean:
	python3 build_macos.py clean

# 构建macOS应用程序
macos-app:
	python3 build_macos.py app

# 创建DMG安装镜像
macos-dmg:
	python3 build_macos.py dmg

# 完整macOS打包流程
macos-package: macos-clean test
	python3 build_macos.py
	@echo "✅ macOS打包完成"

# 安装应用到系统
macos-install:
	@if [ -d "dist/PDF发票拼版打印系统.app" ]; then \
		cp -R "dist/PDF发票拼版打印系统.app" /Applications/; \
		echo "✅ 应用程序已安装到 /Applications/"; \
	else \
		echo "❌ 未找到应用程序包，请先运行 make macos-app"; \
	fi

# 快速构建和安装
macos-quick: macos-app macos-install
	@echo "✅ 快速构建和安装完成"

# 修复版macOS构建命令
.PHONY: macos-fixed macos-simple macos-fix

# 构建修复版macOS应用程序
macos-fixed:
	@echo "构建修复版macOS应用程序..."
	python3 build_macos_fixed.py

# 构建简化版macOS应用程序
macos-simple:
	@echo "构建简化版macOS应用程序..."
	python3 build_simple_fixed.py

# macOS应用程序故障排除
macos-fix:
	@echo "运行macOS应用程序故障排除..."
	python3 fix_macos_app.py

# 终极调试和最小化版本
.PHONY: macos-debug-ultimate macos-minimal

# 构建终极调试版（显示详细诊断信息）
macos-debug-ultimate:
	@echo "构建终极调试版macOS应用程序..."
	python3 build_debug_ultimate.py

# 构建最小化版本（最高兼容性）
macos-minimal:
	@echo "构建最小化版本macOS应用程序..."
	python3 build_minimal.py

# 一键解决所有问题
.PHONY: macos-solve macos-import-fix

macos-solve:
	@echo "一键解决macOS应用程序问题..."
	python3 solve_macos_issue.py

# 构建导入修复版（专门解决模块导入问题）
macos-import-fix:
	@echo "构建导入修复版macOS应用程序..."
	python3 build_import_fixed.py

# Windows构建相关命令
.PHONY: windows-check windows-clean windows-exe windows-installer windows-portable windows-package

# 检查Windows构建环境
windows-check:
	@echo "检查Windows构建环境..."
	python build_windows.py --check

# 清理Windows构建文件
windows-clean:
	@echo "清理Windows构建文件..."
	@if exist build rmdir /s /q build
	@if exist dist rmdir /s /q dist
	@echo "✅ Windows构建文件已清理"

# 构建Windows EXE文件
windows-exe:
	@echo "构建Windows EXE文件..."
	python build_windows.py

# 创建Windows安装程序
windows-installer:
	@echo "创建Windows安装程序..."
	python build_windows.py --installer-only

# 创建便携版
windows-portable:
	@echo "创建Windows便携版..."
	python build_windows.py --portable-only

# 完整Windows打包流程
windows-package: windows-clean
	@echo "完整Windows打包流程..."
	python build_windows.py
	@echo "✅ Windows打包完成"

# 快速Windows构建（仅EXE）
windows-quick:
	@echo "快速Windows构建..."
	python build_windows.py --exe-only