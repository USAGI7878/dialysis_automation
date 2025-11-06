🏥 Dialysis Data Automation System | 透析数据自动化系统
<div align="center">
Show Image
Show Image
Show Image

🌍 English | 中文

Automated OCR and data entry solution for hemodialysis treatment records
透析治疗记录的自动OCR识别和数据录入解决方案

</div>
<a name="english"></a>

📖 English Documentation
📋 Table of Contents
Overview
Key Features
Demo
System Requirements
Quick Start
User Guide
Project Structure
Configuration
FAQ
Roadmap
Contributing
License
Contact
🎯 Overview
This is an automated data entry system designed specifically for hemodialysis units. It uses OCR (Optical Character Recognition) technology to recognize nursing records and dialysis machine screens, automatically filling data into the hospital's Origin system, significantly reducing nurses' manual data entry workload.

Background & Motivation
👩‍⚕️ Nurses manually enter massive amounts of dialysis data daily
📄 Data sources: Paper nursing records + dialysis machine screen photos
⏰ Time-consuming, error-prone, repetitive work
💡 Solution: OCR automatic recognition + automated form filling
Why This Project?
As a nurse learning programming, I created this tool to:

🎯 Solve real-world problems in healthcare
🚀 Reduce colleagues' workload
💻 Apply programming skills to nursing practice
🌟 Bridge technology and healthcare
✨ Key Features
📸 OCR Recognition
✅ Nursing Record Recognition: Auto-extract date, blood pressure, weight, dialysis parameters
✅ Machine Screen Recognition: Extract hourly observations (BP, VP, QB, QD, Pulse, UFR)
✅ High Accuracy: Powered by EasyOCR engine with English support
✅ Smart Fault Tolerance: Supports multiple date and number formats
🤖 Automated Data Entry
✅ Automatic Origin System Login
✅ Auto-navigation to Dialysis Treatment Record Page
✅ Automatic Patient Search (via MRN)
✅ Batch Fill Basic Data and Hourly Observations
✅ Auto-save
💾 Data Management
✅ Data Export: JSON format for easy backup and sharing
✅ Data Import: Quickly restore previous records
✅ Data Validation: Manual correction after recognition
✅ Operation Logging: Complete audit trail
🌐 User Interface
✅ Bilingual Interface: English + 中文
✅ Intuitive Operation: Complete data entry in 3 steps
✅ Image Preview: Real-time view of uploaded photos
✅ Live Logging: Monitor each operation status
🎬 Demo
Main Interface
┌─────────────────────────────────────────────────────────┐
│  🏥 Dialysis Data Automation System                     │
│  Version 1.0.0 | For KLSCH Haemodialysis Unit          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Steps          │  Image Preview  │  Data Editor       │
│  ──────────────│  ─────────────  │  ───────────────   │
│  Step 1:        │                 │  Basic Data:       │
│  ✓ Upload Photo │   [Preview]     │  • Date: 08-10-25  │
│  ✓ Start OCR    │                 │  • Pre BP: 233/107 │
│                 │                 │  • Weight: 71.15kg │
│  Step 2:        │                 │  ...               │
│  ✓ Upload Photo │                 │                     │
│  ✓ Extract Obs  │                 │  Hourly Obs:       │
│                 │                 │  07:10 - BP 217/107│
│  Step 3:        │                 │  08:10 - BP 205/98 │
│  ✓ Auto Fill    │                 │  ...               │
└─────────────────────────────────────────────────────────┘
Workflow Diagram
📷 Photo → 🔍 OCR → ✏️ Verify → 🤖 Auto-fill → ✅ Done
💻 System Requirements
Required
Python 3.8+ (Download)
Windows 10/11 (Recommended) or Linux/Mac
4GB RAM (Minimum)
500MB Disk Space (for models)
Chrome Browser (for automation)
Network Requirements
Access to hospital Origin system
Internet connection for first run (download OCR models)
🚀 Quick Start
Method 1: One-Click Launch (Recommended for Beginners)
Clone the Repository
bash
git clone https://github.com/USAGI7878/dialysis-automation.git
cd dialysis-automation
Double-click start.bat
✅ Auto-create virtual environment
✅ Auto-install dependencies
✅ Auto-launch application
Method 2: Manual Installation
Clone the Repository
bash
git clone https://github.com/USAGI7878/dialysis-automation.git
cd dialysis-automation
Create Virtual Environment
bash
python -m venv venv
Activate Virtual Environment
bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
Install Dependencies
bash
pip install -r requirements.txt
Configure Origin URL
Edit config.json:

json
{
  "origin_url": "https://your-origin-system-url.com"
}
Run Application
bash
python main.py
📖 User Guide
Workflow
1️⃣ Take photo of nursing record
   ↓
2️⃣ Upload photo → OCR recognition
   ↓
3️⃣ Verify/correct data
   ↓
4️⃣ Take photos of dialysis machine screen (multiple time points)
   ↓
5️⃣ Upload photos → OCR hourly observations
   ↓
6️⃣ Verify data
   ↓
7️⃣ Enter Origin login credentials + Patient MRN
   ↓
8️⃣ Click "Auto Fill Data"
   ↓
9️⃣ ✅ Complete!
Detailed Steps
Step 1: Nursing Record OCR
Click "📄 Upload Photo"
Select nursing record photo
Click "🔍 Start OCR"
Verify data in "Basic Data" tab
Manually correct any recognition errors
Step 2: Dialysis Machine Screen OCR
Click "📱 Upload Photo"
Select machine screen photo
Click "🔍 Extract Hourly Obs"
Repeat for different time points
Verify data in "Hourly Obs" tab
Step 3: Auto-fill Origin
Enter Origin username and password
Enter Patient MRN
Click "🚀 Auto Fill Data"
Wait for automation to complete (check logs)
Verify data in Origin system
📸 Photo Tips
For Best OCR Results:

✅ DO:

Good lighting, avoid shadows
Shoot straight-on, avoid tilting
Clear focus, readable text
Include complete table area
❌ DON'T:

Glare or overexposure
Blurry images
Extreme angles
Fingers covering text
📁 Project Structure
dialysis-automation/
│
├── 📄 main.py                  # Main entry point
├── 📄 config.json             # Configuration file
├── 📄 requirements.txt        # Python dependencies
├── 📄 start.bat               # One-click launcher (Windows)
├── 📄 README.md               # This file
├── 📄 LICENSE                 # MIT License
│
├── 📂 modules/                # Core modules
│   ├── __init__.py
│   ├── ocr_module.py          # OCR recognition
│   ├── origin_automation.py   # Origin automation
│   └── data_processor.py      # Data processing (TBD)
│
├── 📂 data/                   # Data folder
│   ├── exports/               # Exported JSON files
│   └── temp/                  # Temporary files
│
├── 📂 logs/                   # Log folder
│   └── automation.log         # Operation log
│
└── 📂 docs/                   # Documentation
    └── screenshots/           # Screenshots
⚙️ Configuration
config.json
json
{
  "origin_url": "http://192.168.20.11:8080/EMR/main.jsp",
  "ocr_settings": {
    "use_gpu": false,
    "confidence_threshold": 0.5
  },
  "selenium_settings": {
    "headless": false,
    "implicit_wait": 10
  }
}
❓ FAQ
Q1: OCR Recognition Not Accurate?
A:

Ensure photo is clear with good lighting
Avoid glare and shadows
Manually correct errors after recognition
Can edit directly in "Data Editor"
Q2: Origin Automation Failed?
A:

Check network connection
Verify username and password
Confirm patient MRN exists
Check logs/automation.log for details
Q3: Can I Use at Home?
A:

✅ Can perform OCR and data editing
❌ Cannot auto-fill Origin (requires hospital network)
💡 Suggestion: Recognize data at home, export JSON, import and auto-fill at hospital
🗺️ Roadmap
✅ Completed (v1.0.0)
 Nursing record OCR
 Machine screen OCR
 Origin system automation
 Bilingual UI
 Data import/export
🚧 In Progress (v1.1.0)
 Improve OCR accuracy
 Batch processing for multiple patients
 Data statistics and reports
📅 Planned (v2.0.0)
 Cloud storage and sync
 Mobile app version
 AI-assisted data validation
🤝 Contributing
Contributions, bug reports, and feature requests are welcome!

How to Contribute
Fork this repository
Create feature branch (git checkout -b feature/AmazingFeature)
Commit changes (git commit -m 'Add AmazingFeature')
Push to branch (git push origin feature/AmazingFeature)
Create Pull Request
📜 License
This project is licensed under the MIT License - see LICENSE file for details.

👨‍💻 Author
Your Name - Healthcare IT Nurse
📧 Email: your.email@example.com
🔗 GitHub: @yourusername

🙏 Acknowledgments
Thanks to EasyOCR for excellent OCR engine
Thanks to Selenium for browser automation
Thanks to all nursing colleagues for testing and feedback
<div align="center">
⭐ If this project helps you, please give it a Star!

Made with ❤️ by a Nurse who codes

</div>
<a name="中文"></a>

📖 中文文档
📋 目录
项目简介
核心功能
演示
系统要求
快速开始
使用指南
项目结构
配置说明
常见问题
开发路线图
贡献指南
许可证
联系方式
🎯 项目简介
这是一个专为血液透析单位设计的自动化数据录入系统。通过 OCR（光学字符识别）技术识别护理记录纸和透析机屏幕，自动填入医院的 Origin 系统，大幅减少护理师的手工录入工作量。

背景与动机
👩‍⚕️ 护理师每天需要手工录入大量透析数据
📄 数据来源：纸质护理记录 + 透析机屏幕照片
⏰ 耗时长、易出错、重复劳动
💡 解决方案：OCR 自动识别 + 自动化填表
为什么开发这个项目？
作为一名正在学习编程的护理师，我创建这个工具是为了：

🎯 解决医疗工作中的实际问题
🚀 减轻同事们的工作负担
💻 将编程技能应用到护理实践中
🌟 连接技术与医疗
✨ 核心功能
📸 OCR 识别
✅ 护理记录纸识别：自动提取日期、血压、体重、透析参数等
✅ 透析机屏幕识别：提取每小时观察数据（BP, VP, QB, QD, Pulse, UFR）
✅ 高准确率：使用 EasyOCR 引擎，支持英文识别
✅ 智能容错：支持多种日期和数字格式
🤖 自动化填表
✅ Origin 系统自动登录
✅ 自动导航到透析治疗记录页面
✅ 自动查找病人（通过 MRN）
✅ 批量填写基本数据和每小时观察记录
✅ 自动保存
💾 数据管理
✅ 数据导出：JSON 格式，方便备份和分享
✅ 数据导入：快速恢复之前的记录
✅ 数据验证：识别后可手动修正
✅ 日志记录：完整的操作日志
🌐 用户界面
✅ 双语界面：中文 + English
✅ 直观操作：三步完成数据录入
✅ 图片预览：实时查看上传的照片
✅ 实时日志：查看每一步操作状态
🎬 演示
主界面
┌─────────────────────────────────────────────────────────┐
│  🏥 透析数据自动化系统                                   │
│  版本 1.0.0 | 适用于 KLSCH 透析单位                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  操作步骤        │  图片预览      │  数据编辑器         │
│  ──────────────│  ───────────── │  ────────────────   │
│  步骤 1:        │                │  基本数据:          │
│  ✓ 上传照片     │   [预览区]     │  • 日期: 08-10-25   │
│  ✓ 开始识别     │                │  • 治疗前BP: 233/107│
│                 │                │  • 体重: 71.15kg    │
│  步骤 2:        │                │  ...                │
│  ✓ 上传照片     │                │                     │
│  ✓ 提取记录     │                │  每小时记录:        │
│                 │                │  07:10 - BP 217/107 │
│  步骤 3:        │                │  08:10 - BP 205/98  │
│  ✓ 自动填入     │                │  ...                │
└─────────────────────────────────────────────────────────┘
工作流程图
📷 拍照 → 🔍 OCR识别 → ✏️ 验证 → 🤖 自动填表 → ✅ 完成
💻 系统要求
必需
Python 3.8+ (下载)
Windows 10/11（推荐）或 Linux/Mac
4GB RAM（最低）
500MB 磁盘空间（用于模型）
Chrome 浏览器（用于自动化）
网络要求
可访问医院 Origin 系统
首次运行需要互联网（下载 OCR 模型）
🚀 快速开始
方法一：一键启动（推荐新手）
克隆项目
bash
git clone https://github.com/USAGI7878/dialysis-automation.git
cd dialysis-automation
双击运行 start.bat
✅ 自动创建虚拟环境
✅ 自动安装依赖
✅ 自动启动程序
方法二：手动安装
克隆项目
bash
git clone https://github.com/USAGI7878/dialysis-automation.git
cd dialysis-automation
创建虚拟环境
bash
python -m venv venv
激活虚拟环境
bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
安装依赖
bash
pip install -r requirements.txt
配置 Origin URL
编辑 config.json：

json
{
  "origin_url": "http://192.168.20.11:8080/EMR/main.jsp"
}
运行程序
bash
python main.py
📖 使用指南
工作流程
1️⃣ 拍照护理记录纸
   ↓
2️⃣ 上传照片 → OCR 识别
   ↓
3️⃣ 验证/修正数据
   ↓
4️⃣ 拍照透析机屏幕（多个时间点）
   ↓
5️⃣ 上传照片 → OCR 识别每小时观察
   ↓
6️⃣ 验证数据
   ↓
7️⃣ 输入 Origin 登录信息 + 病人 MRN
   ↓
8️⃣ 点击"自动填入数据"
   ↓
9️⃣ ✅ 完成！
详细步骤
步骤 1: 护理记录纸 OCR
点击 "📄 Upload Photo 上传照片"
选择护理记录纸照片
点击 "🔍 Start OCR 开始识别"
在右侧"Basic Data 基本数据"标签页验证数据
手动修正任何识别错误
步骤 2: 透析机屏幕 OCR
点击 "📱 Upload Photo 上传照片"
选择透析机屏幕照片
点击 "🔍 Extract Hourly Obs 提取每小时记录"
重复以上步骤添加不同时间点的数据
在"Hourly Obs 每小时记录"标签页验证数据
步骤 3: 自动填入 Origin
输入 Origin 用户名和密码
输入 病人 MRN（病历号）
点击 "🚀 Auto Fill Data 自动填入数据"
等待自动化完成（查看日志）
在 Origin 系统中验证数据
📸 拍照技巧
为了获得最佳 OCR 识别效果：

✅ 应该做：

光线充足、避免阴影
正面拍摄、避免倾斜
焦距清晰、文字可读
包含完整的表格区域
❌ 不要：

反光或过曝
模糊不清
角度过大
手指遮挡文字
📁 项目结构
dialysis-automation/
│
├── 📄 main.py                  # 主程序入口
├── 📄 config.json             # 配置文件
├── 📄 requirements.txt        # Python 依赖
├── 📄 start.bat               # 一键启动脚本（Windows）
├── 📄 README.md               # 本文件
├── 📄 LICENSE                 # MIT 许可证
│
├── 📂 modules/                # 核心模块
│   ├── __init__.py
│   ├── ocr_module.py          # OCR 识别模块
│   ├── origin_automation.py   # Origin 自动化模块
│   └── data_processor.py      # 数据处理模块（待开发）
│
├── 📂 data/                   # 数据文件夹
│   ├── exports/               # 导出的 JSON 文件
│   └── temp/                  # 临时文件
│
├── 📂 logs/                   # 日志文件夹
│   └── automation.log         # 操作日志
│
└── 📂 docs/                   # 文档
    └── screenshots/           # 截图
⚙️ 配置说明
config.json 配置文件
json
{
  "origin_url": "http://192.168.20.11:8080/EMR/main.jsp",
  "ocr_settings": {
    "use_gpu": false,
    "confidence_threshold": 0.5
  },
  "selenium_settings": {
    "headless": false,
    "implicit_wait": 10
  }
}
❓ 常见问题
Q1: OCR 识别不准确怎么办？
答：

确保照片清晰、光线充足
避免反光和阴影
识别后手动修正错误
可以在"Data Editor 数据编辑器"中直接编辑
Q2: Origin 自动化失败？
答：

检查网络连接
验证用户名密码正确
确认病人 MRN 存在
查看 logs/automation.log 了解详情
Q3: 可以在家使用吗？
答：

✅ 可以进行 OCR 识别和数据编辑
❌ 无法自动填入 Origin（需要医院网络）
💡 建议：在家识别数据，导出 JSON，回医院后导入并自动填表
🗺️ 开发路线图
✅ 已完成 (v1.0.0)
 护理记录纸 OCR
 透析机屏幕 OCR
 Origin 系统自动化
 双语用户界面
 数据导入/导出
🚧 进行中 (v1.1.0)
 提高 OCR 准确率
 批量处理多个病人
 数据统计和报表
📅 计划中 (v2.0.0)
 云端存储和同步
 手机 App 版本
 AI 辅助数据验证
🤝 贡献指南
欢迎贡献代码、报告 bug 或提出新功能建议！

如何贡献
Fork 本项目
创建特性分支 (git checkout -b feature/AmazingFeature)
提交更改 (git commit -m 'Add AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
创建 Pull Request
📜 许可证
本项目采用 MIT 许可证 - 详见 LICENSE 文件

👨‍💻 作者
你的名字 - 医疗信息化护理师
📧 邮箱: peggy8526123@gmail.com  
🔗 GitHub: @USAGI7878

🙏 致谢
感谢 EasyOCR 提供优秀的 OCR 引擎
感谢 Selenium 实现浏览器自动化
感谢所有测试和反馈的护理同事们
<div align="center">
⭐ 如果这个项目对你有帮助，请给一个 Star！

Made with ❤️ by 一位会写代码的护理师

</div>
