"""
GUI控制器
使用tkinter实现现代化用户界面，包括文件选择、进度显示和结果提示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import logging
from typing import List, Optional, Callable
import queue
import datetime

from src.interfaces.base_interfaces import ProgressCallback
from src.services.pdf_processor import PDFProcessor
from src.services.file_handler import FileHandler
from src.models.data_models import ProcessResult


class GUILogHandler(logging.Handler):
    """自定义日志处理器，将日志信息发送到GUI界面"""
    
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        
    def emit(self, record):
        """发送日志记录到队列"""
        try:
            # 格式化日志消息
            msg = self.format(record)
            # 添加时间戳
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {msg}"
            # 发送到队列
            self.log_queue.put(formatted_msg)
        except Exception:
            self.handleError(record)


class GUIController:
    """GUI控制器类"""
    
    def __init__(self):
        """初始化GUI控制器"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化后端服务
        self.pdf_processor = PDFProcessor()
        self.file_handler = FileHandler()
        
        # 初始化GUI组件
        self.root = None
        self.progress_var = None
        self.progress_label_var = None
        self.progress_bar = None
        self.process_button = None
        self.selected_files = []
        self.output_directory = ""
        
        # 处理状态
        self.is_processing = False
        
        # 日志同步相关
        self.log_queue = queue.Queue()
        self.gui_log_handler = None
        self._setup_logging()
        
        # 亮色系主题配置
        self.colors = {
            'primary': '#3b82f6',      # 明亮蓝色主色调
            'primary_hover': '#2563eb', # 蓝色悬停
            'success': '#10b981',      # 明亮绿色
            'warning': '#f59e0b',      # 明亮橙色
            'danger': '#ef4444',       # 明亮红色
            'light': '#f0f9ff',        # 浅蓝色背景
            'dark': '#1f2937',         # 深色文字
            'gray': '#6b7280',         # 中性灰色
            'border': '#bfdbfe',       # 浅蓝色边框
            'card': '#ffffff',         # 纯白卡片背景
            'shadow': '#93c5fd',       # 浅蓝色阴影
            'accent': '#8b5cf6',       # 紫色强调色
            'info': '#06b6d4',         # 青色信息色
            'light_green': '#d1fae5',  # 浅绿色背景
            'light_blue': '#dbeafe',   # 浅蓝色背景
            'light_purple': '#e9d5ff', # 浅紫色背景
            'light_orange': '#fed7aa'  # 浅橙色背景
        }
        
    def create_main_window(self) -> tk.Tk:
        """
        创建现代化主窗口
        
        Returns:
            tk.Tk: 主窗口对象
        """
        self.root = tk.Tk()
        self.root.title("📄 PDF发票拼版打印系统")
        self.root.geometry("785x986")
        self.root.resizable(True, True)
        self.root.configure(bg=self.colors['light'])
        
        # 设置现代化样式
        self._setup_modern_style()
        
        # 创建标题栏
        self._create_title_bar()
        
        # 创建主滚动框架
        self._create_scrollable_main_frame()
        
        # 启动日志队列处理
        self.root.after(100, self._process_log_queue)
        
        return self.root
    
    def _setup_modern_style(self):
        """设置现代化样式"""
        style = ttk.Style()
        
        # 配置现代化按钮样式
        style.configure('Modern.TButton',
                       padding=(20, 12),
                       font=('Segoe UI', 10),
                       borderwidth=0,
                       focuscolor='none')
        
        style.configure('Primary.TButton',
                       padding=(20, 12),
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.configure('Success.TButton',
                       padding=(20, 12),
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        # 配置标签样式
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       foreground=self.colors['dark'],
                       background=self.colors['light'])
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11),
                       foreground=self.colors['gray'],
                       background=self.colors['light'])
        
        style.configure('Section.TLabel',
                       font=('Segoe UI', 14, 'bold'),
                       foreground=self.colors['dark'],
                       background=self.colors['card'])
        
        style.configure('Card.TLabel',
                       font=('Segoe UI', 10),
                       foreground=self.colors['dark'],
                       background=self.colors['card'])
        
        # 配置框架样式
        style.configure('Card.TFrame',
                       background=self.colors['card'],
                       relief='flat',
                       borderwidth=1)
        
        # 配置进度条样式
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['primary'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
    
    def _create_title_bar(self):
        """创建标题栏"""
        title_frame = tk.Frame(self.root, bg=self.colors['light'], height=100)
        title_frame.pack(fill=tk.X, padx=30, pady=(30, 0))
        title_frame.pack_propagate(False)
        
        # 主标题
        title_label = ttk.Label(title_frame, text="PDF发票拼版打印系统", style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        # 副标题
        subtitle_label = ttk.Label(title_frame, 
                                  text="智能处理12306电子发票，支持PDF和ZIP文件，一键生成拼版打印文件", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_scrollable_main_frame(self):
        """创建可滚动的主框架"""
        # 创建画布和滚动条
        canvas = tk.Canvas(self.root, bg=self.colors['light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.colors['light'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(30, 0), pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 30), pady=20)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 创建界面组件
        self._create_modern_sections()
    
    def _create_modern_sections(self):
        """创建现代化界面组件"""
        # 文件选择卡片
        self._create_file_selection_card()
        
        # 输出设置卡片
        self._create_output_selection_card()
        
        # 处理控制卡片
        self._create_process_control_card()
        
        # 进度显示卡片
        self._create_progress_card()
        
        # 结果显示卡片
        self._create_result_card()
    
    def _create_card_frame(self, title: str, subtitle: str = "", accent_color=None) -> tk.Frame:
        """创建卡片框架"""
        # 卡片容器
        card_container = tk.Frame(self.scrollable_frame, bg=self.colors['light'])
        card_container.pack(fill=tk.X, pady=(0, 20))
        
        # 卡片主体（带彩色边框）
        border_color = accent_color or self.colors['border']
        card = tk.Frame(card_container, bg=self.colors['card'], relief='solid', bd=2, highlightbackground=border_color)
        card.pack(fill=tk.X, padx=2, pady=2)
        
        # 卡片头部
        header_frame = tk.Frame(card, bg=self.colors['card'])
        header_frame.pack(fill=tk.X, padx=25, pady=(25, 15))
        
        # 标题
        title_label = ttk.Label(header_frame, text=title, style='Section.TLabel')
        title_label.pack(anchor=tk.W)
        
        # 副标题
        if subtitle:
            subtitle_label = ttk.Label(header_frame, text=subtitle, 
                                     font=('Segoe UI', 9), 
                                     foreground=self.colors['gray'],
                                     background=self.colors['card'])
            subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 内容区域
        content_frame = tk.Frame(card, bg=self.colors['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 25))
        
        return content_frame
    
    def _create_modern_button(self, parent, text, command, style='primary', width=None):
        """创建现代化亮色按钮"""
        # 高对比度按钮颜色配置
        colors = {
            'primary': {'bg': '#2563eb', 'hover': '#1d4ed8', 'fg': 'white'},      # 深蓝色，更明显
            'secondary': {'bg': '#7c3aed', 'hover': '#6d28d9', 'fg': 'white'},    # 紫色，更明显
            'success': {'bg': '#059669', 'hover': '#047857', 'fg': 'white'},      # 深绿色，更明显
            'danger': {'bg': '#dc2626', 'hover': '#b91c1c', 'fg': 'white'},       # 深红色，更明显
            'light': {'bg': '#e5e7eb', 'hover': '#d1d5db', 'fg': '#374151'},      # 浅灰色，深色文字
            'info': {'bg': '#0891b2', 'hover': '#0e7490', 'fg': 'white'},         # 深青色，更明显
            'warning': {'bg': '#d97706', 'hover': '#b45309', 'fg': 'white'}       # 深橙色，更明显
        }
        
        color_config = colors.get(style, colors['primary'])
        
        # 创建按钮框架
        btn_frame = tk.Frame(parent, bg=parent['bg'])
        if width:
            btn_frame.configure(width=width)
        
        # 创建按钮
        button = tk.Button(
            btn_frame,
            text=text,
            command=command,
            font=('Segoe UI', 10, 'bold'),  # 所有按钮都用粗体
            bg=color_config['bg'],
            fg=color_config['fg'],
            activebackground=color_config['hover'],
            activeforeground=color_config['fg'],
            relief='raised',  # 使用凸起效果
            borderwidth=2,    # 添加边框
            cursor='hand2',
            padx=25,          # 增加内边距
            pady=15
        )
        button.pack(fill=tk.BOTH, expand=True)
        
        # 添加增强的悬停效果
        def on_enter(e):
            button.configure(bg=color_config['hover'], relief='raised', borderwidth=3)
        
        def on_leave(e):
            button.configure(bg=color_config['bg'], relief='raised', borderwidth=2)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return btn_frame
    
    def _create_file_selection_card(self) -> None:
        """创建文件选择卡片"""
        content_frame = self._create_card_frame(
            "📁 选择发票文件", 
            "支持PDF文件和ZIP压缩包，可单选或批量选择",
            accent_color=self.colors['primary']
        )
        
        # 按钮区域
        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 亮色现代化按钮
        select_files_btn = self._create_modern_button(
            button_frame, "📄 选择文件", self.show_file_selection_dialog, 
            style='primary', width=140
        )
        select_files_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        select_folder_btn = self._create_modern_button(
            button_frame, "📂 选择文件夹", self.show_directory_selection_dialog,
            style='info', width=140
        )
        select_folder_btn.pack(side=tk.LEFT)
        
        # 文件列表区域
        list_label = ttk.Label(content_frame, text="已选择的文件:", style='Card.TLabel')
        list_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 文件列表框架
        list_container = tk.Frame(content_frame, bg=self.colors['primary'], bd=2)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        list_frame = tk.Frame(list_container, bg=self.colors['light_blue'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 亮色文件列表
        self.file_listbox = tk.Listbox(
            list_frame, 
            height=6,
            font=('Segoe UI', 9),
            bg=self.colors['light_blue'],
            fg=self.colors['dark'],
            selectbackground=self.colors['primary'],
            selectforeground='white',
            borderwidth=0,
            highlightthickness=0,
            activestyle='none'
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 现代化滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 清除按钮
        clear_btn = self._create_modern_button(
            content_frame, "🗑️ 清除列表", self.clear_file_list,
            style='warning', width=120
        )
        clear_btn.pack(anchor=tk.W)
    
    def _create_output_selection_card(self) -> None:
        """创建输出目录选择卡片"""
        content_frame = self._create_card_frame(
            "💾 输出设置", 
            "选择生成的拼版PDF文件保存位置",
            accent_color=self.colors['accent']
        )
        
        # 输出目录选择区域
        output_frame = tk.Frame(content_frame, bg=self.colors['card'])
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 选择目录按钮
        select_output_btn = self._create_modern_button(
            output_frame, "📁 选择输出目录", self.show_output_directory_dialog,
            style='secondary', width=150
        )
        select_output_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # 输出路径显示
        path_container = tk.Frame(output_frame, bg=self.colors['accent'], bd=2)
        path_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        path_frame = tk.Frame(path_container, bg=self.colors['light_purple'])
        path_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.output_label_var = tk.StringVar(value="未选择输出目录")
        output_path_label = tk.Label(
            path_frame,
            textvariable=self.output_label_var,
            font=('Segoe UI', 9),
            bg=self.colors['light_purple'],
            fg=self.colors['dark'],
            anchor='w',
            padx=15,
            pady=12
        )
        output_path_label.pack(fill=tk.BOTH, expand=True)
    
    def _create_process_control_card(self) -> None:
        """创建处理控制卡片"""
        content_frame = self._create_card_frame(
            "⚡ 开始处理", 
            "一键生成拼版PDF文件，支持2列4行布局",
            accent_color=self.colors['success']
        )
        
        # 按钮区域
        button_frame = tk.Frame(content_frame, bg=self.colors['card'])
        button_frame.pack(fill=tk.X)
        
        # 开始处理按钮
        self.process_button_frame = self._create_modern_button(
            button_frame, "🚀 开始拼版处理", self.start_processing,
            style='success', width=180
        )
        self.process_button_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # 取消处理按钮
        self.cancel_button_frame = self._create_modern_button(
            button_frame, "⏹️ 取消处理", self.cancel_processing,
            style='danger', width=140
        )
        self.cancel_button_frame.pack(side=tk.LEFT)
        
        # 获取实际的按钮组件以便后续控制状态
        self.process_button = self.process_button_frame.winfo_children()[0]
        self.cancel_button = self.cancel_button_frame.winfo_children()[0]
        
        # 初始状态
        self.process_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.DISABLED)
    
    def _create_progress_card(self) -> None:
        """创建进度显示卡片"""
        content_frame = self._create_card_frame(
            "📊 处理进度", 
            "实时显示文件处理进度和状态信息",
            accent_color=self.colors['info']
        )
        
        # 进度条容器
        progress_container = tk.Frame(content_frame, bg=self.colors['info'], bd=2)
        progress_container.pack(fill=tk.X, pady=(0, 15))
        
        progress_frame = tk.Frame(progress_container, bg=self.colors['light_blue'])
        progress_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # 现代化进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100,
            style='Modern.Horizontal.TProgressbar',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, padx=15, pady=15)
        
        # 进度标签
        self.progress_label_var = tk.StringVar(value="🟢 准备就绪")
        progress_label = tk.Label(
            content_frame,
            textvariable=self.progress_label_var,
            font=('Segoe UI', 10),
            bg=self.colors['card'],
            fg=self.colors['dark'],
            anchor='w'
        )
        progress_label.pack(fill=tk.X)
    
    def _create_result_card(self) -> None:
        """创建结果显示卡片"""
        content_frame = self._create_card_frame(
            "📋 处理结果", 
            "详细的处理日志和结果信息",
            accent_color=self.colors['warning']
        )
        
        # 结果文本框容器
        result_container = tk.Frame(content_frame, bg=self.colors['warning'], bd=2)
        result_container.pack(fill=tk.BOTH, expand=True)
        
        result_frame = tk.Frame(result_container, bg=self.colors['light_orange'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 亮色文本框
        self.result_text = tk.Text(
            result_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg=self.colors['light_orange'],
            fg=self.colors['dark'],
            selectbackground=self.colors['warning'],
            selectforeground='white',
            borderwidth=0,
            highlightthickness=0,
            state=tk.DISABLED,
            padx=15,
            pady=15
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 现代化滚动条
        result_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, 
                                       command=self.result_text.yview)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
    
    def show_file_selection_dialog(self) -> None:
        """显示文件选择对话框"""
        try:
            files = filedialog.askopenfilenames(
                title="选择PDF发票文件或ZIP压缩包",
                filetypes=[
                    ("支持的文件", "*.pdf;*.zip"), 
                    ("PDF文件", "*.pdf"), 
                    ("ZIP压缩包", "*.zip"),
                    ("所有文件", "*.*")
                ],
                multiple=True
            )
            
            if files:
                # 验证并添加文件
                valid_files = []
                invalid_files = []
                
                for file_path in files:
                    # 处理PDF文件
                    if file_path.lower().endswith('.pdf'):
                        if self.file_handler.validate_pdf_file(file_path):
                            if file_path not in self.selected_files:
                                valid_files.append(file_path)
                        else:
                            invalid_files.append(file_path)
                    
                    # 处理ZIP文件
                    elif file_path.lower().endswith('.zip'):
                        if self.file_handler.validate_zip_file(file_path):
                            # 从ZIP文件中提取PDF
                            extracted_pdfs = self.file_handler.extract_pdfs_from_zip(file_path)
                            for pdf_path in extracted_pdfs:
                                if pdf_path not in self.selected_files:
                                    valid_files.append(pdf_path)
                            
                            if extracted_pdfs:
                                self._log_result(f"从ZIP文件 {os.path.basename(file_path)} 中提取了 {len(extracted_pdfs)} 个PDF文件")
                            else:
                                invalid_files.append(file_path)
                                self._log_result(f"ZIP文件 {os.path.basename(file_path)} 中没有找到有效的PDF文件")
                        else:
                            invalid_files.append(file_path)
                    
                    else:
                        invalid_files.append(file_path)
                
                # 添加有效文件到列表
                self.selected_files.extend(valid_files)
                self._update_file_list()
                
                # 显示验证结果
                if invalid_files:
                    messagebox.showwarning(
                        "文件验证警告",
                        f"以下文件不是有效的PDF或ZIP文件，已跳过:\n" + 
                        "\n".join([os.path.basename(f) for f in invalid_files])
                    )
                
                if valid_files:
                    self._log_result(f"已添加 {len(valid_files)} 个有效PDF文件")
                
                self._update_process_button_state()
                
        except Exception as e:
            self.logger.error(f"文件选择对话框错误: {str(e)}")
            messagebox.showerror("错误", f"选择文件时发生错误: {str(e)}")
    
    def show_directory_selection_dialog(self) -> None:
        """显示目录选择对话框"""
        try:
            directory = filedialog.askdirectory(title="选择包含PDF文件的目录")
            
            if directory:
                # 获取目录中的PDF文件
                pdf_files = self.file_handler.get_pdf_files(directory)
                
                if pdf_files:
                    # 添加新文件到列表（避免重复）
                    new_files = [f for f in pdf_files if f not in self.selected_files]
                    self.selected_files.extend(new_files)
                    self._update_file_list()
                    
                    self._log_result(f"从目录 {directory} 中添加了 {len(new_files)} 个PDF文件")
                    self._update_process_button_state()
                else:
                    messagebox.showinfo("信息", f"在目录 {directory} 中没有找到有效的PDF文件")
                    
        except Exception as e:
            self.logger.error(f"目录选择对话框错误: {str(e)}")
            messagebox.showerror("错误", f"选择目录时发生错误: {str(e)}")
    
    def show_output_directory_dialog(self) -> None:
        """显示输出目录选择对话框"""
        try:
            directory = filedialog.askdirectory(title="选择输出目录")
            
            if directory:
                self.output_directory = directory
                self.output_label_var.set(directory)
                self._update_process_button_state()
                self._log_result(f"输出目录设置为: {directory}")
                
        except Exception as e:
            self.logger.error(f"输出目录选择错误: {str(e)}")
            messagebox.showerror("错误", f"选择输出目录时发生错误: {str(e)}")
    
    def clear_file_list(self) -> None:
        """清除文件列表"""
        self.selected_files.clear()
        self._update_file_list()
        self._update_process_button_state()
        self._log_result("已清除文件列表")
    
    def start_processing(self) -> None:
        """开始处理发票文件"""
        if self.is_processing:
            return
        
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择要处理的PDF文件")
            return
        
        if not self.output_directory:
            messagebox.showwarning("警告", "请先选择输出目录")
            return
        
        # 生成输出文件名
        output_filename = self.file_handler.generate_output_filename(self.selected_files)
        output_path = os.path.join(self.output_directory, output_filename)
        
        # 更新UI状态
        self.is_processing = True
        self.process_button.configure(state=tk.DISABLED)
        self.cancel_button.configure(state=tk.NORMAL)
        
        # 清除之前的结果
        self._clear_result_text()
        self._log_result(f"开始处理 {len(self.selected_files)} 个PDF文件...")
        self._log_result(f"输出文件: {output_path}")
        
        # 在后台线程中处理
        processing_thread = threading.Thread(
            target=self._process_in_background,
            args=(self.selected_files.copy(), output_path),
            daemon=True
        )
        processing_thread.start()
    
    def cancel_processing(self) -> None:
        """取消处理（目前只是更新UI状态）"""
        # 注意：实际的取消逻辑需要在PDFProcessor中实现
        self._log_result("用户请求取消处理...")
        self.is_processing = False
        self.process_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)
    
    def _process_in_background(self, input_files: List[str], output_path: str) -> None:
        """在后台线程中处理文件"""
        try:
            # 创建进度回调函数
            def progress_callback(progress: float, message: str) -> None:
                # 使用after方法在主线程中更新UI
                self.root.after(0, self._update_progress, progress, message)
                # 同时记录到日志
                self.logger.info(f"处理进度 {progress:.1f}%: {message}")
            
            # 记录开始处理
            self.logger.info(f"开始处理 {len(input_files)} 个PDF文件")
            self.logger.info(f"输出文件路径: {output_path}")
            
            # 开始处理
            result = self.pdf_processor.process_invoices(
                input_files, output_path, progress_callback
            )
            
            # 在主线程中显示结果
            self.root.after(0, self._show_process_result, result)
            
        except Exception as e:
            self.logger.error(f"后台处理错误: {str(e)}")
            # 在主线程中显示错误
            self.root.after(0, self._show_process_error, str(e))
    
    def _update_progress(self, progress: float, message: str) -> None:
        """更新进度显示"""
        self.progress_var.set(progress)
        
        # 添加进度图标
        if progress == 0:
            icon = "🟡"
        elif progress < 50:
            icon = "🔄"
        elif progress < 100:
            icon = "⚡"
        else:
            icon = "✅"
        
        self.progress_label_var.set(f"{icon} {message}")
        self.root.update_idletasks()
    
    def _show_process_result(self, result: ProcessResult) -> None:
        """显示处理结果"""
        self.is_processing = False
        self.process_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)
        
        if result.success:
            # 成功完成
            self._log_result("=" * 50)
            self._log_result("处理完成！")
            self._log_result(f"成功处理: {result.processed_count} 个文件")
            self._log_result(f"生成页数: {result.total_pages} 页")
            self._log_result(f"输出文件: {result.output_file}")
            
            if result.skipped_files:
                self._log_result(f"跳过文件: {len(result.skipped_files)} 个")
                for skipped in result.skipped_files:
                    self._log_result(f"  - {os.path.basename(skipped)}")
            
            # 显示成功对话框
            messagebox.showinfo(
                "处理完成",
                f"成功生成拼版PDF文件！\n\n"
                f"处理文件: {result.processed_count} 个\n"
                f"生成页数: {result.total_pages} 页\n"
                f"输出文件: {os.path.basename(result.output_file)}\n\n"
                f"文件保存在: {os.path.dirname(result.output_file)}"
            )
        else:
            # 处理失败
            self._log_result("=" * 50)
            self._log_result("处理失败！")
            
            if result.errors:
                self._log_result("错误信息:")
                for error in result.errors:
                    self._log_result(f"  - {error}")
            
            # 显示错误对话框
            error_message = "处理过程中发生错误:\n\n" + "\n".join(result.errors[:3])
            if len(result.errors) > 3:
                error_message += f"\n... 还有 {len(result.errors) - 3} 个错误"
            
            messagebox.showerror("处理失败", error_message)
    
    def _show_process_error(self, error_message: str) -> None:
        """显示处理错误"""
        self.is_processing = False
        self.process_button.configure(state=tk.NORMAL)
        self.cancel_button.configure(state=tk.DISABLED)
        
        self._log_result("=" * 50)
        self._log_result("处理过程中发生严重错误！")
        self._log_result(f"错误: {error_message}")
        
        messagebox.showerror("严重错误", f"处理过程中发生严重错误:\n\n{error_message}")
    
    def _update_file_list(self) -> None:
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
    
    def _update_process_button_state(self) -> None:
        """更新处理按钮状态"""
        if self.selected_files and self.output_directory and not self.is_processing:
            self.process_button.configure(state=tk.NORMAL)
            # 更新输出路径显示颜色
            if hasattr(self, 'output_label_var'):
                # 找到输出路径标签并更新颜色
                for widget in self.scrollable_frame.winfo_children():
                    if hasattr(widget, 'winfo_children'):
                        for child in widget.winfo_children():
                            if hasattr(child, 'winfo_children'):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Label) and grandchild.cget('textvariable') == str(self.output_label_var):
                                        grandchild.configure(fg=self.colors['dark'])
        else:
            self.process_button.configure(state=tk.DISABLED)
    
    def _log_result(self, message: str) -> None:
        """记录结果到文本框"""
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.configure(state=tk.DISABLED)
        self.result_text.see(tk.END)
    
    def _clear_result_text(self) -> None:
        """清除结果文本"""
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.configure(state=tk.DISABLED)
    
    def run(self) -> None:
        """运行GUI应用"""
        if self.root is None:
            self.create_main_window()
        
        # 设置关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 启动主循环
        self.root.mainloop()
    
    def _on_closing(self) -> None:
        """窗口关闭事件处理"""
        if self.is_processing:
            if messagebox.askokcancel("退出", "正在处理文件，确定要退出吗？"):
                self._cleanup_and_exit()
        else:
            self._cleanup_and_exit()
    
    def _cleanup_and_exit(self) -> None:
        """清理资源并退出"""
        try:
            # 清理临时目录
            self.file_handler.cleanup_temp_dirs()
            # 清理日志处理器
            self._cleanup_logging()
        except Exception as e:
            self.logger.warning(f"清理临时目录时发生错误: {e}")
        finally:
            self.root.destroy()
    
    def _setup_logging(self) -> None:
        """设置日志处理器，将日志信息同步到GUI"""
        # 创建GUI日志处理器
        self.gui_log_handler = GUILogHandler(self.log_queue)
        self.gui_log_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.gui_log_handler.setFormatter(formatter)
        
        # 添加到相关的logger
        loggers_to_monitor = [
            'src.services.pdf_processor',
            'src.services.file_handler', 
            'src.services.pdf_reader',
            'src.services.layout_manager',
            'src.ui.gui_controller'
        ]
        
        for logger_name in loggers_to_monitor:
            logger = logging.getLogger(logger_name)
            logger.addHandler(self.gui_log_handler)
            logger.setLevel(logging.INFO)
    
    def _cleanup_logging(self) -> None:
        """清理日志处理器"""
        if self.gui_log_handler:
            # 从所有logger中移除处理器
            loggers_to_cleanup = [
                'src.services.pdf_processor',
                'src.services.file_handler',
                'src.services.pdf_reader', 
                'src.services.layout_manager',
                'src.ui.gui_controller'
            ]
            
            for logger_name in loggers_to_cleanup:
                logger = logging.getLogger(logger_name)
                logger.removeHandler(self.gui_log_handler)
    
    def _process_log_queue(self) -> None:
        """处理日志队列中的消息"""
        try:
            while True:
                # 非阻塞获取日志消息
                log_message = self.log_queue.get_nowait()
                # 显示到结果文本框
                self._log_result(log_message)
        except queue.Empty:
            pass
        
        # 如果GUI还在运行，继续检查日志队列
        if self.root and self.root.winfo_exists():
            self.root.after(100, self._process_log_queue)  # 每100ms检查一次


def create_gui_application(config=None) -> GUIController:
    """
    创建GUI应用程序实例
    
    Args:
        config: 配置字典（可选）
    
    Returns:
        GUIController: GUI控制器实例
    """
    return GUIController()