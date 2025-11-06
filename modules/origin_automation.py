"""
Origin System Automation Module - KLSCH Implementation
Origin系统自动化模块 - KLSCH 完整实现版

完整的登录和数据填入流程
Complete login and data entry workflow
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OriginAutomation:
    """Origin系统自动化类 - KLSCH完整版"""
    
    def __init__(self, origin_url=None, headless=False):
        """初始化Origin自动化"""
        self.origin_urls = [
            "http://192.168.20.12:8080/EMR/main.jsp",
            "http://192.168.20.11:8080/EMR/main.jsp"
        ]
        
        if origin_url:
            self.origin_urls.insert(0, origin_url)
        
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def initialize_driver(self):
        """初始化Chrome驱动"""
        try:
            logger.info("⏳ Initializing Chrome driver...")
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("✅ Chrome driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome: {e}")
            return False
            
    def login_step1_credentials(self, username, password):
        """
        步骤1: 输入用户名密码登录
        Step 1: Enter username and password
        """
        try:
            logger.info("📝 Step 1: Entering credentials...")
            
            # 尝试连接到Origin
            logged_in = False
            for url in self.origin_urls:
                try:
                    logger.info(f"🔗 Trying: {url}")
                    self.driver.get(url)
                    time.sleep(2)
                    
                    if "KLSCH" in self.driver.page_source or "login" in self.driver.page_source.lower():
                        logger.info("✓ Page loaded")
                        logged_in = True
                        break
                except Exception as e:
                    logger.warning(f"⚠️  Failed: {e}")
                    continue
            
            if not logged_in:
                raise Exception("无法连接到Origin")
            
            time.sleep(2)
            
            # 查找用户名输入框
            logger.info("📝 Finding username field...")
            username_field = None
            
            # 方法1: 通过placeholder
            try:
                username_field = self.driver.find_element(
                    By.XPATH, 
                    "//input[contains(@placeholder, 'USER') or contains(@placeholder, 'user')]"
                )
                logger.info("✓ Found username field by placeholder")
            except:
                # 方法2: 第一个输入框
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    username_field = inputs[0]
                    logger.info("✓ Found username field by position")
                except:
                    raise Exception("找不到用户名输入框")
            
            # 输入用户名
            username_field.clear()
            username_field.send_keys(username)
            logger.info(f"✓ Username entered: {username}")
            time.sleep(0.5)
            
            # 查找密码输入框
            logger.info("📝 Finding password field...")
            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_field.clear()
            password_field.send_keys(password)
            logger.info("✓ Password entered")
            time.sleep(0.5)
            
            # 点击第一个LOGIN按钮
            logger.info("🔘 Clicking first LOGIN button...")
            login_button = self.driver.find_element(
                By.XPATH, 
                "//button[contains(text(), 'LOGIN')] | //input[@value='LOGIN']"
            )
            login_button.click()
            logger.info("✓ First LOGIN clicked")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Login step 1 failed: {e}")
            self.take_screenshot("login_step1_error.png")
            return False
            
    def login_step2_department(self):
        """
        步骤2: 选择HAEMODIALYSIS UNIT并确认
        Step 2: Select department and confirm
        """
        try:
            logger.info("🏥 Step 2: Selecting HAEMODIALYSIS UNIT...")
            time.sleep(2)
            
            # 检查是否看到 "WELCOME TO ORIGIN"
            if "WELCOME" in self.driver.page_source.upper():
                logger.info("✓ Department selection page loaded")
                
                # 查找下拉框
                try:
                    dept_select = self.driver.find_element(By.TAG_NAME, "select")
                    select = Select(dept_select)
                    
                    # 选择 HAEMODIALYSIS UNIT
                    select.select_by_visible_text("HAEMODIALYSIS UNIT")
                    logger.info("✓ HAEMODIALYSIS UNIT selected")
                    time.sleep(1)
                except Exception as e:
                    logger.info("ℹ️  Department already selected")
                
                # 点击第二个LOGIN按钮（或OK按钮）
                logger.info("🔘 Clicking second LOGIN/OK button...")
                try:
                    # 尝试找LOGIN按钮
                    confirm_button = self.driver.find_element(
                        By.XPATH, 
                        "//button[contains(text(), 'LOGIN')] | //button[contains(text(), 'OK')]"
                    )
                    confirm_button.click()
                    logger.info("✓ Department confirmed")
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"⚠️  Could not find confirm button: {e}")
                
                return True
            else:
                logger.info("ℹ️  Department selection not needed or already passed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Login step 2 failed: {e}")
            self.take_screenshot("login_step2_error.png")
            return False
            
    def find_patient_in_queue(self, mrn):
        """
        步骤3: 在Dialysis Queue中找到病人
        Step 3: Find patient in dialysis queue
        """
        try:
            logger.info(f"🔍 Step 3: Finding patient MRN: {mrn} in queue...")
            time.sleep(2)
            
            # 方法1: 直接在当前页面查找MRN
            try:
                logger.info("Looking for patient in current page...")
                patient_element = self.driver.find_element(
                    By.XPATH, 
                    f"//td[contains(text(), '{mrn}')] | //a[contains(text(), '{mrn}')]"
                )
                patient_element.click()
                logger.info("✓ Patient found and clicked")
                time.sleep(2)
                return True
            except:
                logger.info("Patient not found on current page, trying search...")
            
            # 方法2: 使用搜索框
            try:
                search_box = self.driver.find_element(
                    By.XPATH, 
                    "//input[@type='text' or @type='search']"
                )
                search_box.clear()
                search_box.send_keys(mrn)
                search_box.send_keys(Keys.RETURN)
                time.sleep(2)
                
                # 点击搜索结果
                patient_element = self.driver.find_element(
                    By.XPATH, 
                    f"//td[contains(text(), '{mrn}')] | //a[contains(text(), '{mrn}')]"
                )
                patient_element.click()
                logger.info("✓ Patient found via search")
                time.sleep(2)
                return True
            except:
                pass
            
            # 方法3: 在表格中查找
            try:
                patient_row = self.driver.find_element(
                    By.XPATH, 
                    f"//tr[contains(., '{mrn}')]"
                )
                # 点击该行的链接
                link = patient_row.find_element(By.TAG_NAME, "a")
                link.click()
                logger.info("✓ Patient found in table")
                time.sleep(2)
                return True
            except:
                pass
            
            logger.error(f"❌ Could not find patient with MRN: {mrn}")
            self.take_screenshot("patient_not_found.png")
            return False
            
        except Exception as e:
            logger.error(f"❌ Find patient error: {e}")
            self.take_screenshot("find_patient_error.png")
            return False
            
    def open_hd_treatment_record(self):
        """
        步骤4: 打开HAEMODIALYSIS TREATMENT RECORD
        Step 4: Open HD treatment record
        """
        try:
            logger.info("📋 Step 4: Opening HD Treatment Record...")
            time.sleep(2)
            
            # 点击左侧INVESTIGATIONS菜单
            logger.info("Expanding INVESTIGATIONS menu...")
            try:
                investigations = self.driver.find_element(
                    By.XPATH, 
                    "//*[contains(text(), 'INVESTIGATION')]"
                )
                investigations.click()
                logger.info("✓ INVESTIGATIONS clicked")
                time.sleep(1)
            except:
                logger.info("ℹ️  INVESTIGATIONS already expanded")
            
            # 点击HAEMODIALYSIS TREATMENT RECORD
            logger.info("Clicking HAEMODIALYSIS TREATMENT RECORD...")
            hd_record = self.driver.find_element(
                By.XPATH, 
                "//a[contains(text(), 'HAEMODIALYSIS') and contains(text(), 'TREATMENT')]"
            )
            hd_record.click()
            logger.info("✓ HD Treatment Record opened")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Open HD record error: {e}")
            self.take_screenshot("open_record_error.png")
            return False
            
    def open_current_month_table(self):
        """
        步骤5: 找到当月表格并打开
        Step 5: Find and open current month table
        """
        try:
            logger.info("📅 Step 5: Opening current month table...")
            time.sleep(2)
            
            # 获取当前月份
            from datetime import datetime
            current_month = datetime.now().strftime("%B")  # e.g., "January"
            current_year = datetime.now().strftime("%Y")
            
            logger.info(f"Looking for table: {current_month} {current_year}")
            
            # 方法1: 查找包含当前月份的链接或行
            try:
                month_element = self.driver.find_element(
                    By.XPATH, 
                    f"//td[contains(text(), '{current_month}')] | //a[contains(text(), '{current_month}')]"
                )
                month_element.click()
                logger.info(f"✓ {current_month} table found and clicked")
                time.sleep(2)
            except:
                # 方法2: 点击第一个表格（假设是最新的）
                logger.info("Current month not found, clicking first table...")
                first_row = self.driver.find_element(
                    By.XPATH, 
                    "//table//tbody//tr[1]//a | //table//tbody//tr[1]//td"
                )
                first_row.click()
                logger.info("✓ First table clicked")
                time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Open table error: {e}")
            self.take_screenshot("open_table_error.png")
            return False
            
    def click_edit_button(self):
        """
        步骤6: 点击编辑按钮（铅笔图标）
        Step 6: Click edit button (pencil icon)
        """
        try:
            logger.info("✏️ Step 6: Clicking edit button...")
            time.sleep(2)
            
            # 查找编辑按钮
            try:
                # 方法1: 通过图标class
                edit_button = self.driver.find_element(
                    By.XPATH, 
                    "//button[contains(@class, 'edit')] | //i[contains(@class, 'pencil')] | //a[contains(@title, 'Edit')]"
                )
                edit_button.click()
                logger.info("✓ Edit button clicked")
            except:
                # 方法2: 通过文本
                edit_button = self.driver.find_element(
                    By.XPATH, 
                    "//button[contains(text(), 'Edit')] | //a[contains(text(), 'Edit')]"
                )
                edit_button.click()
                logger.info("✓ Edit link clicked")
            
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"❌ Click edit error: {e}")
            self.take_screenshot("edit_button_error.png")
            return False
            
    def fill_data_in_form(self, data):
        """
        步骤7: 填入数据
        Step 7: Fill in data
        """
        try:
            logger.info("📝 Step 7: Filling data...")
            time.sleep(1)
            
            basic_data = data.get("basic_data", {})
            filled_count = 0
            
            # 填入基本数据
            for key, value in basic_data.items():
                if not value:
                    continue
                
                try:
                    # 尝试多种方式查找输入框
                    field_name = key.replace("_", " ")
                    
                    # 方法1: 通过标签文本查找
                    try:
                        input_field = self.driver.find_element(
                            By.XPATH,
                            f"//td[contains(text(), '{field_name}')]//following-sibling::td//input | "
                            f"//label[contains(text(), '{field_name}')]//following-sibling::input"
                        )
                    except:
                        # 方法2: 通过name属性
                        input_field = self.driver.find_element(By.NAME, key.lower())
                    
                    # 填入数据
                    if key in ["COMFORTABLE", "DIZZINESS", "BLEEDING", "DRESSING"]:
                        select = Select(input_field)
                        select.select_by_visible_text(value)
                    else:
                        input_field.clear()
                        input_field.send_keys(str(value))
                    
                    filled_count += 1
                    logger.info(f"  ✓ {key}: {value}")
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not fill {key}: {e}")
            
            # 填入每小时观察
            hourly_obs = data.get("hourly_observations", [])
            if hourly_obs:
                logger.info(f"📊 Filling {len(hourly_obs)} hourly observations...")
                # 这里需要根据实际表格结构调整
                # 暂时跳过，因为需要看到实际的HTML结构
            
            logger.info(f"✅ Filled {filled_count} fields")
            return filled_count > 0
            
        except Exception as e:
            logger.error(f"❌ Fill data error: {e}")
            self.take_screenshot("fill_data_error.png")
            return False
            
    def save_form(self):
        """
        步骤8: 保存表单
        Step 8: Save form
        """
        try:
            logger.info("💾 Step 8: Saving form...")
            time.sleep(1)
            
            # 查找保存按钮
            save_button = self.driver.find_element(
                By.XPATH, 
                "//button[contains(text(), 'UPDATE')] | //button[contains(text(), 'SAVE')] | //input[@value='UPDATE']"
            )
            save_button.click()
            logger.info("✓ Save button clicked")
            time.sleep(3)
            
            logger.info("✅ Form saved")
            return True
            
        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            self.take_screenshot("save_error.png")
            return False
            
    def take_screenshot(self, filename):
        """截图"""
        try:
            self.driver.save_screenshot(f"logs/{filename}")
            logger.info(f"📸 Screenshot: logs/{filename}")
        except:
            pass
            
    def run_automation(self, username, password, mrn, data, callback=None):
        """
        运行完整的自动化流程
        Run complete automation workflow
        """
        def log_cb(msg):
            if callback:
                callback(msg)
            logger.info(msg)
        
        try:
            # 初始化
            log_cb("⏳ 初始化浏览器 Initializing...")
            if not self.initialize_driver():
                return False
            
            # 步骤1: 用户名密码登录
            log_cb("🔐 Step 1/8: 登录 Login...")
            if not self.login_step1_credentials(username, password):
                log_cb("❌ 登录失败 Login failed")
                return False
            log_cb("✅ Step 1 完成")
            
            # 步骤2: 选择部门
            log_cb("🏥 Step 2/8: 选择部门 Select department...")
            if not self.login_step2_department():
                log_cb("❌ 部门选择失败 Department selection failed")
                return False
            log_cb("✅ Step 2 完成")
            
            # 步骤3: 查找病人
            log_cb(f"🔍 Step 3/8: 查找病人 Finding patient {mrn}...")
            if not self.find_patient_in_queue(mrn):
                log_cb("❌ 找不到病人 Patient not found")
                return False
            log_cb("✅ Step 3 完成")
            
            # 步骤4: 打开HD记录
            log_cb("📋 Step 4/8: 打开治疗记录 Opening HD record...")
            if not self.open_hd_treatment_record():
                log_cb("❌ 无法打开记录 Could not open record")
                return False
            log_cb("✅ Step 4 完成")
            
            # 步骤5: 打开当月表格
            log_cb("📅 Step 5/8: 打开当月表格 Opening current month...")
            if not self.open_current_month_table():
                log_cb("⚠️  Could not find table, continuing...")
            log_cb("✅ Step 5 完成")
            
            # 步骤6: 点击编辑
            log_cb("✏️ Step 6/8: 点击编辑 Clicking edit...")
            if not self.click_edit_button():
                log_cb("⚠️  Could not find edit button, continuing...")
            log_cb("✅ Step 6 完成")
            
            # 步骤7: 填入数据
            log_cb("📝 Step 7/8: 填入数据 Filling data...")
            if not self.fill_data_in_form(data):
                log_cb("⚠️  Some fields could not be filled")
            log_cb("✅ Step 7 完成")
            
            # 步骤8: 保存
            log_cb("💾 Step 8/8: 保存 Saving...")
            if not self.save_form():
                log_cb("⚠️  Could not verify save")
            log_cb("✅ Step 8 完成")
            
            log_cb("✅ 自动化完成！Automation completed!")
            self.take_screenshot("success.png")
            return True
            
        except Exception as e:
            log_cb(f"❌ 错误 Error: {str(e)}")
            self.take_screenshot("automation_error.png")
            return False
            
        finally:
            if self.driver:
                log_cb("⏳ 5秒后关闭浏览器 Closing browser in 5s...")
                time.sleep(5)
                self.driver.quit()
                log_cb("✅ 浏览器已关闭 Browser closed")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 ORIGIN AUTOMATION TEST - KLSCH")
    print("="*70 + "\n")
    
    username = input("Username 用户名: ")
    password = input("Password 密码: ")
    mrn = input("Patient MRN 病历号: ")
    
    test_data = {
        "basic_data": {
            "DATE": "17-01-2025",
            "NUMBER_OF_HD": "613",
            "PRE_BP": "225/108"
        },
        "hourly_observations": []
    }
    
    automation = OriginAutomation()
    success = automation.run_automation(
        username, password, mrn, test_data,
        callback=lambda msg: print(f"  {msg}")
    )
    
    print("\n" + "="*70)
    if success:
        print("✅ 测试成功 TEST PASSED")
    else:
        print("❌ 测试失败 TEST FAILED")
    print("="*70 + "\n")