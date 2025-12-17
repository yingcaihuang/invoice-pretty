#!/usr/bin/env python3
"""
PDF发票拼版打印系统 - 最小化版本
使用最简单的启动方式
"""

import sys
import os
from pathlib import Path

# 确保正确的工作目录
if getattr(sys, 'frozen', False):
    # PyInstaller环境
    app_dir = Path(sys.executable).parent
    os.chdir(app_dir)

def main():
    """主函数"""
    try:
        # 直接启动GUI
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建简单的启动窗口
        root = tk.Tk()
        root.title("PDF发票拼版打印系统")
        root.geometry("400x300")
        
        # 添加启动按钮
        def start_app():
            try:
                root.destroy()
                # 导入并启动真正的应用程序
                sys.path.insert(0, str(Path(__file__).parent))
                from main_app import start_gui_app
                start_gui_app()
            except Exception as e:
                messagebox.showerror("启动错误", f"应用程序启动失败:\n{e}")
        
        # 创建界面
        tk.Label(root, text="PDF发票拼版打印系统", font=("Arial", 16)).pack(pady=20)
        tk.Label(root, text="智能处理12306电子发票", font=("Arial", 12)).pack(pady=10)
        tk.Button(root, text="启动应用程序", command=start_app, font=("Arial", 14)).pack(pady=20)
        
        # 添加测试按钮
        def test_modules():
            try:
                import fitz
                import PIL
                messagebox.showinfo("测试结果", "所有模块导入成功！")
            except Exception as e:
                messagebox.showerror("测试结果", f"模块导入失败:\n{e}")
        
        tk.Button(root, text="测试模块", command=test_modules).pack(pady=10)
        
        root.mainloop()
        
    except Exception as e:
        # 如果GUI失败，显示错误信息
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误到桌面
        error_file = Path.home() / "Desktop" / "pdf_invoice_error.txt"
        with open(error_file, 'w') as f:
            f.write(f"错误: {e}\n")
            f.write(traceback.format_exc())
        
        print(f"错误信息已保存到: {error_file}")

if __name__ == "__main__":
    main()
