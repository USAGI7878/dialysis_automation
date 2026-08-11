"""
Dialysis Data Automation System - Main Application
透析数据自动化系统 - 主程序

Version: 1.0.0
Author: Healthcare IT Team
Date: 2025-01-08
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from PIL import Image, ImageTk, ImageOps
import json
import os
import threading
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
        self.current_image = None
        self.nursing_image = None
        self.machine_image = None

        # 批量队列: 直接把"当前已识别/编辑好的数据"加入队列，不用先导出JSON再导入
        # Batch queue: push the currently OCR'd/edited data straight in, skipping export→re-import
        self.batch_queue = []

        # 病人名录(姓名<->RN对照表)，本地JSON存的，避免每次要死记RN号码
        from modules.patient_directory import load_patients
        self.patients = load_patients()
        
        # 创建界面
        self.create_ui()
        self.log("System initialized successfully 系统初始化成功")

        # 启动局域网照片上传服务，方便同事用手机直接上传照片(不用Phone Link这类配对软件)
        self.start_phone_upload_service()

    def start_phone_upload_service(self):
        """启动局域网内的照片上传服务(后台线程运行，不阻塞界面)"""
        try:
            from modules.upload_server import start_server_in_background
            port = self.config.get("phone_upload_port", 5001) if hasattr(self, "config") else 5001
            local_ip, used_port, success = start_server_in_background(port=port)
            if success:
                self.log(f"📱 手机上传服务已启动: http://{local_ip}:{used_port}")
                self.log(f"   同事只要连着同一个WiFi/内网，手机浏览器打开这个网址就能上传照片")
            else:
                self.log("ℹ️  手机上传服务未启动(缺少flask，运行 pip install flask 后重启程序即可启用)")
        except Exception as e:
            self.log(f"ℹ️  手机上传服务启动失败: {e}")
        
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {}
            logging.error(f"Failed to load config: {e}")

    def update_gemini_usage_display(self):
        """
        刷新界面上的 "Gemini AI本次会话用量" 指标。
        每次AI OCR调用完(不管成功还是失败)都应该调这个方法刷新一下显示。

        注意: 这只是"本次程序运行以来累计用了多少token"的参考值，
        不是Gemini账号"真正还剩多少额度"——Gemini API没有提供查询剩余额度的接口，
        真实额度要去 https://aistudio.google.com/apikey 后台看。
        """
        try:
            from modules.ai_ocr_module import get_session_usage
            usage = get_session_usage()
        except Exception:
            return

        text = (
            f"✨ Gemini AI本次会话用量: {usage['call_count']} 次调用, "
            f"{usage['total_tokens']} tokens"
        )
        if usage.get("last_error"):
            text += f"  ⚠️ 最近一次: {usage['last_error']}"

        if hasattr(self, "gemini_usage_label"):
            self.gemini_usage_label.config(text=text)

    def reset_gemini_usage_display(self):
        """清零 Gemini 本次会话用量计数(比如想单独看某一段时间的用量)"""
        try:
            from modules.ai_ocr_module import reset_session_usage
            reset_session_usage()
        except Exception:
            pass
        self.update_gemini_usage_display()
        self.log("🔄 已清零 Gemini 用量计数 Gemini usage counter reset")
        
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

        # Gemini AI识别 本次会话用量指标
        # 注意: Gemini API本身没有"剩余额度"查询接口，这里只能显示"本次会话已经用了多少"，
        # 不是真正的"还剩多少"——真实额度要去 https://aistudio.google.com/apikey 后台看。
        # 点这个标签可以重新清零计数(比如想单独看某一段时间的用量)。
        usage_row = ttk.Frame(title_frame)
        usage_row.pack(pady=(2, 0))
        self.gemini_usage_label = ttk.Label(
            usage_row,
            text="✨ Gemini AI本次会话用量: 0 次调用, 0 tokens",
            font=("Arial", 8),
            foreground="gray"
        )
        self.gemini_usage_label.pack(side="left")
        reset_link = ttk.Label(
            usage_row, text="  [清零 Reset]", font=("Arial", 8, "underline"),
            foreground="steel blue", cursor="hand2"
        )
        reset_link.pack(side="left")
        reset_link.bind("<Button-1>", lambda e: self.reset_gemini_usage_display())
        # 用bind绑定点击而不是ttk.Button，是为了做成一个不占地方的小文字链接
        # 而不是一个突兀的按钮——这个指标只是参考信息，不需要太抢眼
        
        # 左侧面板 - 步骤和控制
        # 用Canvas+Scrollbar包一层，让这个面板可以上下滚动——
        # 之前"批量填入"弹窗里的开始按钮被挤出可视范围外看不到，就是同一类问题
        # (窗口不够高、内容没有滚动条，最下面的东西直接被截掉)。
        # 这里加上滚动之后，不管以后再加多少个按钮、窗口开多小，
        # 都能通过滚动找到，不会再发生"功能明明加了但是看不到"的情况。
        left_outer = ttk.LabelFrame(main_container, text="Steps 操作步骤", padding="0")
        left_outer.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        left_canvas = tk.Canvas(left_outer, highlightthickness=0, width=420)
        left_scrollbar = ttk.Scrollbar(left_outer, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        left_canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")

        left_frame = ttk.Frame(left_canvas, padding="10")
        left_canvas_window = left_canvas.create_window((0, 0), window=left_frame, anchor="nw")

        left_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        left_canvas.bind(
            "<Configure>",
            lambda e: left_canvas.itemconfig(left_canvas_window, width=e.width)
        )

        # 鼠标只在悬停在这个面板上的时候才响应滚轮，避免影响别的地方(比如右侧数据表格)的滚动
        def _on_left_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_left_mousewheel(event):
            left_canvas.bind_all("<MouseWheel>", _on_left_mousewheel)

        def _unbind_left_mousewheel(event):
            left_canvas.unbind_all("<MouseWheel>")

        left_canvas.bind("<Enter>", _bind_left_mousewheel)
        left_canvas.bind("<Leave>", _unbind_left_mousewheel)
        
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
            text="📲 从手机导入 Import from Phone",
            command=lambda: self.show_phone_import_dialog("nursing"),
            width=30
        ).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step1_frame, 
            text="🔍 Start OCR 开始识别 (Tesseract)",
            command=self.ocr_nursing_record,
            width=30
        ).grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(
            step1_frame,
            text="✨ AI识别 AI OCR (Gemini)",
            command=self.ocr_nursing_record_ai,
            width=30
        ).grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.nursing_status = ttk.Label(step1_frame, text="Status: Ready 准备就绪", foreground="blue")
        self.nursing_status.grid(row=4, column=0, pady=5)
        
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
            text="📲 从手机导入 Import from Phone",
            command=lambda: self.show_phone_import_dialog("machine"),
            width=30
        ).grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step2_frame, 
            text="🔍 Extract Hourly Obs 提取每小时记录 (Tesseract)",
            command=self.ocr_machine_screen,
            width=30
        ).grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(
            step2_frame,
            text="✨ AI识别 AI OCR (Gemini)",
            command=self.ocr_machine_screen_ai,
            width=30
        ).grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(
            step2_frame, 
            text="➕ Add Another Time 添加时间点",
            command=self.upload_machine_screen,
            width=30
        ).grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.machine_status = ttk.Label(step2_frame, text="Status: Ready 准备就绪", foreground="blue")
        self.machine_status.grid(row=5, column=0, pady=5)
        
        # 步骤3: Origin自动填入
        step3_frame = ttk.LabelFrame(left_frame, text="Step 3: Origin System Origin系统", padding="10")
        step3_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(step3_frame, text="Username 用户名:").grid(row=0, column=0, sticky=tk.W, pady=2)
        # 用共享的StringVar而不是各自独立的值，这样批量填入弹窗里的账密输入框
        # 才能跟这里双向同步——不管在哪边填，两边都能看到同一份数据，
        # 不会出现"明明在批量弹窗里填过了，回到这里点单个填入却又要求重填"的情况。
        self.origin_username_var = tk.StringVar()
        self.origin_password_var = tk.StringVar()
        self.username_entry = ttk.Entry(step3_frame, width=25, textvariable=self.origin_username_var)
        self.username_entry.grid(row=0, column=1, pady=2, padx=5)
        
        ttk.Label(step3_frame, text="Password 密码:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.password_entry = ttk.Entry(step3_frame, width=25, show="*", textvariable=self.origin_password_var)
        self.password_entry.grid(row=1, column=1, pady=2, padx=5)

        ttk.Label(step3_frame, text="搜索病人 Search Patient:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.patient_search_entry = ttk.Entry(step3_frame, width=25)
        self.patient_search_entry.grid(row=2, column=1, pady=2, padx=5)
        self.patient_search_entry.bind("<KeyRelease>", self.on_patient_search_keyrelease)
        self.patient_search_entry.bind("<FocusOut>", lambda e: self.root.after(150, self.hide_patient_dropdown))
        self._patient_dropdown = None
        
        ttk.Label(step3_frame, text="Patient MRN 病历号:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.mrn_entry = ttk.Entry(step3_frame, width=25)
        self.mrn_entry.grid(row=3, column=1, pady=2, padx=5)

        ttk.Button(
            step3_frame,
            text="👥 病人名单管理 Manage Patients",
            command=self.show_patient_manager,
            width=30
        ).grid(row=4, column=0, columnspan=2, pady=(2, 8), sticky=(tk.W, tk.E))
        
        ttk.Button(
            step3_frame, 
            text="🚀 Auto Fill Data 自动填入数据",
            command=self.auto_fill_origin,
            width=30
        ).grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        ttk.Button(
            step3_frame,
            text="➕ 加入批量队列 Add to Batch Queue",
            command=self.add_to_batch_queue,
            width=30
        ).grid(row=6, column=0, columnspan=2, pady=(0, 4), sticky=(tk.W, tk.E))

        self.batch_queue_label = ttk.Label(
            step3_frame, text="队列 Queue: 0 位 patient(s)", foreground="gray"
        )
        self.batch_queue_label.grid(row=7, column=0, columnspan=2, pady=(0, 6))

        ttk.Button(
            step3_frame,
            text="📦 批量填入队列 Batch Auto-Fill Queue",
            command=self.show_batch_fill_dialog,
            width=30
        ).grid(row=8, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
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

        ttk.Button(
            action_frame,
            text="🧹 清空病人资料 Next Patient",
            command=self.clear_current_patient,
            width=30
        ).grid(row=3, column=0, pady=3, sticky=(tk.W, tk.E))
        
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
        self.basic_field_placeholders = {}  # 记录每个字段的初始"示例值"，收集数据时用来判断是否被用户真正改过
        fields = [
            ("_SECTION_SESSION", "── 每次透析都要填 Per-Session Data ──", None),
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
            ("REMARKS", "Remarks 备注", ""),

            ("_SECTION_PROFILE", "── 病人固定信息(较少变化) Patient Profile ──", None),
            ("HEIGHT", "Height 身高 (cm)", "165"),
            ("WEIGHT", "Weight/Dry Weight 体重 (kg)", "60.5"),
            ("DIALYZER", "Dialyzer 透析器", "PES 1.4LF"),
            ("VASCULAR_ACCESS", "Vascular Access 血管通路", "LT BCF"),
            ("QD", "QD 透析液流速", "500"),
            ("QB", "QB 血流速", "250"),
            ("CONSTRUCTION", "Construction 建立日期", "DD-MM-YYYY"),
            ("INSERTION", "Insertion 置入日期", "DD-MM-YYYY"),
            ("EPO", "EPO 促红细胞生成素", "REC 4000IU"),
            ("IV_IRON", "IV Iron 静脉铁剂", "2/52"),
            ("HEPARIN", "Heparin 肝素", "1 MLS"),
            ("ALLERGY", "Allergy 过敏史", "No Known Allergy"),
            ("NOTE", "Note 备注(Na/T等)", ""),
        ]
        
        for i, (key, label, placeholder) in enumerate(fields):
            if key.startswith("_SECTION"):
                # 分组标题,不是输入框,跨两列显示,加粗
                section_label = ttk.Label(
                    scrollable_frame, text=label,
                    font=("TkDefaultFont", 9, "bold")
                )
                section_label.grid(row=i, column=0, columnspan=2, sticky=tk.W, pady=(12, 4), padx=5)
                continue

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
            self.basic_field_placeholders[key] = placeholder
        
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
        ttk.Button(button_frame, text="⬆️ 上移 Move Up", command=self.move_hourly_row_up).pack(side="left", padx=5)
        ttk.Button(button_frame, text="⬇️ 下移 Move Down", command=self.move_hourly_row_down).pack(side="left", padx=5)
        
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
            
    def show_phone_import_dialog(self, target):
        """
        弹窗列出所有同事用手机上传、还没处理的照片(带缩略图)，
        点击某一张就导入成 nursing_image 或 machine_image(取决于target)，
        导入后自动把这张照片从"待处理"移到"已导入"，不会重复出现。
        target: "nursing" 或 "machine"
        """
        try:
            from modules.upload_server import list_incoming_photos, archive_incoming_photo
        except ImportError:
            messagebox.showerror(
                "Missing dependency 缺少依赖",
                "缺少 flask，请先运行: pip install flask，然后重启程序"
            )
            return

        photos = list_incoming_photos()
        if not photos:
            messagebox.showinfo(
                "No photos 暂无照片",
                "手机上传服务里目前没有待处理的照片。\n"
                "请先让同事用手机打开上传网址(启动程序时日志里有显示)上传照片。"
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("从手机导入照片 Import from Phone")
        dialog.geometry("520x520")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"选择一张照片导入到 "
                                f"{'Step 1 护理记录' if target == 'nursing' else 'Step 2 透析机屏幕'}："
                  ).pack(pady=8)

        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 重要: PhotoImage对象必须有持久的Python引用，不然一旦这个函数执行完，
        # 局部变量马上被垃圾回收，图片内容就会变成空白(经典的tkinter坑)。
        # 挂在dialog这个对象本身上，让引用跟弹窗窗口"同生共死"，弹窗关掉才释放。
        dialog.thumb_refs = []

        def do_import(photo_path):
            try:
                if not os.path.exists(photo_path):
                    messagebox.showerror("Error 错误", f"文件不存在，可能已经被处理过了:\n{photo_path}")
                    dialog.destroy()
                    return

                # 先归档(把照片从"待处理"移到"已导入"文件夹)，拿到移动后的新路径，
                # 再把这个新路径赋给nursing_image/machine_image——
                # 一定要先归档再赋值，不然后面OCR会去读一个已经被挪走、不存在了的旧路径
                archived_path = archive_incoming_photo(photo_path)
                archived_path = self._load_and_normalize_image(archived_path)

                if target == "nursing":
                    self.nursing_image = archived_path
                    self.nursing_status.config(text="Status: Image loaded 图片已加载", foreground="green")
                else:
                    self.machine_image = archived_path
                    self.machine_status.config(text="Status: Image loaded 图片已加载", foreground="green")
                self.current_image = archived_path
                self.display_image(archived_path)
                self.log(f"📲 从手机导入照片: {os.path.basename(archived_path)}")
                dialog.destroy()
            except Exception as e:
                # 之前这里没有任何错误处理，一旦display_image或别的步骤出错，
                # 界面看起来就像"点击完全没反应"，用户不知道到底发生了什么。
                # 现在改成明确弹窗告诉用户具体哪里出错了。
                logging.error(f"从手机导入照片失败: {e}")
                messagebox.showerror(
                    "Import failed 导入失败",
                    f"导入这张照片时出错:\n{e}\n\n"
                    f"文件: {os.path.basename(photo_path)}"
                )

        cols = 3
        for idx, photo_path in enumerate(photos):
            frame = ttk.Frame(scrollable_frame)
            frame.grid(row=idx // cols, column=idx % cols, padx=8, pady=8)

            try:
                img = Image.open(photo_path)
                img.thumbnail((130, 130))
                thumb = ImageTk.PhotoImage(img)
                dialog.thumb_refs.append(thumb)
                btn = tk.Button(
                    frame, image=thumb, command=lambda p=photo_path: do_import(p),
                    relief="flat", cursor="hand2"
                )
            except Exception as e:
                # 缩略图生成失败(比如格式PIL打不开)也不要直接跳过不显示，
                # 改成显示一个能点的占位按钮，点了会弹出具体错误，而不是"消失不见"
                logging.warning(f"缩略图生成失败({os.path.basename(photo_path)}): {e}")
                btn = tk.Button(
                    frame, text="⚠️\n无法预览\n(点击查看详情)", width=14, height=6,
                    command=lambda p=photo_path: do_import(p),
                    relief="flat", cursor="hand2", bg="#fdeceb"
                )
            btn.pack()
            ttk.Label(frame, text=os.path.basename(photo_path)[:16], font=("TkDefaultFont", 8)).pack()

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

    def on_patient_search_keyrelease(self, event):
        """搜索框输入时，弹出匹配的病人列表(姓名+RN)供选择"""
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        from modules.patient_directory import search_patients

        query = self.patient_search_entry.get()
        matches = search_patients(self.patients, query)[:15]  # 最多显示15条，避免下拉太长

        self.hide_patient_dropdown()
        if not matches or not query.strip():
            return

        x = self.patient_search_entry.winfo_rootx()
        y = self.patient_search_entry.winfo_rooty() + self.patient_search_entry.winfo_height()

        dropdown = tk.Toplevel(self.root)
        dropdown.wm_overrideredirect(True)
        dropdown.wm_geometry(f"+{x}+{y}")
        self._patient_dropdown = dropdown

        listbox = tk.Listbox(dropdown, width=35, height=min(len(matches), 8))
        for p in matches:
            listbox.insert(tk.END, f"{p.get('name','')}  ({p.get('mrn','')})")
        listbox.pack()

        def on_select(evt):
            sel = listbox.curselection()
            if sel:
                chosen = matches[sel[0]]
                self.patient_search_entry.delete(0, tk.END)
                self.patient_search_entry.insert(0, chosen.get("name", ""))
                self.mrn_entry.delete(0, tk.END)
                self.mrn_entry.insert(0, chosen.get("mrn", ""))
            self.hide_patient_dropdown()

        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Button-1>", lambda e: self.root.after(50, lambda: on_select(None)))

    def hide_patient_dropdown(self):
        if self._patient_dropdown is not None:
            try:
                self._patient_dropdown.destroy()
            except Exception:
                pass
            self._patient_dropdown = None

    def show_patient_manager(self):
        """病人名单管理弹窗: 增/删/改单个病人，也支持批量粘贴导入"""
        from modules.patient_directory import (
            save_patients, add_or_update_patient, remove_patient, parse_bulk_text
        )

        dialog = tk.Toplevel(self.root)
        dialog.title("病人名单管理 Manage Patients")
        dialog.geometry("480x520")
        dialog.transient(self.root)
        dialog.grab_set()

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== Tab1: 名单列表(可删除) =====
        list_tab = ttk.Frame(notebook)
        notebook.add(list_tab, text=f"名单 ({len(self.patients)}人)")

        listbox = tk.Listbox(list_tab)
        listbox.pack(fill="both", expand=True, padx=5, pady=5)

        def refresh_listbox():
            listbox.delete(0, tk.END)
            for p in sorted(self.patients, key=lambda x: x.get("name", "").upper()):
                listbox.insert(tk.END, f"{p.get('name','')}  —  {p.get('mrn','')}")
            notebook.tab(list_tab, text=f"名单 ({len(self.patients)}人)")

        refresh_listbox()

        def delete_selected():
            sel = listbox.curselection()
            if not sel:
                return
            text = listbox.get(sel[0])
            name = text.split("  —  ")[0]
            if messagebox.askyesno("确认删除", f"确定要删除病人 '{name}' 吗？"):
                self.patients = remove_patient(self.patients, name)
                save_patients(self.patients)
                refresh_listbox()

        ttk.Button(list_tab, text="🗑️ 删除选中 Delete Selected", command=delete_selected).pack(pady=5)

        # ===== Tab2: 新增/修改单个 =====
        add_tab = ttk.Frame(notebook)
        notebook.add(add_tab, text="新增/修改")

        ttk.Label(add_tab, text="病人姓名 Name:").pack(anchor=tk.W, padx=10, pady=(15, 2))
        name_entry = ttk.Entry(add_tab, width=35)
        name_entry.pack(padx=10)

        ttk.Label(add_tab, text="病历号 RN/MRN:").pack(anchor=tk.W, padx=10, pady=(10, 2))
        mrn_entry_new = ttk.Entry(add_tab, width=35)
        mrn_entry_new.pack(padx=10)

        def save_single():
            name = name_entry.get().strip()
            mrn = mrn_entry_new.get().strip()
            if not name or not mrn:
                messagebox.showwarning("提示", "姓名和病历号都要填")
                return
            self.patients = add_or_update_patient(self.patients, name, mrn)
            save_patients(self.patients)
            refresh_listbox()
            name_entry.delete(0, tk.END)
            mrn_entry_new.delete(0, tk.END)
            messagebox.showinfo("成功", f"已保存: {name} ({mrn})")

        ttk.Button(add_tab, text="💾 保存 Save", command=save_single).pack(pady=15)
        ttk.Label(
            add_tab, text="提示: 姓名如果已存在，会直接更新RN号码，\n不会出现重复的病人。",
            foreground="gray", justify=tk.LEFT
        ).pack(padx=10, anchor=tk.W)

        # ===== Tab3: 批量导入 =====
        bulk_tab = ttk.Frame(notebook)
        notebook.add(bulk_tab, text="批量导入")

        ttk.Label(
            bulk_tab,
            text="每行一个病人，姓名和RN用逗号/Tab/多个空格隔开，比如：\n"
                 "VIRAMUTHU, 24005403\nKOH HENG KEANG  23000139",
            justify=tk.LEFT, foreground="gray"
        ).pack(anchor=tk.W, padx=10, pady=10)

        bulk_text = tk.Text(bulk_tab, height=14, width=40)
        bulk_text.pack(padx=10, pady=5, fill="both", expand=True)

        def import_bulk():
            text = bulk_text.get("1.0", tk.END)
            parsed = parse_bulk_text(text)
            if not parsed:
                messagebox.showwarning("提示", "没有解析出任何有效的 姓名+RN 记录，请检查格式")
                return
            for p in parsed:
                self.patients = add_or_update_patient(self.patients, p["name"], p["mrn"])
            save_patients(self.patients)
            refresh_listbox()
            bulk_text.delete("1.0", tk.END)
            messagebox.showinfo("成功", f"已导入/更新 {len(parsed)} 位病人")

        ttk.Button(bulk_tab, text="📥 批量导入 Import", command=import_bulk).pack(pady=10)

    def upload_nursing_record(self):
        """上传护理记录纸照片"""
        filename = filedialog.askopenfilename(
            title="Select Nursing Record Photo 选择护理记录照片",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if filename:
            filename = self._load_and_normalize_image(filename)
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
            filename = self._load_and_normalize_image(filename)
            self.machine_image = filename
            self.current_image = filename
            self.display_image(filename)
            self.machine_status.config(text="Status: Image loaded 图片已加载", foreground="green")
            self.log(f"✓ Machine screen loaded 透析机照片已加载: {os.path.basename(filename)}")
            
    def _load_and_normalize_image(self, path):
        """
        按照片的EXIF方向信息把图片摆正。

        iPhone拍照时，实际存下来的像素往往是"横的"，靠一个EXIF方向标记告诉
        看图软件"显示的时候要转90度"——Windows的照片查看器、iPhone相册这些
        会自动读这个标记转正显示，但PIL/大部分图像处理库、包括丢给Gemini的
        原始字节，都不会自动处理这个标记，结果预览和AI识别看到的都是没转正
        的横图，AI把表格的行列看错了，才会出现"只读到一小时血压"这种情况。

        这里统一转正一次，存成新文件，之后不管是界面预览还是喂给AI识别，
        用的都是这份已经摆正的图，不会出现"预览是正的，AI看到的是横的"这种
        两边不一致的情况。转正失败的话(比如根本没有EXIF信息、或者不是图片
        文件)，就照常使用原图，不影响原本能正常工作的照片。
        """
        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)  # 按EXIF方向转正，同时清除方向标记避免被重复处理
        except Exception as e:
            logging.warning(f"读取/转正图片方向失败，改用原图: {path} ({e})")
            return path

        base, ext = os.path.splitext(path)
        ext_lower = ext.lower()
        if ext_lower not in (".jpg", ".jpeg", ".png"):
            ext_lower = ".jpg"  # 万一是heic等格式，转正后统一存成jpg，后续处理更省心
        normalized_path = f"{base}_upright{ext_lower}"

        try:
            if img.mode in ("RGBA", "P") and ext_lower in (".jpg", ".jpeg"):
                img = img.convert("RGB")
            img.save(normalized_path)
            return normalized_path
        except Exception as e:
            logging.warning(f"保存转正后的图片失败，改用原图: {path} ({e})")
            return path

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

    def _get_gemini_api_key(self):
        """获取Gemini API Key: 先看config.json里有没有存过，没有就弹窗问一次并询问是否保存"""
        config_path = "config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("gemini_api_key"):
                    return cfg["gemini_api_key"]
        except Exception as e:
            logging.warning(f"读取config.json失败: {e}")

        api_key = simpledialog.askstring(
            "Gemini API Key",
            "还没配置 Gemini API Key。\n"
            "免费申请: https://aistudio.google.com/apikey\n\n"
            "请输入你的 API Key:",
            show="*"
        )
        if not api_key:
            return None

        if messagebox.askyesno(
            "保存 Key？",
            "要把这个API Key保存到config.json，下次不用再输入吗？\n"
            "(会以明文存在本地文件里，请自行保管好这台电脑)"
        ):
            try:
                cfg = {}
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                cfg["gemini_api_key"] = api_key
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.warning(f"保存gemini_api_key到config.json失败: {e}")

        return api_key

    def _pick_daily_column_dialog(self, daily_columns):
        """有多个日期列时，弹一个小窗口让用户选要用哪一列"""
        if len(daily_columns) <= 1:
            return daily_columns[0] if daily_columns else None

        dialog = tk.Toplevel(self.root)
        dialog.title("选择日期 Select Date")
        dialog.geometry("320x260")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="识别到多个日期的数据，选择要加载哪一天：\n"
                         "Found multiple dates, pick one to load:"
        ).pack(pady=10, padx=10)

        listbox = tk.Listbox(dialog, height=8)
        for col in daily_columns:
            date_str = col.get("DATE", "") or "(无日期 no date)"
            hd_str = col.get("NUMBER_OF_HD", "")
            listbox.insert(tk.END, f"{date_str}   (HD#{hd_str})")
        listbox.select_set(len(daily_columns) - 1)  # 默认选最后一个(最新)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)

        result = {"chosen": None}

        def on_confirm():
            sel = listbox.curselection()
            if sel:
                result["chosen"] = daily_columns[sel[0]]
            dialog.destroy()

        ttk.Button(dialog, text="确定 OK", command=on_confirm).pack(pady=10)
        dialog.wait_window()
        return result["chosen"]

    def ocr_nursing_record_ai(self):
        """用AI视觉模型(Gemini)识别护理记录纸——尤其擅长手写数据"""
        if not self.nursing_image:
            messagebox.showwarning("Warning 警告", "Please upload nursing record image first\n请先上传护理记录照片")
            return

        api_key = self._get_gemini_api_key()
        if not api_key:
            self.log("ℹ️  未提供Gemini API Key，取消AI识别")
            return

        self.nursing_status.config(text="Status: AI Processing... AI识别中...", foreground="orange")
        self.log("⏳ Starting AI OCR (Gemini) for nursing record 开始AI识别护理记录...")

        try:
            from modules.privacy_redact import redact_sensitive_fields
            from modules.ai_ocr_module import GeminiNursingOCR, pick_target_column

            # 先在本地打码盖住 NAME/IC/RN，只把打码后的图发给Gemini，
            # 病人姓名/身份证号全程不会真正离开这台电脑
            self.log("🔒 正在本地打码敏感信息(NAME/IC/RN)...")
            redacted_path, redacted_count = redact_sensitive_fields(self.nursing_image)

            if redacted_count == 0:
                proceed = messagebox.askyesno(
                    "⚠️ 没有找到可打码的敏感信息",
                    "本地打码没有找到 NAME/IC/RN 这几个标签，"
                    "可能是这张照片的版式和预期不一样，或者角度/清晰度导致没识别到。\n\n"
                    "如果继续，原图会【不打码】直接发给Gemini。\n"
                    "确定要继续吗？\n\n"
                    "No sensitive labels found to redact. If you continue, "
                    "the ORIGINAL (unredacted) image will be sent to Gemini.\n"
                    "Continue anyway?"
                )
                if not proceed:
                    self.log("ℹ️  用户取消了AI识别(未找到可打码内容)")
                    self.nursing_status.config(text="Status: Cancelled 已取消", foreground="blue")
                    return
                image_to_send = self.nursing_image
            else:
                self.log(f"✓ 已打码 {redacted_count} 处敏感信息，发送打码后的图片")
                image_to_send = redacted_path

            ocr = GeminiNursingOCR(api_key=api_key)
            result = ocr.extract_nursing_record(image_to_send)
            self.update_gemini_usage_display()

            header = result.get("header", {})
            daily_columns = result.get("daily_columns", [])

            self.log(f"🔍 识别到表头字段 {sum(1 for v in header.values() if v)} 个，"
                      f"有数据的日期列 {len(daily_columns)} 个")

            if not daily_columns:
                messagebox.showwarning(
                    "No dated data 没有识别到日期数据",
                    "表头信息识别到了，但周表格里没找到任何有数据的日期列。\n"
                    "可能这张照片的周表格本身是空的，或者角度/清晰度不够。"
                )
                chosen_column = {}
            else:
                chosen_column = self._pick_daily_column_dialog(daily_columns) or {}

            # 合并表头 + 选中的日期列，一起填入UI
            combined_data = {**header, **chosen_column}

            filled_count = 0
            for key, value in combined_data.items():
                if key in self.basic_fields and value:
                    widget = self.basic_fields[key]
                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                        widget.insert("1.0", value)
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, value)
                    filled_count += 1
                    self.log(f"✓ [AI] Filled {key} = {value}")

            self.log(f"✅ [AI] Total fields filled: {filled_count}")
            self.nursing_status.config(text="Status: AI OCR completed ✓ AI识别完成", foreground="green")

            self.notebook.select(self.basic_data_tab)

            messagebox.showinfo(
                "AI OCR Complete AI识别完成",
                f"AI识别完成，填入了 {filled_count} 个字段！\n"
                "手写字可能有认不清的地方，字段值末尾带 '?' 的表示AI自己也不确定，\n"
                "请务必人工核对一遍再继续。\n\n"
                f"AI extraction completed with {filled_count} field(s) filled.\n"
                "Please verify carefully, especially any value ending with '?'."
            )

        except ImportError as e:
            self.nursing_status.config(text="Status: AI OCR failed ✗ AI识别失败", foreground="red")
            self.log(f"✗ AI OCR缺少依赖: {e}")

            missing_module = getattr(e, "name", None) or ""
            pip_hints = {
                "google": "pip install google-genai",
                "google.genai": "pip install google-genai",
                "pytesseract": "pip install pytesseract\n"
                                "  (还需要另外安装Tesseract引擎本体: "
                                "https://github.com/UB-Mannheim/tesseract/wiki)",
                "cv2": "pip install opencv-python",
                "PIL": "pip install Pillow",
            }
            hint = pip_hints.get(missing_module, f"pip install {missing_module}" if missing_module else "")

            messagebox.showerror(
                "Missing dependency 缺少依赖",
                f"{e}\n\n请先运行:\n{hint}" if hint else str(e)
            )
        except Exception as e:
            self.nursing_status.config(text="Status: AI OCR failed ✗ AI识别失败", foreground="red")
            self.log(f"✗ AI OCR Error AI识别错误: {str(e)}")
            logging.error(f"AI OCR nursing record error: {e}")
            self.update_gemini_usage_display()
            messagebox.showerror("Error 错误", f"AI OCR failed AI识别失败:\n{str(e)}")

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

    def ocr_machine_screen_ai(self):
        """用AI视觉模型(Gemini)识别透析机屏幕"""
        if not self.machine_image:
            messagebox.showwarning("Warning 警告", "Please upload machine screen image first\n请先上传透析机照片")
            return

        api_key = self._get_gemini_api_key()
        if not api_key:
            self.log("ℹ️  未提供Gemini API Key，取消AI识别")
            return

        self.machine_status.config(text="Status: AI Processing... AI识别中...", foreground="orange")
        self.log("⏳ Starting AI OCR (Gemini) for dialysis machine 开始AI识别透析机...")

        try:
            from modules.ai_ocr_module import GeminiMachineOCR

            # 透析机屏幕上不会有病人姓名/IC这类隐私信息，不需要打码这一步，直接发图
            ocr = GeminiMachineOCR(api_key=api_key)
            readings = ocr.extract_machine_screen(self.machine_image)
            self.update_gemini_usage_display()

            if not readings:
                messagebox.showwarning(
                    "Warning 警告",
                    "AI没有识别到任何数据。请尝试其他照片或手动添加。\n"
                    "No data extracted by AI. Please try another photo or add manually."
                )
                self.machine_status.config(text="Status: No data found 未识别到数据", foreground="orange")
                return

            # 按TIME跟已有的hourly_observations去重，重复的时间点不重复添加
            # 注意: 这里直接读表格(self.hourly_tree)里现在实际显示的内容，
            # 而不是另外维护一份list——之前维护的那份list(self.hourly_observations)
            # 只会一直往里加、从来不会因为你删除某一行或者点"清空病人资料/Next Patient"
            # 而跟着清掉，导致换了新病人之后，AI识别到的新数据会被"上一位病人"的
            # 旧时间点误判成重复而跳过。改成直接读表格，表格显示什么，去重就按什么算，
            # 不会再有两边数据对不上的问题。
            existing_times = set()
            for item in self.hourly_tree.get_children():
                row_values = self.hourly_tree.item(item)["values"]
                if row_values:
                    t = str(row_values[0]).strip()
                    if t:
                        existing_times.add(t)

            added_count = 0
            skipped_count = 0
            for reading in readings:
                t = str(reading.get("TIME", "")).strip()
                if t and t in existing_times:
                    skipped_count += 1
                    self.log(f"  ⏭️  跳过重复时间点 {t}(已存在)")
                    continue
                self.add_hourly_observation(reading)
                if t:
                    existing_times.add(t)
                added_count += 1

            self.machine_status.config(text="Status: AI OCR completed ✓ AI识别完成", foreground="green")
            self.log(
                f"✅ [AI] Machine screen extraction completed: "
                f"识别到 {len(readings)} 条记录，新增 {added_count} 条，跳过重复 {skipped_count} 条"
            )
            for reading in readings:
                t = str(reading.get("TIME", "")).strip()
                self.log(f"  ✓ [AI] TIME={t} BP={reading.get('BP','')} PULSE={reading.get('PULSE','')}")

            self.notebook.select(self.hourly_obs_tab)

            messagebox.showinfo(
                "Success 成功",
                f"AI识别完成！共识别到 {len(readings)} 条记录，"
                f"新增 {added_count} 条，跳过重复 {skipped_count} 条。\n请验证数据。\n\n"
                f"AI extraction completed: {len(readings)} reading(s) found, "
                f"{added_count} added, {skipped_count} duplicate(s) skipped.\nPlease verify."
            )

        except ImportError as e:
            self.machine_status.config(text="Status: AI OCR failed ✗ AI识别失败", foreground="red")
            self.log(f"✗ AI OCR缺少依赖: {e}")
            missing_module = getattr(e, "name", None) or ""
            pip_hints = {
                "google": "pip install google-genai",
                "google.genai": "pip install google-genai",
            }
            hint = pip_hints.get(missing_module, f"pip install {missing_module}" if missing_module else "")
            messagebox.showerror(
                "Missing dependency 缺少依赖",
                f"{e}\n\n请先运行:\n{hint}" if hint else str(e)
            )
        except Exception as e:
            self.machine_status.config(text="Status: AI OCR failed ✗ AI识别失败", foreground="red")
            self.log(f"✗ AI OCR Error AI识别错误: {str(e)}")
            logging.error(f"AI OCR machine screen error: {e}")
            self.update_gemini_usage_display()
            messagebox.showerror("Error 错误", f"AI OCR failed AI识别失败:\n{str(e)}")

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
        
    def add_hourly_row(self):
        """手动添加每小时记录行"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Hourly Observation 添加每小时记录")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # VP跟着第一条已有记录走(不是每小时都会变的机器设置)，
        # 没有已有记录的话才用160这个通用示例值兜底
        # (直接读表格里现在显示的第一行，而不是另外维护的一份list——
        # 原因同上面的去重逻辑，避免读到"上一位病人"遗留的旧数据)
        default_vp = "160"
        existing_rows = self.hourly_tree.get_children()
        if existing_rows:
            first_values = self.hourly_tree.item(existing_rows[0])["values"]
            if len(first_values) > 2 and str(first_values[2]).strip():
                default_vp = str(first_values[2]).strip()
        
        fields = {}
        labels = [
            ("TIME", "Time 时间 (HH:MM)", "07:10"),
            ("BP", "BP 血压 (SYS/DIA)", "217/107"),
            ("VP", "VP 静脉压", default_vp),
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

            # VP这类机器设置整个疗程通常是固定的：如果编辑的是第一行，
            # 就把新的VP值同步到其他所有行，不用每一行都手动改一遍
            all_items = self.hourly_tree.get_children()
            if all_items and selected[0] == all_items[0]:
                new_vp = fields["VP"].get()
                if new_vp:
                    synced_count = 0
                    for item in all_items:
                        if item == selected[0]:
                            continue
                        row_values = list(self.hourly_tree.item(item)["values"])
                        if len(row_values) > 2 and row_values[2] != new_vp:
                            row_values[2] = new_vp  # VP是第3列(index 2)
                            self.hourly_tree.item(item, values=row_values)
                            synced_count += 1
                    if synced_count:
                        self.log(f"  ↳ VP已同步到其他 {synced_count} 行")

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

    def move_hourly_row_up(self):
        """把选中的每小时记录行往上移一行(方便手动补漏的行插到正确的时间顺序里)"""
        selected = self.hourly_tree.selection()
        if not selected:
            messagebox.showwarning("Warning 警告", "Please select a row first\n请先选择一行")
            return
        item = selected[0]
        idx = self.hourly_tree.index(item)
        if idx == 0:
            return  # 已经是第一行了
        self.hourly_tree.move(item, "", idx - 1)

    def move_hourly_row_down(self):
        """把选中的每小时记录行往下移一行"""
        selected = self.hourly_tree.selection()
        if not selected:
            messagebox.showwarning("Warning 警告", "Please select a row first\n请先选择一行")
            return
        item = selected[0]
        idx = self.hourly_tree.index(item)
        if idx >= len(self.hourly_tree.get_children()) - 1:
            return  # 已经是最后一行了
        self.hourly_tree.move(item, "", idx + 1)

    def collect_all_data(self):
        """收集所有数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "basic_data": {},
            "hourly_observations": []
        }
        
        # 收集基本数据
        # 注意: REMARKS等文本框(tk.Text)的初始placeholder是空字符串"", 天然不会有这个问题；
        # Combobox(COMFORTABLE等)、Entry这些如果用户完全没碰过，内容还是初始示例值，
        # 要跳过、不当作真实数据提交，不然会把"233/107"这种示例数字误填进病人的表格里。
        for key, widget in self.basic_fields.items():
            original_placeholder = self.basic_field_placeholders.get(key, "")
            try:
                if isinstance(widget, tk.Text):
                    value = widget.get("1.0", tk.END).strip()
                    if value and value != original_placeholder:
                        data["basic_data"][key] = value
                else:
                    value = widget.get()
                    # 跳过占位符文字本身(以防万一)，以及内容跟初始示例值完全一样(没被改过)的字段
                    if (
                        value
                        and not any(ph in value for ph in ["e.g.", "例如:"])
                        and value != original_placeholder
                    ):
                        data["basic_data"][key] = value
            except:
                pass  # 读取失败就当作没填，不要塞一个空字符串进去(空字符串也会被当成"有填"而覆盖已有数据)
                
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

        # 分开检查，给出具体缺了什么的提示——而不是笼统地说"请填写Origin登录信息"，
        # 不然账密明明填好了，只是忘了搜索/选择病人，也会被误导去检查账密。
        missing = []
        if not username or not password:
            missing.append("Origin用户名/密码 Origin username/password")
        if not mrn:
            missing.append("病人 MRN (请先在上面的\"搜索病人 Search Patient\"框里搜索并选择) Patient MRN (search & select a patient above first)")

        if missing:
            messagebox.showwarning(
                "Warning 警告",
                "还缺少以下信息 Missing the following before Auto Fill Data can run:\n\n"
                + "\n".join(f"• {m}" for m in missing)
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
        
    def show_batch_fill_dialog(self):
        """
        批量填入弹窗：让用户依次挑选"病人 + 该病人对应的数据JSON文件"，
        组成一个处理队列，一次性登录Origin后依次自动填入每一位病人。

        每个病人的数据来自之前用 Export JSON 导出的文件(基本数据+每小时记录)，
        病人身份来自 patients.json 名单(姓名<->MRN)，不用每次手动记/输入MRN。
        """
        from modules.patient_directory import search_patients

        dialog = tk.Toplevel(self.root)
        dialog.title("批量填入 Batch Auto-Fill")
        dialog.geometry("700x640")
        dialog.minsize(560, 480)
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        # ===== 登录信息 =====
        login_frame = ttk.LabelFrame(dialog, text="Origin 登录信息 Login", padding=10)
        login_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(login_frame, text="Username 用户名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        # 直接绑定同一个StringVar(跟主界面共用)，不再是"打开弹窗时复制一次"，
        # 这样不管在主界面还是在这个弹窗里填账密，两边永远保持一致。
        batch_user_entry = ttk.Entry(login_frame, width=28, textvariable=self.origin_username_var)
        batch_user_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(login_frame, text="Password 密码:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        batch_pass_entry = ttk.Entry(login_frame, width=28, show="*", textvariable=self.origin_password_var)
        batch_pass_entry.grid(row=1, column=1, padx=5, pady=3)

        # ===== 底部固定操作区(操作按钮 + 提示 + 开始按钮) =====
        # 关键: 这里必须先打包(pack)、且用 side="bottom"，再打包下面会撑开的
        # 病人队列列表。这样无论队列里有多少病人、提示文字多长，这个区域
        # (尤其是"开始批量填入"按钮)永远固定显示在弹窗底部，不会被挤出
        # 弹窗的可视范围之外看不到。
        # 这几个按钮的command用lambda延迟到"真正被点击的那一刻"才去找
        # add_job/remove_selected/move_up/move_down/start_batch这些函数，
        # 所以即使这些函数要到后面才会被定义，这里也能先把按钮建出来。
        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(side="bottom", fill="x")

        action_bar = ttk.Frame(bottom_frame)
        action_bar.pack(fill="x", padx=10, pady=(5, 5))
        ttk.Button(action_bar, text="➕ 从JSON添加 Add from JSON", command=lambda: add_job()).pack(side="left", padx=3)
        ttk.Button(action_bar, text="🗑️ 删除选中 Remove", command=lambda: remove_selected()).pack(side="left", padx=3)
        ttk.Button(action_bar, text="⬆️ 上移 Up", command=lambda: move_up()).pack(side="left", padx=3)
        ttk.Button(action_bar, text="⬇️ 下移 Down", command=lambda: move_down()).pack(side="left", padx=3)

        ttk.Label(
            bottom_frame,
            text="💡 提示：在左侧主界面OCR识别完一位病人后，点\"加入批量队列\"即可直接加进这里，"
                 "不用先导出JSON再手动导入。这里的 Add from JSON 只是备用方式。\n"
                 "Tip: after OCR'ing a patient on the main screen, click \"Add to Batch Queue\" to "
                 "add them here directly — no need to export/re-import JSON. \"Add from JSON\" is a fallback.",
            foreground="gray", wraplength=640, justify="left"
        ).pack(fill="x", padx=10, pady=(0, 5))

        ttk.Button(
            bottom_frame, text="🚀 开始批量填入 Start Batch Auto-Fill",
            command=lambda: start_batch()
        ).pack(pady=(0, 10))

        # ===== 病人队列列表 =====
        list_frame = ttk.LabelFrame(dialog, text="待处理病人队列 Patient Queue (按顺序处理)", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("NAME", "MRN", "JSON_FILE")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        tree.heading("NAME", text="病人姓名 Name")
        tree.heading("MRN", text="MRN")
        tree.heading("JSON_FILE", text="数据来源 Source")
        tree.column("NAME", width=170)
        tree.column("MRN", width=90, anchor="center")
        tree.column("JSON_FILE", width=320)
        tree.pack(fill="both", expand=True, side="left")

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=list_scrollbar.set)
        list_scrollbar.pack(side="right", fill="y")

        def _job_source_label(j):
            """队列里每一行显示的'来源': 表单直接加入的没有json_path，
            从JSON文件加入的显示文件名。"""
            jp = j.get("json_path")
            return os.path.basename(jp) if jp else "📝 表单直接加入 In-app form"

        # 直接复用 self.batch_queue 这个列表对象(不是拷贝)，
        # 这样在这个弹窗里增删的结果会同步回主界面的队列，
        # 主界面上"➕ 加入批量队列"加进来的病人也会直接显示在这里。
        jobs = self.batch_queue
        for j in jobs:
            tree.insert("", "end", values=(j["name"], j["mrn"], _job_source_label(j)))

        def add_job():
            """子弹窗: 搜索病人 + 选该病人的JSON数据文件，确认后加入队列"""
            sub = tk.Toplevel(dialog)
            sub.title("添加病人 Add Patient")
            sub.geometry("420x340")
            sub.transient(dialog)
            sub.grab_set()

            ttk.Label(sub, text="搜索病人姓名/MRN Search:").pack(anchor=tk.W, padx=12, pady=(15, 2))
            search_entry = ttk.Entry(sub, width=38)
            search_entry.pack(padx=12)
            search_entry.focus_set()

            result_listbox = tk.Listbox(sub, height=6)
            result_listbox.pack(fill="x", padx=12, pady=6)

            matches_holder = {"matches": []}

            def on_search(event=None):
                q = search_entry.get()
                matches = search_patients(self.patients, q)[:12]
                matches_holder["matches"] = matches
                result_listbox.delete(0, tk.END)
                for p in matches:
                    result_listbox.insert(tk.END, f"{p.get('name', '')}  ({p.get('mrn', '')})")

            search_entry.bind("<KeyRelease>", on_search)
            on_search()  # 一打开就显示全部名单，方便直接挑选

            selected_patient = {"name": None, "mrn": None}

            def on_pick(event=None):
                sel = result_listbox.curselection()
                if sel:
                    p = matches_holder["matches"][sel[0]]
                    selected_patient["name"] = p.get("name")
                    selected_patient["mrn"] = p.get("mrn")
                    picked_label.config(
                        text=f"已选择: {selected_patient['name']} ({selected_patient['mrn']})",
                        foreground="green"
                    )

            result_listbox.bind("<<ListboxSelect>>", on_pick)

            picked_label = ttk.Label(sub, text="尚未选择病人 No patient selected", foreground="gray")
            picked_label.pack(anchor=tk.W, padx=12, pady=(0, 8))

            json_path_var = tk.StringVar()
            ttk.Label(sub, text="该病人的数据JSON文件 Data JSON file:").pack(anchor=tk.W, padx=12, pady=(4, 2))
            path_frame = ttk.Frame(sub)
            path_frame.pack(fill="x", padx=12)
            ttk.Entry(path_frame, textvariable=json_path_var, width=30).pack(side="left", fill="x", expand=True)

            def browse_json():
                fn = filedialog.askopenfilename(
                    title="选择数据JSON文件 Select data JSON",
                    initialdir="data/exports",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                if fn:
                    json_path_var.set(fn)

            ttk.Button(path_frame, text="浏览 Browse...", command=browse_json).pack(side="left", padx=5)

            def confirm_add():
                if not selected_patient["mrn"]:
                    messagebox.showwarning("提示 Notice", "请先从列表中选择一位病人\nPlease select a patient from the list")
                    return
                json_path = json_path_var.get()
                if not json_path or not os.path.exists(json_path):
                    messagebox.showwarning("提示 Notice", "请选择一个有效的数据JSON文件\nPlease select a valid data JSON file")
                    return
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    messagebox.showerror("错误 Error", f"无法读取JSON文件 Could not read JSON file:\n{e}")
                    return

                # 允许同一次批量里对同一个病人重复添加(比如分两份文件)，
                # 但至少要有basic_data或hourly_observations之一，不然填了也是空的
                if not data.get("basic_data") and not data.get("hourly_observations"):
                    if not messagebox.askyesno(
                        "数据为空？ Empty data?",
                        "这个JSON文件里basic_data和hourly_observations都是空的，\n"
                        "确定还要加入队列吗？\n\nThis file appears to have no data. Add anyway?"
                    ):
                        return

                jobs.append({
                    "mrn": selected_patient["mrn"],
                    "name": selected_patient["name"],
                    "data": data,
                    "json_path": json_path
                })
                tree.insert("", "end", values=(
                    selected_patient["name"], selected_patient["mrn"], os.path.basename(json_path)
                ))
                self.update_batch_queue_label()
                sub.destroy()

            ttk.Button(sub, text="✅ 添加到队列 Add to Queue", command=confirm_add).pack(pady=15)

        def remove_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("提示 Notice", "请先选择要删除的一行\nPlease select a row first")
                return
            for item in sel:
                idx = tree.index(item)
                tree.delete(item)
                del jobs[idx]
            self.update_batch_queue_label()

        def move_up():
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            if idx == 0:
                return
            jobs[idx - 1], jobs[idx] = jobs[idx], jobs[idx - 1]
            _refresh_tree()
            tree.selection_set(tree.get_children()[idx - 1])

        def move_down():
            sel = tree.selection()
            if not sel:
                return
            idx = tree.index(sel[0])
            if idx >= len(jobs) - 1:
                return
            jobs[idx + 1], jobs[idx] = jobs[idx], jobs[idx + 1]
            _refresh_tree()
            tree.selection_set(tree.get_children()[idx + 1])

        def _refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            for j in jobs:
                tree.insert("", "end", values=(j["name"], j["mrn"], _job_source_label(j)))

        def start_batch():
            if not jobs:
                messagebox.showwarning("提示 Notice", "还没有添加任何病人\nNo patients added yet")
                return
            username = batch_user_entry.get()
            password = batch_pass_entry.get()
            if not username or not password:
                messagebox.showwarning("提示 Notice", "请填写Origin用户名和密码\nPlease enter Origin username and password")
                return

            names_preview = "\n".join(f"  {i+1}. {j['name']} ({j['mrn']})" for i, j in enumerate(jobs))
            if not messagebox.askyesno(
                "确认批量填入 Confirm Batch Auto-Fill",
                f"即将依次自动处理以下 {len(jobs)} 位病人：\n\n{names_preview}\n\n"
                "整个过程会自动操作浏览器(登录/查找病人/填表/保存)，\n"
                "过程中请不要手动点击或关闭浏览器窗口。\n\n确定开始吗？"
            ):
                return

            dialog.destroy()
            self._run_batch_in_background(username, password, jobs)

    def _run_batch_in_background(self, username, password, jobs):
        """
        在后台线程运行批量自动化，避免Selenium的等待时间把tkinter主界面卡死。
        日志通过 self.root.after(0, ...) 转发回主线程更新，
        因为tkinter的控件不是线程安全的，不能从子线程里直接操作。
        """
        self.notebook.select(self.log_tab)
        self.log(f"📦 开始批量填入，共 {len(jobs)} 位病人 Starting batch for {len(jobs)} patient(s)...")

        def progress_callback(msg):
            self.root.after(0, lambda m=msg: self.log(m))

        def worker():
            try:
                from modules.origin_automation import OriginAutomation
                origin = OriginAutomation(self.config.get("origin_url"))
                results = origin.run_batch_automation(
                    username, password, jobs, callback=progress_callback
                )

                def show_summary():
                    total = len(jobs)
                    success_mrns = {r.get("mrn") for r in results if r.get("success")}
                    success = len(success_mrns)
                    lines = []
                    for r in results:
                        mark = "✅" if r.get("success") else "❌"
                        extra = f" — {r['reason']}" if r.get("reason") else ""
                        lines.append(f"{mark} {r.get('name')} (MRN {r.get('mrn')}){extra}")
                    summary_text = "\n".join(lines) if lines else "(没有处理结果 No results)"

                    # 成功的病人从队列移除；失败的留在队列里，方便直接重试而不用重新做一次OCR
                    # Remove succeeded patients from the queue; keep failures queued so they can
                    # be retried directly without redoing OCR.
                    self.batch_queue[:] = [j for j in self.batch_queue if j["mrn"] not in success_mrns]
                    self.update_batch_queue_label()

                    retry_note = (
                        "\n\n⚠️ 处理失败的病人仍留在队列中，可直接重试。\n"
                        "Failed patients remain in the queue and can be retried directly."
                        if success < total else ""
                    )
                    messagebox.showinfo(
                        "批量填入完成 Batch Auto-Fill Complete",
                        f"共 {total} 位病人，成功 {success} 位。\n"
                        f"Total {total}, succeeded {success}.\n\n{summary_text}{retry_note}\n\n"
                        "请务必在Origin系统里逐一核对数据。\n"
                        "Please verify the data in Origin for each patient."
                    )

                self.root.after(0, show_summary)

            except Exception as e:
                logging.error(f"Batch automation error: {e}")
                err_msg = str(e)
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "错误 Error", f"批量填入过程中出错 Batch automation failed:\n{err_msg}"
                    )
                )

        threading.Thread(target=worker, daemon=True).start()

    def _clear_form_fields(self, clear_patient=False):
        """清空表单/图片(共用逻辑)，不动批量队列。
        Shared logic to clear the form/images. Never touches the batch queue.
        clear_patient=True 时连搜索到的病人姓名/MRN也一起清掉(准备处理下一位病人时用)。
        """
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

        if clear_patient:
            self.patient_search_entry.delete(0, tk.END)
            self.mrn_entry.delete(0, tk.END)

    def reset_all(self):
        """重置所有数据(不影响已加入批量队列的病人)"""
        if messagebox.askyesno(
            "Confirm 确认",
            "Reset all data? This cannot be undone.\n"
            "(批量队列里已加入的病人不受影响 Patients already in the batch queue are not affected)\n"
            "重置所有数据？此操作无法撤销。"
        ):
            self._clear_form_fields(clear_patient=True)
            self.log("🔄 All data reset 所有数据已重置")

    def update_batch_queue_label(self):
        """刷新队列数量显示"""
        n = len(self.batch_queue)
        self.batch_queue_label.config(
            text=f"队列 Queue: {n} 位 patient(s)",
            foreground=("green" if n else "gray")
        )

    def add_to_batch_queue(self):
        """
        把当前已经OCR/编辑好的病人数据直接加入批量队列。
        跳过"导出JSON → 再手动导入"这一步，护理师做完一位病人的OCR和核对后
        点一下这个按钮就好，接着可以直接清空表单处理下一位病人。

        Push the currently OCR'd/edited patient data straight into the batch
        queue — no need to export a JSON file and re-import it. After OCR and
        review, the nurse just clicks this once, then clears the form and
        moves on to the next patient's photos.
        """
        name = self.patient_search_entry.get().strip()
        mrn = self.mrn_entry.get().strip()

        if not mrn:
            messagebox.showwarning(
                "提示 Notice",
                "请先搜索并选择病人(或至少填入MRN)再加入队列\n"
                "Please search/select a patient (or at least enter an MRN) before adding to the queue"
            )
            return

        data = self.collect_all_data()
        if not data.get("basic_data") and not data.get("hourly_observations"):
            if not messagebox.askyesno(
                "数据为空？ Empty data?",
                "当前基本数据和每小时记录都是空的，\n确定还要加入队列吗？\n\n"
                "Both basic data and hourly observations are currently empty. Add anyway?"
            ):
                return

        display_name = name or mrn

        # 队列里已经有同一个MRN时，询问是否用当前数据覆盖(避免重复处理同一人两次)
        for i, job in enumerate(self.batch_queue):
            if job["mrn"] == mrn:
                if messagebox.askyesno(
                    "已在队列中 Already in queue",
                    f"{display_name} 已经在队列里了，是否用目前表单的数据覆盖？\n\n"
                    f"{display_name} is already in the queue. Replace it with the current form data?"
                ):
                    self.batch_queue[i] = {"mrn": mrn, "name": display_name, "data": data}
                    self.update_batch_queue_label()
                    self.log(f"🔁 已更新队列中的病人 Updated in queue: {display_name} ({mrn})")
                return

        self.batch_queue.append({"mrn": mrn, "name": display_name, "data": data})
        self.update_batch_queue_label()
        self.log(
            f"➕ 已加入批量队列 Added to batch queue: {display_name} ({mrn}) "
            f"— 队列共 {len(self.batch_queue)} 位 total"
        )

        if messagebox.askyesno(
            "已加入队列 Added to Queue",
            f"{display_name} 已加入批量队列（当前共 {len(self.batch_queue)} 位）。\n\n"
            "是否清空表单，准备处理下一位病人？(不会影响队列里的数据)\n\n"
            f"{display_name} was added to the batch queue ({len(self.batch_queue)} total).\n\n"
            "Clear the form now to start the next patient? (Won't affect data already queued)"
        ):
            self._reset_form_for_next_patient()

    def _reset_form_for_next_patient(self):
        """清空表单准备处理下一位病人，但保留批量队列。
        Clear the form for the next patient without touching the batch queue."""
        self._clear_form_fields(clear_patient=True)
        self.log("➡️ 表单已清空，可以开始下一位病人 Form cleared, ready for the next patient")

    def clear_current_patient(self):
        """
        清空当前病人的资料(搜索框/MRN/基本数据/每小时记录/图片)，方便直接输入下一位病人。
        跟"加入批量队列"没有关系——不管你是不是在用批量流程，都可以随时点这个开始下一位。
        不会影响已经加入批量队列的数据。

        Clear the current patient's data (search box/MRN/basic data/hourly obs/images)
        so you can start entering the next patient right away. Independent of the batch
        queue flow — usable any time, and doesn't touch data already added to the queue.
        """
        name = self.patient_search_entry.get().strip()
        mrn = self.mrn_entry.get().strip()
        has_data = bool(name or mrn or self.collect_all_data().get("basic_data")
                         or self.hourly_tree.get_children())

        if has_data and not messagebox.askyesno(
            "确认清空 Confirm Clear",
            "确定要清空当前病人的资料吗？(搜索框/MRN/基本数据/每小时记录/图片都会被清空)\n"
            "如果这位病人的数据还没加入批量队列或填入Origin，清空后就找不回来了。\n\n"
            "Clear the current patient's data? (search box/MRN/basic data/hourly obs/"
            "images will all be cleared)\nIf this patient hasn't been added to the batch "
            "queue or filled into Origin yet, this can't be undone."
        ):
            return

        self._clear_form_fields(clear_patient=True)
        self.log("🧹 已清空当前病人资料，可以输入下一位病人了 Cleared current patient, ready for the next one")


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