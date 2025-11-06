"""
Dialysis Data Automation System - Main Application
透析数据自动化系统 - 主程序

Version: 1.0.0
Author: Healthcare IT Team
Date: 2025-01-08
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import json
import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    filename='logs/automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DialysisAutomationSystem:
    def __init__(self, root, use_gpu=False):  # ✅ 添加 root 参数
        self.root = root
        self.root.title("Dialysis Data Automation System 透析数据自动化系统")
        self.root.geometry("1400x900")
        
        # 加载配置
        self.load_config()
        
        # 数据存储
        self.nursing_record_data = {}
        self.hourly_observations = []
        self.current_image = None
        self.nursing_image = None
        self.machine_image = None
        
        # 创建界面
        self.create_ui()
        self.log("System initialized successfully 系统初始化成功")
        
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {}
            logging.error(f"Failed to load config: {e}")
        
    def create_ui(self):
        """创建用户界面"""
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.columnconfigure(2, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # 标题
        title_frame = ttk.Frame(main_container)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        title_label = ttk.Label(
            title_frame, 
            text="🏥 Dialysis Data Automation System\n透析数据自动化系统",
            font=("Arial", 16, "bold"),
            justify="center"
        )
        title_label.pack()
        
        # 版本信息
        version_label = ttk.Label(
            title_frame,
            text="Version 1.0.0 | For KLSCH Haemodialysis Unit",
            font=("Arial", 8),
            foreground="gray"
        )
        version_label.pack()
        
        # 左侧面板 - 步骤和控制
        left_frame = ttk.LabelFrame(main_container, text="Steps 操作步骤", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # 步骤1: 护理记录纸
        step1_frame = ttk.LabelFrame(left_frame, text="Step 1: Nursing Record 护理记录纸", padding="10")
        step1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            step1_frame, 
            text="📄 Upload Photo 上传照片",
            command=self.upload_nursing_record,
            width=30
        ).grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step1_frame, 
            text="🔍 Start OCR 开始识别",
            command=self.ocr_nursing_record,
            width=30
        ).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.nursing_status = ttk.Label(step1_frame, text="Status: Ready 准备就绪", foreground="blue")
        self.nursing_status.grid(row=2, column=0, pady=5)
        
        # 步骤2: 透析机屏幕
        step2_frame = ttk.LabelFrame(left_frame, text="Step 2: Dialysis Machine 透析机屏幕", padding="10")
        step2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            step2_frame, 
            text="📱 Upload Photo 上传照片",
            command=self.upload_machine_screen,
            width=30
        ).grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step2_frame, 
            text="🔍 Extract Hourly Obs 提取每小时记录",
            command=self.ocr_machine_screen,
            width=30
        ).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step2_frame, 
            text="➕ Add Another Time 添加时间点",
            command=self.upload_machine_screen,
            width=30
        ).grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.machine_status = ttk.Label(step2_frame, text="Status: Ready 准备就绪", foreground="blue")
        self.machine_status.grid(row=3, column=0, pady=5)
        
        # 步骤3: Origin自动填入
        step3_frame = ttk.LabelFrame(left_frame, text="Step 3: Origin System Origin系统", padding="10")
        step3_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(step3_frame, text="Username 用户名:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.username_entry = ttk.Entry(step3_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=2, padx=5)
        
        ttk.Label(step3_frame, text="Password 密码:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_entry = ttk.Entry(step3_frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=2, padx=5)
        
        ttk.Label(step3_frame, text="Patient MRN 病历号:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mrn_entry = ttk.Entry(step3_frame, width=25)
        self.mrn_entry.grid(row=2, column=1, pady=2, padx=5)
        
        ttk.Button(
            step3_frame, 
            text="🚀 Auto Fill Data 自动填入数据",
            command=self.auto_fill_origin,
            width=30
        ).grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # 其他操作
        action_frame = ttk.LabelFrame(left_frame, text="Actions 操作", padding="10")
        action_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(
            action_frame, 
            text="💾 Export JSON 导出数据",
            command=self.export_json,
            width=30
        ).grid(row=0, column=0, pady=3, sticky=(tk.W, tk.E))
        
        ttk.Button(
            action_frame, 
            text="📋 Load JSON 导入数据",
            command=self.load_json,
            width=30
        ).grid(row=1, column=0, pady=3, sticky=(tk.W, tk.E))
        
        ttk.Button(
            action_frame, 
            text="🔄 Reset All 重置所有",
            command=self.reset_all,
            width=30
        ).grid(row=2, column=0, pady=3, sticky=(tk.W, tk.E))
        
        # 中间面板 - 图片预览
        middle_frame = ttk.LabelFrame(main_container, text="Image Preview 图片预览", padding="10")
        middle_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # 创建Canvas用于显示图片
        self.image_canvas = tk.Canvas(middle_frame, width=500, height=600, bg="white")
        self.image_canvas.pack(fill="both", expand=True)
        
        # 默认提示
        self.image_canvas.create_text(
            250, 300,
            text="No image loaded\n未加载图片\n\nClick upload buttons to start\n点击上传按钮开始",
            font=("Arial", 12),
            fill="gray",
            justify="center"
        )
        
        # 右侧面板 - 数据编辑
        right_frame = ttk.LabelFrame(main_container, text="Data Editor 数据编辑器", padding="10")
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Notebook for different data sections
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: 基本数据
        self.basic_data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_data_tab, text="Basic Data 基本数据")
        self.create_basic_data_fields()
        
        # Tab 2: 每小时观察
        self.hourly_obs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.hourly_obs_tab, text="Hourly Obs 每小时记录")
        self.create_hourly_obs_table()
        
        # Tab 3: 日志
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Logs 日志")
        self.create_log_area()
        
    def create_basic_data_fields(self):
        """创建基本数据输入字段"""
        # 使用滚动框架
        canvas = tk.Canvas(self.basic_data_tab)
        scrollbar = ttk.Scrollbar(self.basic_data_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 基本数据字段
        self.basic_fields = {}
        fields = [
            ("DATE", "Date 日期", "08-10-2025"),
            ("NUMBER_OF_HD", "Number of HD 透析次数", "609"),
            ("HRS_OF_HD", "Hours of HD 透析时长", "4"),
            ("PRE_BP", "Pre BP 治疗前血压", "233/107"),
            ("POST_BP", "Post BP 治疗后血压", "157/76"),
            ("PRE_PULSE", "Pre Pulse 治疗前脉搏", "94"),
            ("TEMPERATURE", "Temperature 体温 (°C)", "36.0"),
            ("PRE_WEIGHT", "Pre Weight 治疗前体重 (kg)", "71.15"),
            ("IDWG", "IDWG 体重增加", "2.0/2.65"),
            ("POST_WEIGHT", "Post Weight 治疗后体重 (kg)", "68.5"),
            ("UF", "UF 超滤量 (L)", "2.5"),
            ("KT_V", "Kt/V 透析充分性", "1.07"),
            ("WEIGHT_LOSS", "Weight Loss 体重减少", "2.65"),
            ("COMFORTABLE", "Comfortable 舒适", "Yes"),
            ("DIZZINESS", "Dizziness 头晕", "No"),
            ("BLEEDING", "Bleeding 出血", "No"),
            ("DRESSING", "Dressing 敷料", "No"),
            ("REMARKS", "Remarks 备注", "")
        ]
        
        for i, (key, label, placeholder) in enumerate(fields):
            ttk.Label(scrollable_frame, text=label + ":").grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            
            if key == "REMARKS":
                entry = tk.Text(scrollable_frame, width=30, height=4)
                entry.grid(row=i, column=1, pady=5, padx=5)
            elif key in ["COMFORTABLE", "DIZZINESS", "BLEEDING", "DRESSING"]:
                entry = ttk.Combobox(scrollable_frame, width=28, values=["Yes", "No", "-"])
                entry.set(placeholder)
                entry.grid(row=i, column=1, pady=5, padx=5)
            else:
                entry = ttk.Entry(scrollable_frame, width=30)
                entry.insert(0, placeholder)
                entry.bind("<FocusIn>", lambda e, p=placeholder: self.clear_placeholder(e, p))
                entry.grid(row=i, column=1, pady=5, padx=5)
            
            self.basic_fields[key] = entry
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_hourly_obs_table(self):
        """创建每小时观察记录表格"""
        # 表格框架
        table_frame = ttk.Frame(self.hourly_obs_tab)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Treeview
        columns = ("TIME", "BP", "VP", "QB", "QD", "PULSE", "UFR")
        self.hourly_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # 列标题
        headers = {
            "TIME": "Time\n时间",
            "BP": "BP\n血压",
            "VP": "VP\n静脉压",
            "QB": "QB\n血流速",
            "QD": "QD\n透析液流速",
            "PULSE": "Pulse\n脉搏",
            "UFR": "UFR\n超滤率"
        }
        
        for col in columns:
            self.hourly_tree.heading(col, text=headers[col])
            self.hourly_tree.column(col, width=90, anchor="center")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.hourly_tree.yview)
        self.hourly_tree.configure(yscrollcommand=scrollbar.set)
        
        self.hourly_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按钮框架
        button_frame = ttk.Frame(self.hourly_obs_tab)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(button_frame, text="➕ Add Row 添加行", command=self.add_hourly_row).pack(side="left", padx=5)
        ttk.Button(button_frame, text="✏️ Edit Row 编辑行", command=self.edit_hourly_row).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🗑️ Delete Row 删除行", command=self.delete_hourly_row).pack(side="left", padx=5)
        
    def create_log_area(self):
        """创建日志区域"""
        self.log_text = scrolledtext.ScrolledText(self.log_tab, width=60, height=35, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        logging.info(message)
        
    def clear_placeholder(self, event, placeholder):
        """清除占位符"""
        widget = event.widget
        if widget.get() == placeholder:
            widget.delete(0, tk.END)
            
    def upload_nursing_record(self):
        """上传护理记录纸照片"""
        filename = filedialog.askopenfilename(
            title="Select Nursing Record Photo 选择护理记录照片",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if filename:
            self.nursing_image = filename
            self.current_image = filename
            self.display_image(filename)
            self.nursing_status.config(text="Status: Image loaded 图片已加载", foreground="green")
            self.log(f"✓ Nursing record loaded 护理记录已加载: {os.path.basename(filename)}")
            
    def upload_machine_screen(self):
        """上传透析机屏幕照片"""
        filename = filedialog.askopenfilename(
            title="Select Dialysis Machine Photo 选择透析机照片",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if filename:
            self.machine_image = filename
            self.current_image = filename
            self.display_image(filename)
            self.machine_status.config(text="Status: Image loaded 图片已加载", foreground="green")
            self.log(f"✓ Machine screen loaded 透析机照片已加载: {os.path.basename(filename)}")
            
    def display_image(self, filename):
        """显示图片预览"""
        try:
            image = Image.open(filename)
            # 调整大小以适应显示
            canvas_width = self.image_canvas.winfo_width() if self.image_canvas.winfo_width() > 1 else 500
            canvas_height = self.image_canvas.winfo_height() if self.image_canvas.winfo_height() > 1 else 600
            
            # 计算缩放比例
            img_width, img_height = image.size
            scale = min(canvas_width / img_width, canvas_height / img_height, 1)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # 清除canvas
            self.image_canvas.delete("all")
            
            # 居中显示图片
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.image_canvas.create_image(x, y, image=photo, anchor="nw")
            self.image_canvas.image = photo  # 保持引用
            
        except Exception as e:
            self.log(f"✗ Error displaying image 显示图片错误: {str(e)}")
            logging.error(f"Display image error: {e}")
            
    def ocr_nursing_record(self):
        """OCR识别护理记录纸"""
        if not self.nursing_image:
            messagebox.showwarning("Warning 警告", "Please upload nursing record image first\n请先上传护理记录照片")
            return
        
        self.nursing_status.config(text="Status: Processing OCR... 识别中...", foreground="orange")
        self.log("⏳ Starting OCR for nursing record 开始识别护理记录...")
    
        try:
            from modules.ocr_module import DialysisOCR
            ocr = DialysisOCR()
            sample_data = ocr.extract_nursing_record(self.nursing_image)
        
            # ✅ 添加这些调试行
            self.log(f"🔍 DEBUG: OCR returned {len(sample_data)} fields")
            self.log(f"🔍 DEBUG: Data = {sample_data}")
        
            filled_count = 0  # ✅ 添加计数器
        
        # 填入数据
            for key, value in sample_data.items():
                if key in self.basic_fields and value:
                    self.log(f"🔍 DEBUG: Trying to fill {key} = {value}")  # ✅ 添加
                    widget = self.basic_fields[key]
                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                        widget.insert("1.0", value)
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    filled_count += 1  # ✅ 添加
                    self.log(f"✓ Filled {key}")  # ✅ 添加
        
            self.log(f"✅ Total fields filled: {filled_count}")  # ✅ 添加
        
            self.nursing_status.config(text="Status: OCR completed ✓ 识别完成", foreground="green")
            self.log("✓ OCR completed. Please verify data. 识别完成，请验证数据")
        
            # 切换到基本数据标签页
            self.notebook.select(self.basic_data_tab)
        
            messagebox.showinfo(
                "OCR Complete OCR完成",
                "Data extracted successfully!\nPlease verify and correct if needed.\n\n"
                "数据提取成功！\n请验证并修正（如需要）。"
            )
        
        except Exception as e:
            self.nursing_status.config(text="Status: OCR failed ✗ 识别失败", foreground="red")
            self.log(f"✗ OCR Error OCR错误: {str(e)}")
            logging.error(f"OCR nursing record error: {e}")
            messagebox.showerror("Error 错误", f"OCR failed OCR失败:\n{str(e)}")

    def ocr_machine_screen(self):
        """OCR识别透析机屏幕"""
        if not self.machine_image:
            messagebox.showwarning("Warning 警告", "Please upload machine screen image first\n请先上传透析机照片")
            return
            
        self.machine_status.config(text="Status: Processing OCR... 识别中...", foreground="orange")
        self.log("⏳ Starting OCR for dialysis machine 开始识别透析机...")
        
        try:
            from modules.ocr_module import DialysisOCR
            ocr = DialysisOCR()
            sample_data = ocr.extract_machine_screen(self.machine_image)

            if not sample_data or not any(sample_data.values()):
                messagebox.showwarning(
                    "Warning 警告",
                    "No data extracted. Please try another photo or add manually.\n未识别到数据。请尝试其他照片或手动添加。"
                )
                return
            
            self.add_hourly_observation(sample_data)
            
            self.machine_status.config(text="Status: OCR completed ✓ 识别完成", foreground="green")
            self.log("✓ Machine screen OCR completed 透析机识别完成")
            
            # 切换到每小时观察标签页
            self.notebook.select(self.hourly_obs_tab)
            
            messagebox.showinfo(
                "Success 成功",
                "Hourly observation added!\nPlease verify the data.\n\n"
                "每小时记录已添加！\n请验证数据。"
            )
            
        except Exception as e:
            self.machine_status.config(text="Status: OCR failed ✗ 识别失败", foreground="red")
            self.log(f"✗ OCR Error OCR错误: {str(e)}")
            logging.error(f"OCR machine screen error: {e}")
            messagebox.showerror("Error 错误", f"OCR failed OCR失败:\n{str(e)}")
            
    def add_hourly_observation(self, data):
        """添加每小时观察记录"""
        values = (
            data.get("TIME", ""),
            data.get("BP", ""),
            data.get("VP", ""),
            data.get("QB", ""),
            data.get("QD", ""),
            data.get("PULSE", ""),
            data.get("UFR", "")
        )
        self.hourly_tree.insert("", "end", values=values)
        self.hourly_observations.append(data)
        
    def add_hourly_row(self):
        """手动添加每小时记录行"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Hourly Observation 添加每小时记录")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        fields = {}
        labels = [
            ("TIME", "Time 时间 (HH:MM)", "07:10"),
            ("BP", "BP 血压 (SYS/DIA)", "217/107"),
            ("VP", "VP 静脉压", "160"),
            ("QB", "QB 血流速 (ml/min)", "300"),
            ("QD", "QD 透析液流速 (ml/min)", "500"),
            ("PULSE", "Pulse 脉搏 (P-XX)", "P-84"),
            ("UFR", "UFR 超滤率 (ml/h)", "625")
        ]
        
        for i, (key, label, placeholder) in enumerate(labels):
            ttk.Label(dialog, text=label + ":").grid(row=i, column=0, sticky=tk.W, padx=15, pady=8)
            entry = ttk.Entry(dialog, width=25)
            entry.insert(0, placeholder)
            entry.grid(row=i, column=1, padx=15, pady=8)
            fields[key] = entry
            
        def save_row():
            data = {key: entry.get() for key, entry in fields.items()}
            self.add_hourly_observation(data)
            self.log(f"✓ Added hourly observation at {data['TIME']} 添加了{data['TIME']}的记录")
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Save 保存", command=save_row, width=15).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel 取消", command=dialog.destroy, width=15).pack(side="left", padx=5)
        
    def edit_hourly_row(self):
        """编辑每小时记录行"""
        selected = self.hourly_tree.selection()
        if not selected:
            messagebox.showwarning("Warning 警告", "Please select a row first\n请先选择一行")
            return
            
        values = self.hourly_tree.item(selected[0])['values']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Hourly Observation 编辑每小时记录")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        fields = {}
        labels = [
            ("TIME", "Time 时间"),
            ("BP", "BP 血压"),
            ("VP", "VP 静脉压"),
            ("QB", "QB 血流速"),
            ("QD", "QD 透析液流速"),
            ("PULSE", "Pulse 脉搏"),
            ("UFR", "UFR 超滤率")
        ]
        
        for i, (key, label) in enumerate(labels):
            ttk.Label(dialog, text=label + ":").grid(row=i, column=0, sticky=tk.W, padx=15, pady=8)
            entry = ttk.Entry(dialog, width=25)
            entry.insert(0, values[i] if i < len(values) else "")
            entry.grid(row=i, column=1, padx=15, pady=8)
            fields[key] = entry
            
        def save_changes():
            new_values = tuple(entry.get() for entry in fields.values())
            self.hourly_tree.item(selected[0], values=new_values)
            self.log(f"✓ Updated hourly observation 更新了每小时记录")
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=len(labels), column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Save 保存", command=save_changes, width=15).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel 取消", command=dialog.destroy, width=15).pack(side="left", padx=5)
        
    def delete_hourly_row(self):
        """删除每小时记录行"""
        selected = self.hourly_tree.selection()
        if not selected:
            messagebox.showwarning("Warning 警告", "Please select a row first\n请先选择一行")
            return
            
        if messagebox.askyesno("Confirm 确认", "Delete selected row?\n删除选中的行？"):
            self.hourly_tree.delete(selected[0])
            self.log("✓ Deleted hourly observation 删除了每小时记录")
            
    def collect_all_data(self):
        """收集所有数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "basic_data": {},
            "hourly_observations": []
        }
        
        # 收集基本数据
        for key, widget in self.basic_fields.items():
            try:
                if isinstance(widget, tk.Text):
                    data["basic_data"][key] = widget.get("1.0", tk.END).strip()
                else:
                    value = widget.get()
                    # 跳过占位符
                    if value and not any(placeholder in value for placeholder in ["e.g.", "例如:"]):
                        data["basic_data"][key] = value
            except:
                data["basic_data"][key] = ""
                
        # 收集每小时观察数据
        for item in self.hourly_tree.get_children():
            values = self.hourly_tree.item(item)['values']
            obs = {
                "TIME": values[0],
                "BP": values[1],
                "VP": values[2],
                "QB": values[3],
                "QD": values[4],
                "PULSE": values[5],
                "UFR": values[6]
            }
            data["hourly_observations"].append(obs)
            
        return data
        
    def export_json(self):
        """导出JSON数据"""
        data = self.collect_all_data()
        
        # 生成默认文件名
        default_filename = f"dialysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filename = filedialog.asksaveasfilename(
            title="Save Data 保存数据",
            defaultextension=".json",
            initialfile=default_filename,
            initialdir="data/exports",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.log(f"✓ Data exported 数据已导出: {os.path.basename(filename)}")
                messagebox.showinfo("Success 成功", f"Data exported successfully!\n数据导出成功！\n\n{os.path.basename(filename)}")
            except Exception as e:
                self.log(f"✗ Export error 导出错误: {str(e)}")
                logging.error(f"Export error: {e}")
                messagebox.showerror("Error 错误", f"Export failed 导出失败:\n{str(e)}")
                
    def load_json(self):
        """导入JSON数据"""
        filename = filedialog.askopenfilename(
            title="Load Data 加载数据",
            initialdir="data/exports",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 加载基本数据
                for key, value in data.get("basic_data", {}).items():
                    if key in self.basic_fields:
                        widget = self.basic_fields[key]
                        try:
                            if isinstance(widget, tk.Text):
                                widget.delete("1.0", tk.END)
                                widget.insert("1.0", value)
                            else:
                                widget.delete(0, tk.END)
                                widget.insert(0, value)
                        except:
                            pass
                            
                # 清除并加载每小时观察数据
                for item in self.hourly_tree.get_children():
                    self.hourly_tree.delete(item)
                    
                for obs in data.get("hourly_observations", []):
                    self.add_hourly_observation(obs)
                    
                self.log(f"✓ Data loaded 数据已加载: {os.path.basename(filename)}")
                messagebox.showinfo("Success 成功", f"Data loaded successfully!\n数据加载成功！\n\n{os.path.basename(filename)}")
            except Exception as e:
                self.log(f"✗ Load error 加载错误: {str(e)}")
                logging.error(f"Load error: {e}")
                messagebox.showerror("Error 错误", f"Load failed 加载失败:\n{str(e)}")
                
    def auto_fill_origin(self):
        """自动填入Origin系统"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        mrn = self.mrn_entry.get()
    
        if not all([username, password, mrn]):
            messagebox.showwarning(
                "Warning 警告", 
                "Please fill in all Origin credentials\n请填写所有Origin登录信息"
            )
            return
        
        # 确认数据
        if not messagebox.askyesno(
            "Confirm 确认",
            f"Start automatic data entry to Origin?\n开始自动填入Origin系统？\n\nPatient MRN: {mrn}\nUsername: {username}"
        ):
            return
        
        self.log("⏳ Starting Origin automation Origin自动化开始...")
    
        try:
            from modules.origin_automation import OriginAutomation
        
            def progress_callback(message):
                self.log(message)
                self.root.update()
        
            origin = OriginAutomation(self.config.get("origin_url"))
            data = self.collect_all_data()
        
            success = origin.run_automation(
                username, password, mrn, data,
                callback=progress_callback
            )
        
            if success:
                self.complete_origin_automation()
            else:
                raise Exception("Automation failed")
            
        except Exception as e:
            self.log(f"✗ Automation error 自动化错误: {str(e)}")
            logging.error(f"Automation error: {e}")
            messagebox.showerror("Error 错误", f"Automation failed 自动化失败:\n{str(e)}")
            
    def complete_origin_automation(self):
        """完成Origin自动化"""
        self.log("💾 Saving data 保存数据...")
        self.log("✅ Data entry completed successfully! 数据填入成功！")
        messagebox.showinfo(
            "Success 成功",
            "Data has been successfully entered into Origin!\n数据已成功填入Origin系统！\n\n"
            "Please verify the data in Origin.\n请在Origin中验证数据。"
        )
        
    def reset_all(self):
        """重置所有数据"""
        if messagebox.askyesno(
            "Confirm 确认",
            "Reset all data? This cannot be undone.\n重置所有数据？此操作无法撤销。"
        ):
            # 清除基本数据
            for widget in self.basic_fields.values():
                try:
                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                    else:
                        widget.delete(0, tk.END)
                except:
                    pass
                    
            # 清除每小时观察数据
            for item in self.hourly_tree.get_children():
                self.hourly_tree.delete(item)
                
            # 清除图片
            self.image_canvas.delete("all")
            self.image_canvas.create_text(
                250, 300,
                text="No image loaded\n未加载图片\n\nClick upload buttons to start\n点击上传按钮开始",
                font=("Arial", 12),
                fill="gray",
                justify="center"
            )
            
            self.current_image = None
            self.nursing_image = None
            self.machine_image = None
            
            # 重置状态
            self.nursing_status.config(text="Status: Ready 准备就绪", foreground="blue")
            self.machine_status.config(text="Status: Ready 准备就绪", foreground="blue")
            
            self.log("🔄 All data reset 所有数据已重置")


def main():
    """主函数"""
    # 确保必要的目录存在
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/exports', exist_ok=True)
    
    root = tk.Tk()
    
    # 设置窗口图标（如果有）
    try:
        root.iconbitmap('assets/logo.ico')
    except:
        pass
    
    app = DialysisAutomationSystem(root)  # ✅ 修复：传入 root 参数
    
    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()