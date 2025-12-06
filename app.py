"""
Dialysis Data Automation System - Streamlit Web App
透析数据自动化系统 - 网页版

Run: streamlit run app.py
Access: http://localhost:8501
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import logging
from io import BytesIO
from PIL import Image

# 配置页面
st.set_page_config(
    page_title="Dialysis Automation System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化日志
logging.basicConfig(
    filename='logs/automation.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 确保目录存在
os.makedirs('logs', exist_ok=True)
os.makedirs('data/exports', exist_ok=True)
os.makedirs('data/temp', exist_ok=True)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        padding: 1rem;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .step-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-size: 1.3rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'nursing_data' not in st.session_state:
    st.session_state.nursing_data = {}
if 'hourly_observations' not in st.session_state:
    st.session_state.hourly_observations = []
if 'nursing_image' not in st.session_state:
    st.session_state.nursing_image = None
if 'machine_images' not in st.session_state:
    st.session_state.machine_images = []
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log_message(message):
    """添加日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.logs.append(log_entry)
    logging.info(message)

def load_config():
    """加载配置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"origin_url": "https://origin.klsch.com"}

# 主标题
st.markdown('<div class="main-header">🏥 Dialysis Data Automation System<br>透析数据自动化系统</div>', unsafe_allow_html=True)

# 版本信息
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<p style="text-align: center; color: gray; font-size: 0.9rem;">Version 1.0.0 | For KLSCH Haemodialysis Unit</p>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("📋 Navigation 导航")
    
    page = st.radio(
        "Select Page 选择页面:",
        ["🏠 Home", "📄 Step 1: Nursing Record", "📱 Step 2: Machine Screen", "🤖 Step 3: Auto Fill", "📊 View Data", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # 快速状态
    st.subheader("📈 Status 状态")
    
    nursing_status = "✅ Completed" if st.session_state.nursing_data else "⏳ Pending"
    st.write(f"**Nursing Record:** {nursing_status}")
    
    hourly_status = f"✅ {len(st.session_state.hourly_observations)} entries" if st.session_state.hourly_observations else "⏳ No data"
    st.write(f"**Hourly Obs:** {hourly_status}")
    
    st.markdown("---")
    
    # 快速操作
    st.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Reset All Data", use_container_width=True):
        st.session_state.nursing_data = {}
        st.session_state.hourly_observations = []
        st.session_state.nursing_image = None
        st.session_state.machine_images = []
        st.session_state.logs = []
        st.success("All data reset! 所有数据已重置！")
        st.rerun()
    
    if st.button("💾 Export JSON", use_container_width=True):
        data = {
            "timestamp": datetime.now().isoformat(),
            "basic_data": st.session_state.nursing_data,
            "hourly_observations": st.session_state.hourly_observations
        }
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        st.download_button(
            "📥 Download JSON",
            json_str,
            file_name=f"dialysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# 主内容区域
if page == "🏠 Home":
    st.markdown('<div class="step-header">Welcome to Dialysis Automation System 欢迎使用透析自动化系统</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.subheader("📖 How It Works 工作流程")
        st.markdown("""
        **Step 1:** Upload nursing record photo 📄  
        → OCR extracts patient data automatically  
        → Verify and correct if needed
        
        **Step 2:** Upload dialysis machine screen 📱  
        → OCR extracts hourly observations  
        → Add multiple time points
        
        **Step 3:** Automatic data entry 🤖  
        → Enter Origin credentials  
        → System fills data automatically
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.subheader("✨ Features 功能特点")
        st.markdown("""
        ✅ **OCR Recognition** - Automatic text extraction  
        ✅ **Smart Correction** - Manual editing available  
        ✅ **Origin Integration** - Direct system access  
        ✅ **Data Management** - Import/Export JSON  
        ✅ **Web-Based** - No installation needed  
        ✅ **Hospital Network** - Runs on local server
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.subheader("🚀 Quick Start 快速开始")
    st.markdown("""
    1. Click **"Step 1: Nursing Record"** in the sidebar  
    2. Upload a photo of the nursing record  
    3. Review extracted data  
    4. Continue to Step 2 and Step 3
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 统计信息
    st.markdown("---")
    st.subheader("📊 Current Session 当前会话")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Basic Data Fields", len([v for v in st.session_state.nursing_data.values() if v]))
    with col2:
        st.metric("Hourly Observations", len(st.session_state.hourly_observations))
    with col3:
        st.metric("Log Entries", len(st.session_state.logs))

elif page == "📄 Step 1: Nursing Record":
    st.markdown('<div class="step-header">Step 1: Nursing Record OCR 护理记录识别</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload Photo 上传照片")
        
        uploaded_file = st.file_uploader(
            "Choose nursing record photo 选择护理记录照片",
            type=['jpg', 'jpeg', 'png'],
            key="nursing_upload"
        )
        
        if uploaded_file:
            # 显示图片
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # 保存临时文件
            temp_path = f"data/temp/nursing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            image.save(temp_path)
            st.session_state.nursing_image = temp_path
            
            st.success("✅ Image uploaded successfully! 图片上传成功！")
            
            # OCR按钮
            if st.button("🔍 Start OCR Recognition 开始识别", use_container_width=True, type="primary"):
                with st.spinner("Processing OCR... 识别中..."):
                    try:
                        from modules.ocr_module import DialysisOCR
                        
                        ocr = DialysisOCR()
                        data = ocr.extract_nursing_record(temp_path)
                        
                        st.session_state.nursing_data = data
                        log_message("✓ Nursing record OCR completed")
                        
                        filled_count = sum(1 for v in data.values() if v)
                        st.success(f"✅ OCR completed! Found {filled_count} fields. 识别完成！找到 {filled_count} 个字段。")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ OCR Error: {str(e)}")
                        log_message(f"✗ OCR Error: {str(e)}")
    
    with col2:
        st.subheader("✏️ Edit Data 编辑数据")
        
        if st.session_state.nursing_data:
            st.info("📝 Review and correct the extracted data below 请检查并修正以下数据")
        else:
            st.warning("⚠️ No data yet. Upload and process an image first. 还没有数据，请先上传并识别图片。")
        
        # 数据编辑表单
        with st.form("nursing_data_form"):
            data = st.session_state.nursing_data
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                data['DATE'] = st.text_input("Date 日期", value=data.get('DATE', ''), placeholder="DD-MM-YYYY")
                data['NUMBER_OF_HD'] = st.text_input("Number of HD 透析次数", value=data.get('NUMBER_OF_HD', ''))
                data['HRS_OF_HD'] = st.text_input("Hours of HD 透析时长", value=data.get('HRS_OF_HD', ''))
                data['PRE_BP'] = st.text_input("Pre BP 治疗前血压", value=data.get('PRE_BP', ''), placeholder="120/80")
                data['POST_BP'] = st.text_input("Post BP 治疗后血压", value=data.get('POST_BP', ''), placeholder="120/80")
                data['PRE_PULSE'] = st.text_input("Pre Pulse 治疗前脉搏", value=data.get('PRE_PULSE', ''))
                data['TEMPERATURE'] = st.text_input("Temperature 体温", value=data.get('TEMPERATURE', ''), placeholder="36.5")
            
            with col_b:
                data['PRE_WEIGHT'] = st.text_input("Pre Weight 治疗前体重 (kg)", value=data.get('PRE_WEIGHT', ''))
                data['POST_WEIGHT'] = st.text_input("Post Weight 治疗后体重 (kg)", value=data.get('POST_WEIGHT', ''))
                data['IDWG'] = st.text_input("IDWG", value=data.get('IDWG', ''))
                data['UF'] = st.text_input("UF 超滤量 (L)", value=data.get('UF', ''))
                data['KT_V'] = st.text_input("Kt/V", value=data.get('KT_V', ''))
                data['WEIGHT_LOSS'] = st.text_input("Weight Loss 体重减少", value=data.get('WEIGHT_LOSS', ''))
                data['REMARKS'] = st.text_area("Remarks 备注", value=data.get('REMARKS', ''), height=100)
            
            if st.form_submit_button("💾 Save Data 保存数据", use_container_width=True):
                st.session_state.nursing_data = data
                st.success("✅ Data saved! 数据已保存！")
                log_message("✓ Nursing data updated manually")

elif page == "📱 Step 2: Machine Screen":
    st.markdown('<div class="step-header">Step 2: Machine Screen OCR 透析机屏幕识别</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Upload Machine Screen 上传透析机屏幕")
        
        uploaded_file = st.file_uploader(
            "Choose machine screen photo 选择透析机照片",
            type=['jpg', 'jpeg', 'png'],
            key="machine_upload"
        )
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Machine Screen", use_column_width=True)
            
            temp_path = f"data/temp/machine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            image.save(temp_path)
            
            st.success("✅ Image uploaded! 图片已上传！")
            
            if st.button("🔍 Extract Hourly Data 提取每小时数据", use_container_width=True, type="primary"):
                with st.spinner("Processing OCR... 识别中..."):
                    try:
                        from modules.ocr_module import DialysisOCR
                        
                        ocr = DialysisOCR()
                        data = ocr.extract_machine_screen(temp_path)
                        
                        if data and any(data.values()):
                            st.session_state.hourly_observations.append(data)
                            log_message(f"✓ Added hourly observation: {data.get('TIME', 'N/A')}")
                            st.success("✅ Data extracted and added! 数据已提取并添加！")
                            st.rerun()
                        else:
                            st.warning("⚠️ No data found. Try another photo or add manually. 未找到数据，请尝试其他照片或手动添加。")
                        
                    except Exception as e:
                        st.error(f"❌ OCR Error: {str(e)}")
                        log_message(f"✗ Machine OCR error: {str(e)}")
        
        st.markdown("---")
        st.subheader("➕ Manual Entry 手动输入")
        
        with st.form("manual_hourly_entry"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                time = st.text_input("Time 时间", placeholder="07:10")
                bp = st.text_input("BP 血压", placeholder="120/80")
                vp = st.text_input("VP 静脉压", placeholder="160")
                pulse = st.text_input("Pulse 脉搏", placeholder="P-84")
            
            with col_b:
                qb = st.text_input("QB 血流速", placeholder="300")
                qd = st.text_input("QD 透析液流速", placeholder="500")
                ufr = st.text_input("UFR 超滤率", placeholder="625")
            
            if st.form_submit_button("➕ Add Entry 添加记录", use_container_width=True):
                entry = {
                    "TIME": time,
                    "BP": bp,
                    "VP": vp,
                    "QB": qb,
                    "QD": qd,
                    "PULSE": pulse,
                    "UFR": ufr
                }
                st.session_state.hourly_observations.append(entry)
                st.success("✅ Entry added! 记录已添加！")
                log_message(f"✓ Manual hourly entry added: {time}")
                st.rerun()
    
    with col2:
        st.subheader("📊 Hourly Observations 每小时记录")
        
        if st.session_state.hourly_observations:
            st.info(f"📝 Total entries: {len(st.session_state.hourly_observations)}")
            
            for idx, obs in enumerate(st.session_state.hourly_observations):
                with st.expander(f"🕐 Entry {idx + 1}: {obs.get('TIME', 'N/A')}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Time 时间:** {obs.get('TIME', '-')}")
                        st.write(f"**BP 血压:** {obs.get('BP', '-')}")
                        st.write(f"**VP 静脉压:** {obs.get('VP', '-')}")
                        st.write(f"**Pulse 脉搏:** {obs.get('PULSE', '-')}")
                    with col_b:
                        st.write(f"**QB 血流速:** {obs.get('QB', '-')}")
                        st.write(f"**QD 透析液流速:** {obs.get('QD', '-')}")
                        st.write(f"**UFR 超滤率:** {obs.get('UFR', '-')}")
                    
                    if st.button(f"🗑️ Delete 删除", key=f"del_{idx}"):
                        st.session_state.hourly_observations.pop(idx)
                        st.success("✅ Entry deleted! 记录已删除！")
                        st.rerun()
        else:
            st.warning("⚠️ No hourly observations yet. Upload machine photos or add manually. 还没有每小时记录，请上传照片或手动添加。")

elif page == "🤖 Step 3: Auto Fill":
    st.markdown('<div class="step-header">Step 3: Automatic Data Entry to Origin 自动填入Origin系统</div>', unsafe_allow_html=True)
    
    # 检查前置条件
    has_nursing = bool(st.session_state.nursing_data and any(st.session_state.nursing_data.values()))
    has_hourly = bool(st.session_state.hourly_observations)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if has_nursing:
            st.success("✅ Nursing data ready")
        else:
            st.error("❌ No nursing data")
    with col2:
        if has_hourly:
            st.success(f"✅ {len(st.session_state.hourly_observations)} hourly entries")
        else:
            st.warning("⚠️ No hourly data")
    with col3:
        if has_nursing or has_hourly:
            st.info("✅ Ready to proceed")
        else:
            st.error("❌ Complete Steps 1-2 first")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔐 Origin System Credentials")
        
        with st.form("origin_credentials"):
            username = st.text_input("Username 用户名", placeholder="Enter your username")
            password = st.text_input("Password 密码", type="password", placeholder="Enter your password")
            mrn = st.text_input("Patient MRN 病历号", placeholder="Enter patient MRN")
            
            st.markdown("---")
            
            start_automation = st.form_submit_button("🚀 Start Automation 开始自动化", use_container_width=True, type="primary")
            
            if start_automation:
                if not all([username, password, mrn]):
                    st.error("❌ Please fill in all fields! 请填写所有字段！")
                elif not (has_nursing or has_hourly):
                    st.error("❌ No data to fill! Complete Steps 1-2 first. 没有数据可填！请先完成步骤1-2。")
                else:
                    st.info("⏳ Starting automation... This may take a few minutes... 正在启动自动化...可能需要几分钟...")
                    
                    try:
                        from modules.origin_automation import OriginAutomation
                        
                        config = load_config()
                        data = {
                            "basic_data": st.session_state.nursing_data,
                            "hourly_observations": st.session_state.hourly_observations
                        }
                        
                        # 创建进度条
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def progress_callback(message):
                            log_message(message)
                            status_text.text(message)
                        
                        automation = OriginAutomation(config.get("origin_url"))
                        
                        success = automation.run_automation(
                            username, password, mrn, data,
                            callback=progress_callback
                        )
                        
                        progress_bar.progress(100)
                        
                        if success:
                            st.success("✅ Automation completed successfully! 自动化完成！")
                            log_message("✓ Origin automation completed successfully")
                        else:
                            st.error("❌ Automation failed. Check logs for details. 自动化失败，请查看日志。")
                            log_message("✗ Origin automation failed")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        log_message(f"✗ Automation error: {str(e)}")
    
    with col2:
        st.subheader("📋 Data Preview 数据预览")
        
        with st.expander("📄 Nursing Record Data", expanded=True):
            if st.session_state.nursing_data:
                for key, value in st.session_state.nursing_data.items():
                    if value:
                        st.write(f"**{key}:** {value}")
            else:
                st.write("No data available")
        
        with st.expander("📊 Hourly Observations"):
            if st.session_state.hourly_observations:
                for idx, obs in enumerate(st.session_state.hourly_observations, 1):
                    st.write(f"**Entry {idx}:** {obs.get('TIME', 'N/A')}")
            else:
                st.write("No data available")

elif page == "📊 View Data":
    st.markdown('<div class="step-header">View All Data 查看所有数据</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📄 Nursing Data", "📊 Hourly Observations", "📜 Logs"])
    
    with tab1:
        st.subheader("Nursing Record Data 护理记录数据")
        if st.session_state.nursing_data:
            st.json(st.session_state.nursing_data)
        else:
            st.info("No nursing data available yet.")
    
    with tab2:
        st.subheader("Hourly Observations 每小时观察数据")
        if st.session_state.hourly_observations:
            st.json(st.session_state.hourly_observations)
        else:
            st.info("No hourly observations available yet.")
    
    with tab3:
        st.subheader("System Logs 系统日志")
        if st.session_state.logs:
            for log in reversed(st.session_state.logs[-50:]):  # Show last 50
                st.text(log)
        else:
            st.info("No logs available yet.")

elif page == "⚙️ Settings":
    st.markdown('<div class="step-header">Settings 设置</div>', unsafe_allow_html=True)
    
    config = load_config()
    
    with st.form("settings_form"):
        st.subheader("🌐 Origin System Configuration")
        origin_url = st.text_input("Origin URL", value=config.get("origin_url", ""))
        
        st.subheader("🔍 OCR Settings")
        use_gpu = st.checkbox("Use GPU for OCR (if available)", value=config.get("ocr_settings", {}).get("use_gpu", False))
        
        if st.form_submit_button("💾 Save Settings", use_container_width=True):
            new_config = {
                "origin_url": origin_url,
                "ocr_settings": {
                    "use_gpu": use_gpu
                }
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2)
            st.success("✅ Settings saved!")
            log_message("✓ Settings updated")

# 页脚
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🏥 KLSCH Haemodialysis Unit")
with col2:
    st.caption("📧 peggy8526123@gmail.com")
with col3:
    st.caption("v1.0.0 | 2025")
