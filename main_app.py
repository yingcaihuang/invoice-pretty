#!/usr/bin/env python3
"""
主应用程序模块
"""

def start_gui_app():
    """启动GUI应用程序"""
    try:
        # 导入原始的main模块
        import main
        main.main()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动错误", f"无法启动主应用程序:\n{e}")
        root.destroy()
