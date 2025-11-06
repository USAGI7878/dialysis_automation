"""
Dialysis Automation System - Setup Script
透析自动化系统 - 初始化脚本

运行此脚本创建项目结构
Run this script to create project structure
"""

import os
import json

def setup_project():
    '''初始化项目结构 Initialize project structure'''
    
    print("=" * 60)
    print("Dialysis Automation System - Project Setup")
    print("透析自动化系统 - 项目初始化")
    print("=" * 60)
    print()
    
    # 创建目录结构
    directories = [
        'modules',
        'assets',
        'logs',
        'data/exports',
        'data/temp',
        'tests',
        '.vscode'
    ]
    
    print("Creating directories 创建目录...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f'  ✓ {directory}')
    
    print()
    
    # 创建 modules/__init__.py
    print("Creating module files 创建模块文件...")
    with open('modules/__init__.py', 'w', encoding='utf-8') as f:
        f.write('"""Dialysis Automation Modules"""\n')
    print('  ✓ modules/__init__.py')
    
    # 创建 config.json
    config = {
        "origin_url": "http://your-origin-url.com",
        "origin_login_url": "http://your-origin-url.com/login",
        "ocr_settings": {
            "language": "en",
            "use_angle_cls": True,
            "use_gpu": False,
            "det_db_thresh": 0.3,
            "det_db_box_thresh": 0.5
        },
        "selenium_settings": {
            "headless": False,
            "window_size": [1920, 1080],
            "implicit_wait": 10,
            "page_load_timeout": 30
        },
        "field_mappings": {
            "nursing_record": {
                "DATE": "date_input",
                "NUMBER_OF_HD": "number_hd",
                "HRS_OF_HD": "hrs_hd",
                "PRE_BP": "pre_bp",
                "POST_BP": "post_bp",
                "PRE_PULSE": "pre_pulse",
                "TEMPERATURE": "temperature",
                "PRE_WEIGHT": "pre_weight",
                "IDWG": "idwg",
                "POST_WEIGHT": "post_weight",
                "UF": "uf",
                "KT_V": "ktv",
                "WEIGHT_LOSS": "weight_loss",
                "REMARKS": "remarks"
            },
            "hourly_observation": {
                "TIME": "time",
                "BP": "bp",
                "VP": "vp",
                "QB": "qb",
                "QD": "qd",
                "PULSE": "pulse",
                "UFR": "ufr"
            }
        },
        "defaults": {
            "department": "HAEMODIALYSIS UNIT",
            "hrs_of_hd": "4"
        }
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print('  ✓ config.json')
    
    # 创建 requirements.txt
    requirements = """paddleocr>=2.7.0
opencv-python>=4.8.0
Pillow>=10.0.0
selenium>=4.15.0
webdriver-manager>=4.0.0
numpy>=1.24.0
python-dateutil>=2.8.0
"""
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements)
    print('  ✓ requirements.txt')
    
    # 创建 .gitignore
    gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Project specific
logs/
data/temp/
*.log
config_local.json

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore)
    print('  ✓ .gitignore')
    
    # 创建 README.md
    readme = """# Dialysis Data Automation System
# 透析数据自动化系统

## 功能 Features
- 📄 OCR识别护理记录纸 / OCR recognition of nursing records
- 📱 OCR识别透析机屏幕 / OCR recognition of dialysis machine screen
- 🤖 自动填入Origin系统 / Automatic data entry to Origin system
- 💾 数据导入导出 / Data import/export (JSON)
- 🔄 双语界面 / Bilingual interface (English/中文)

## 系统要求 System Requirements
- Python 3.8 或更高版本 / Python 3.8 or higher
- Windows 10/11 (推荐 / Recommended)
- 4GB RAM (最低 / Minimum)
- 可访问Origin系统的网络 / Network access to Origin system

## 快速开始 Quick Start

### 1. 创建虚拟环境 Create Virtual Environment
```bash
python -m venv venv
```

### 2. 激活虚拟环境 Activate Virtual Environment
**Windows:**
```bash
venv\\Scripts\\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. 安装依赖 Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. 配置设置 Configure Settings
编辑 `config.json` 文件:
- 设置Origin系统URL
- 调整OCR参数（如需要）
- 配置字段映射

### 5. 运行程序 Run Application
```bash
python main.py
```

## 使用流程 Workflow

### 步骤1: 护理记录纸 Step 1: Nursing Record
1. 点击"Upload Photo 上传照片"
2. 选择护理记录纸的照片
3. 点击"Start OCR 开始识别"
4. 在右侧数据编辑器中验证和修正数据

### 步骤2: 透析机屏幕 Step 2: Dialysis Machine
1. 点击"Upload Photo 上传照片"
2. 选择透析机屏幕照片
3. 点击"Extract Hourly Obs 提取每小时记录"
4. 可以多次添加不同时间点的数据
5. 在"Hourly Obs"标签页中验证数据

### 步骤3: 自动填入Origin Step 3: Auto Fill Origin
1. 输入Origin用户名和密码
2. 输入患者MRN（病历号）
3. 点击"Auto Fill Data 自动填入数据"
4. 等待自动化完成

## 数据管理 Data Management

### 导出数据 Export Data
- 点击"Export JSON 导出数据"
- 数据保存在 `data/exports/` 文件夹
- JSON格式，可以随时导入重用

### 导入数据 Import Data
- 点击"Load JSON 导入数据"
- 选择之前导出的JSON文件
- 数据自动填入表单

## 故障排查 Troubleshooting

### OCR识别不准确 OCR Inaccuracy
**问题**: 识别结果错误或缺失
**解决方案**:
- 确保照片清晰，光线充足
- 避免反光和阴影
- 照片尽量正面拍摄
- 手动修正识别结果

### Origin自动化失败 Automation Failure
**问题**: 无法登录或填入数据
**解决方案**:
- 检查网络连接
- 验证用户名密码正确
- 检查MRN是否存在
- 查看 `logs/automation.log` 了解详情

### 程序崩溃 Application Crash
**问题**: 程序意外退出
**解决方案**:
- 检查 `logs/` 文件夹中的日志
- 确保所有依赖包已安装
- 重新安装: `pip install -r requirements.txt --force-reinstall`

## 开发说明 Development Notes

### 项目结构 Project Structure
```
dialysis_automation/
├── main.py                    # 主程序
├── setup.py                   # 初始化脚本
├── requirements.txt           # 依赖包
├── config.json               # 配置文件
├── README.md                 # 说明文档
│
├── modules/                  # 功能模块
│   ├── ocr_module.py        # OCR识别
│   ├── origin_automation.py # Origin自动化
│   └── data_processor.py    # 数据处理
│
├── data/                    # 数据文件夹
│   ├── exports/             # 导出的JSON
│   └── temp/                # 临时文件
│
├── logs/                    # 日志文件夹
└── tests/                   # 测试文件
```

### 添加新功能 Adding New Features
1. 在 `modules/` 创建新模块
2. 在 `main.py` 中导入并集成
3. 更新 `config.json` 添加配置
4. 编写测试文件在 `tests/`

## 安全注意事项 Security Notes
⚠️ **重要 Important:**
- 不要将 `config.json` 提交到公共仓库（如果包含敏感信息）
- 建议使用环境变量存储密码
- 定期更改Origin系统密码
- 导出的JSON文件包含患者数据，请妥善保管

## 许可证 License
此项目仅供内部使用
For internal use only

## 联系方式 Contact
如有问题，请联系IT支持
For issues, please contact IT support

## 更新日志 Changelog

### Version 1.0.0 (2025-01-08)
- ✅ 初始版本发布
- ✅ OCR识别功能
- ✅ Origin自动化
- ✅ 双语界面
- ✅ 数据导入导出
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    print('  ✓ README.md')
    
    # 创建 VS Code settings
    vscode_settings = {
        "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": True,
        "python.formatting.provider": "black",
        "editor.formatOnSave": True,
        "files.exclude": {
            "**/__pycache__": True,
            "**/*.pyc": True,
            "**/venv": True
        },
        "files.associations": {
            "*.json": "jsonc"
        }
    }
    
    with open('.vscode/settings.json', 'w', encoding='utf-8') as f:
        json.dump(vscode_settings, f, indent=2)
    print('  ✓ .vscode/settings.json')
    
    # 创建 VS Code launch config
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Main Application",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/main.py",
                "console": "integratedTerminal",
                "justMyCode": True
            }
        ]
    }
    
    with open('.vscode/launch.json', 'w', encoding='utf-8') as f:
        json.dump(launch_config, f, indent=2)
    print('  ✓ .vscode/launch.json')
    
    print()
    print("=" * 60)
    print("✅ Project setup complete! 项目初始化完成！")
    print("=" * 60)
    print()
    print("Next steps 下一步:")
    print("1. Create virtual environment 创建虚拟环境:")
    print("   python -m venv venv")
    print()
    print("2. Activate virtual environment 激活虚拟环境:")
    print("   Windows: venv\\Scripts\\activate")
    print("   Linux/Mac: source venv/bin/activate")
    print()
    print("3. Install dependencies 安装依赖:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Create main.py file 创建main.py文件")
    print()
    print("5. Run application 运行程序:")
    print("   python main.py")
    print()

if __name__ == '__main__':
    setup_project()