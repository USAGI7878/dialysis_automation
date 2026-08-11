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
        self._hd_record_node = None  # Step4定位到的HD记录树节点,供Step5复用
        
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
            
    def _accept_alert_if_present(self, timeout=3):
        """
        检测并自动确认(接受)页面弹出的原生JS弹窗(alert/confirm)
        Detect and auto-accept a native JS alert/confirm dialog if present.
        用于处理类似 "Switch to HAEMODIALYSIS UNIT?" 这种confirm()弹窗，
        否则Selenium的后续操作会因为UnexpectedAlertPresentException而卡死。

        返回值: 有弹窗的话，返回弹窗里的文字内容(方便调用方自己判断这到底是
        "保存成功"的提示、还是"某个字段没填/格式不对"之类的报错提示——
        不能看到"有弹窗就当成功")；没有弹窗则返回None。
        字符串在Python里是"真"、None是"假"，所以原本写
        `if self._accept_alert_if_present(...):` 的地方不用跟着改。
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            logger.info(f"⚠️  Alert detected: {alert_text}")
            alert.accept()
            logger.info("✓ Alert accepted")
            return alert_text
        except TimeoutException:
            return None
        except Exception as e:
            logger.warning(f"⚠️  Error handling alert: {e}")
            return None

    def login_step1_credentials(self, username, password):
        """
        步骤1: 输入用户名密码登录
        Step 1: Enter username and password
        """
        try:
            logger.info("📝 Step 1: Entering credentials...")

            # 防御性处理: 如果是批量模式下的"重新登录"，有可能上一步还留着
            # 没确认的弹窗(比如保存成功提示)，先确认掉，避免driver.get()
            # 因为UnexpectedAlertPresentException而实际上没有真正跳转到登录页，
            # 结果后面在错误的页面(比如部门选择页)上找密码框，导致误判登录失败
            self._accept_alert_if_present(timeout=2)

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

            # 防御性检查: 有可能此时session其实仍然有效，driver.get(url)
            # 已经被自动重定向到了部门选择页或病人队列页(没有真正的登录表单)。
            # 这种情况下不用再填账号密码，直接当作"已登录"处理，
            # 避免下面用 find_element 强行找一个根本不存在的密码框而直接崩溃。
            if not self.driver.find_elements(By.XPATH, "//input[@type='password']"):
                logger.info("ℹ️  页面上没有登录表单(密码框)，Session似乎仍然有效，跳过账号密码输入")
                return True
            
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
                    # 注意：选择该选项会触发页面的 onchange 事件，
                    # 弹出原生JS确认框 "Switch to HAEMODIALYSIS UNIT?"
                    select.select_by_visible_text("HAEMODIALYSIS UNIT")
                    logger.info("✓ HAEMODIALYSIS UNIT selected")

                    # 处理选择部门后立刻弹出的JS confirm弹窗
                    self._accept_alert_if_present(timeout=3)
                    time.sleep(1)
                except Exception as e:
                    logger.info("ℹ️  Department already selected")

                # 以防万一，点击LOGIN/OK按钮前再检查一次是否有残留弹窗
                self._accept_alert_if_present(timeout=1)
                
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
                    time.sleep(1)

                    # 点击后也可能再次弹出确认框，同样需要处理
                    self._accept_alert_if_present(timeout=3)
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"⚠️  Could not find confirm button: {e}")
                
                return True
            else:
                logger.info("ℹ️  Department selection not needed or already passed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Login step 2 failed: {e}")
            # 如果异常本身就是因为有未处理的弹窗(UnexpectedAlertPresentException)，
            # 先把它接受掉，避免浏览器一直卡在弹窗上
            self._accept_alert_if_present(timeout=1)
            self.take_screenshot("login_step2_error.png")
            return False
            
    def _find_element_in_any_frame(self, by, value, max_depth=3):
        """
        在主文档以及所有(可能嵌套的)iframe/frame中查找元素。
        找到后【不会】切回default_content，driver会停留在找到该元素的frame上下文中，
        方便后续对同一元素继续操作(比如紧接着的.click())。
        找不到时会自动切回default_content，返回None。
        """
        self.driver.switch_to.default_content()

        def search(depth):
            try:
                return self.driver.find_element(by, value)
            except NoSuchElementException:
                pass

            if depth <= 0:
                return None

            frame_count = len(
                self.driver.find_elements(By.TAG_NAME, "iframe")
                + self.driver.find_elements(By.TAG_NAME, "frame")
            )
            for idx in range(frame_count):
                try:
                    frames = (
                        self.driver.find_elements(By.TAG_NAME, "iframe")
                        + self.driver.find_elements(By.TAG_NAME, "frame")
                    )
                    self.driver.switch_to.frame(frames[idx])
                    found = search(depth - 1)
                    if found is not None:
                        return found
                    self.driver.switch_to.parent_frame()
                except Exception:
                    try:
                        self.driver.switch_to.parent_frame()
                    except Exception:
                        pass
                    continue
            return None

        result = search(max_depth)
        if result is None:
            self.driver.switch_to.default_content()
        return result

    def dump_page_source(self, filename="page_debug.html"):
        """
        调试用：把当前主页面 + 所有iframe内的HTML都导出到logs/文件夹，
        方便定位真实的DOM结构(比截图更准确，能看到确切的class/id/标签)。
        """
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            self.driver.switch_to.default_content()

            parts = ["<!-- ===== MAIN DOCUMENT ===== -->\n", self.driver.page_source]

            def collect_frames(depth, path):
                if depth <= 0:
                    return
                frames = (
                    self.driver.find_elements(By.TAG_NAME, "iframe")
                    + self.driver.find_elements(By.TAG_NAME, "frame")
                )
                for idx in range(len(frames)):
                    try:
                        frames = (
                            self.driver.find_elements(By.TAG_NAME, "iframe")
                            + self.driver.find_elements(By.TAG_NAME, "frame")
                        )
                        self.driver.switch_to.frame(frames[idx])
                        frame_path = f"{path}/frame[{idx}]"
                        parts.append(f"\n\n<!-- ===== {frame_path} ===== -->\n")
                        parts.append(self.driver.page_source)
                        collect_frames(depth - 1, frame_path)
                        self.driver.switch_to.parent_frame()
                    except Exception as e:
                        parts.append(f"\n<!-- Failed to read {path}/frame[{idx}]: {e} -->\n")
                        try:
                            self.driver.switch_to.parent_frame()
                        except Exception:
                            self.driver.switch_to.default_content()

            collect_frames(3, "root")
            self.driver.switch_to.default_content()

            filepath = f"logs/{filename}"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(parts))
            logger.info(f"📄 Page source dumped: {filepath}")
            return filepath
        except Exception as e:
            logger.warning(f"⚠️  Could not dump page source: {e}")
            return None

    def _find_elements_in_any_frame(self, by, value, max_depth=3):
        """
        与 _find_element_in_any_frame 类似，但返回匹配到的【元素列表】。
        在主文档以及所有(可能嵌套的)iframe/frame中查找，
        找到第一个"有匹配结果"的frame就停止并停留在该frame上下文中。
        """
        self.driver.switch_to.default_content()

        def search(depth):
            try:
                found = self.driver.find_elements(by, value)
                if found:
                    return found
            except Exception:
                pass

            if depth <= 0:
                return None

            frame_count = len(
                self.driver.find_elements(By.TAG_NAME, "iframe")
                + self.driver.find_elements(By.TAG_NAME, "frame")
            )
            for idx in range(frame_count):
                try:
                    frames = (
                        self.driver.find_elements(By.TAG_NAME, "iframe")
                        + self.driver.find_elements(By.TAG_NAME, "frame")
                    )
                    self.driver.switch_to.frame(frames[idx])
                    result = search(depth - 1)
                    if result:
                        return result
                    self.driver.switch_to.parent_frame()
                except Exception:
                    try:
                        self.driver.switch_to.parent_frame()
                    except Exception:
                        pass
                    continue
            return None

        result = search(max_depth)
        if not result:
            self.driver.switch_to.default_content()
        return result

    def _find_element_prefer_current_frame(self, by, value):
        """
        优先在【当前driver所在的frame】里查找元素(不重置到default_content)，
        只有当前frame找不到时，才退回去做全页面(含所有iframe)的重新扫描。
        用于Step4之后的操作——因为这些操作应该继续停留在Step4已经
        导航进入的那个frame里，而不是每次都从头扫描整个页面，
        以免"跳"到页面上其他区域(比如另一个不相关的模块/表格)去了。
        """
        try:
            el = self.driver.find_element(by, value)
            return el
        except NoSuchElementException:
            pass
        except Exception:
            pass
        return self._find_element_in_any_frame(by, value)

    def _find_elements_prefer_current_frame(self, by, value):
        """
        _find_element_prefer_current_frame 的复数版本。
        """
        try:
            found = self.driver.find_elements(by, value)
            if found:
                return found
        except Exception:
            pass
        return self._find_elements_in_any_frame(by, value)

    def _click_patient_row_by_mrn(self, mrn):
        """
        在当前页面(含所有iframe)的表格里，精确匹配MRN单元格所在的那一行，
        并依次尝试点击: MRN单元格本身 -> 该行内的链接(如病人姓名) -> 整行,
        直到有一次点击成功为止。
        用 normalize-space()做精确匹配，避免 contains() 误匹配到
        VISIT NUMBER 等包含相似数字的其他字段。
        """
        xpath_exact_td = f"//td[normalize-space(text())='{mrn}']"
        mrn_cell = self._find_element_in_any_frame(By.XPATH, xpath_exact_td)
        if mrn_cell is None:
            return False

        # 此时driver已经停留在找到mrn_cell的那个frame上下文中

        # 定位该单元格所在的整行
        try:
            row = mrn_cell.find_element(By.XPATH, "./ancestor::tr[1]")
        except NoSuchElementException:
            row = None

        click_targets = [mrn_cell]
        if row is not None:
            try:
                click_targets.append(row.find_element(By.TAG_NAME, "a"))
            except NoSuchElementException:
                pass
            click_targets.append(row)

        for target in click_targets:
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", target
                )
                time.sleep(0.3)
                target.click()
                time.sleep(1.5)
                logger.info(f"✓ Clicked target: {target.tag_name}")
                return True
            except Exception as e:
                logger.info(f"  ⚠️  Click attempt failed on <{target.tag_name}>: {e}")
                continue

        return False

    def _widen_date_range_and_reload(self, days_back=90):
        """
        队列页面默认只显示"当天"的透析病人(From/To 日期框限定了范围)。
        如果要找的病人不是今天做透析，默认范围内就会搜不到，
        这不是bug，是系统的正常筛选行为——所以这里让程序自己把日期范围放宽
        (From: N天前 ~ To: 今天)，再点击 Reload 按钮刷新列表，
        这样不管病人是哪天的都能被列出来。
        """
        try:
            from datetime import datetime, timedelta
            today_str = datetime.now().strftime("%Y-%m-%d")
            past_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            # 查找日期输入框：一般用 placeholder="yyyy-MM-dd" 标识，页面上通常有两个(From/To)
            date_inputs = self._find_elements_in_any_frame(
                By.XPATH,
                "//input[contains(translate(@placeholder, 'YMD', 'ymd'), 'yyyy-mm-dd')]"
            )

            if not date_inputs or len(date_inputs) < 2:
                logger.info("ℹ️  未找到From/To日期范围输入框，跳过放宽日期范围这一步")
                return False

            from_input, to_input = date_inputs[0], date_inputs[1]

            for inp, value in [(from_input, past_str), (to_input, today_str)]:
                try:
                    # 用JS直接设值并派发input/change事件，兼容大部分前端框架的绑定方式
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1];"
                        "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                        inp, value
                    )
                except Exception:
                    try:
                        inp.click()
                        inp.send_keys(Keys.CONTROL, 'a')
                        inp.send_keys(Keys.DELETE)
                        inp.send_keys(value)
                    except Exception as e:
                        logger.info(f"  ⚠️  设置日期失败: {e}")

            logger.info(f"✓ 日期范围已放宽: {past_str} ~ {today_str}")

            # 点击 Reload 按钮刷新列表
            reload_btn = self._find_element_in_any_frame(
                By.XPATH,
                "//button[contains(text(),'Reload')] | //*[contains(text(),'Reload') and (self::a or self::span or self::div)]"
            )
            if reload_btn is not None:
                try:
                    reload_btn.click()
                    time.sleep(2)
                    logger.info("✓ 已点击 Reload")
                except Exception as e:
                    logger.info(f"  ⚠️  点击 Reload 失败: {e}")
            else:
                logger.info("ℹ️  未找到 Reload 按钮")

            return True
        except Exception as e:
            logger.warning(f"⚠️  放宽日期范围失败: {e}")
            return False

    def find_patient_in_queue(self, mrn):
        """
        步骤3: 在Dialysis Queue中找到病人
        Step 3: Find patient in dialysis queue
        """
        try:
            mrn = str(mrn).strip()
            logger.info(f"🔍 Step 3: Finding patient MRN: {mrn} in queue...")
            time.sleep(2)
            
            # 方法1: 直接在当前(默认日期范围/当天)页面精确查找MRN所在行并点击
            logger.info("Looking for patient in current page (exact MRN match)...")
            if self._click_patient_row_by_mrn(mrn):
                logger.info("✓ Patient found and clicked")
                return True
            logger.info("Patient not found in default (today) range, widening date range...")

            # 方法2: 默认(今天)范围内没找到 -> 自动放宽日期范围(近90天)并重新查找
            # 这样即使病人不是今天做透析，也能被列出来，不用手动改日期
            if self._widen_date_range_and_reload(days_back=90):
                if self._click_patient_row_by_mrn(mrn):
                    logger.info("✓ Patient found after widening date range")
                    return True
            logger.info("Still not found after widening date range, trying search box...")

            # 方法3: 使用搜索框过滤后再定位该行
            try:
                search_box = self.driver.find_element(
                    By.XPATH, 
                    "//input[@type='text' or @type='search']"
                )
                search_box.clear()
                search_box.send_keys(mrn)
                search_box.send_keys(Keys.RETURN)
                time.sleep(2)
                
                if self._click_patient_row_by_mrn(mrn):
                    logger.info("✓ Patient found via search")
                    return True
            except Exception as e:
                logger.info(f"  ⚠️  Search box attempt failed: {e}")
            
            logger.error(f"❌ Could not find patient with MRN: {mrn}")
            self.take_screenshot("patient_not_found.png")
            debug_file = self.dump_page_source("patient_not_found_page.html")
            if debug_file:
                logger.info(f"📄 Debug HTML saved to {debug_file} — 如果还是找不到，把这个文件发给开发者分析")
            return False
            
        except Exception as e:
            logger.error(f"❌ Find patient error: {e}")
            self.take_screenshot("find_patient_error.png")
            return False
            
    def open_hd_treatment_record(self):
        """
        步骤4: 打开HAEMODIALYSIS TREATMENT RECORD
        Step 4: Open HD treatment record

        真实页面结构(从调试HTML里确认过): 这是一个树状目录(div嵌套 + class="treeLeaf"的<a>),
        不是表格。层级大致是:
          MEDICAL FOLDER > 病历号 > NURSING NOTES > HAEMODIALYSIS UNIT TREATMENT RECORD > [日期条目...]
        注意: INVESTIGATIONS分类下也有一个同名(甚至完全同名，包括尾部空格)的节点，
        所以必须先定位到 NURSING NOTES 这个节点，再在它的子树里找，
        否则会跟INVESTIGATIONS下同名的节点搞混。
        """
        try:
            logger.info("📋 Step 4: Opening HD Treatment Record...")
            time.sleep(2)

            # 优先用真实树状结构精确定位
            nursing_notes_node = self._find_element_prefer_current_frame(
                By.XPATH,
                "//div[@data-type='4' and normalize-space(@data-unitname)='NURSING NOTES']"
            )

            hd_record_node = None
            if nursing_notes_node is not None:
                logger.info("✓ Found NURSING NOTES tree node")
                # 如果还没展开，先点它的链接展开
                try:
                    if nursing_notes_node.get_attribute("expand") != "true":
                        anchor = nursing_notes_node.find_element(
                            By.XPATH, "./div[contains(@class,'tree-anchor-wrap')]/a"
                        )
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});", anchor
                        )
                        anchor.click()
                        logger.info("✓ NURSING NOTES expanded")
                        time.sleep(1.5)
                except Exception as e:
                    logger.info(f"  ⚠️  Could not expand NURSING NOTES: {e}")

                # 在NURSING NOTES的子树里精确找 HAEMODIALYSIS UNIT TREATMENT RECORD
                try:
                    hd_record_node = nursing_notes_node.find_element(
                        By.XPATH,
                        ".//div[@data-type='4' and "
                        "normalize-space(@data-unitname)='HAEMODIALYSIS UNIT TREATMENT RECORD']"
                    )
                    logger.info("✓ Found HAEMODIALYSIS UNIT TREATMENT RECORD node under NURSING NOTES")
                except NoSuchElementException:
                    hd_record_node = None
            else:
                logger.info("ℹ️  NURSING NOTES tree node not found via exact match")

            # 精确定位失败，退回旧的宽泛搜索方式(兜底，不至于直接失败)
            if hd_record_node is None:
                logger.info("ℹ️  改用宽泛搜索方式查找 HAEMODIALYSIS TREATMENT RECORD")
                hd_record_node = self._find_element_prefer_current_frame(
                    By.XPATH,
                    "//*[contains(text(), 'HAEMODIALYSIS') and contains(text(), 'TREATMENT')"
                    " and (self::a or self::td or self::span or self::div or self::li)]"
                )

            if hd_record_node is None:
                logger.error("❌ Could not find 'HAEMODIALYSIS UNIT TREATMENT RECORD' node anywhere")
                self.take_screenshot("open_record_error.png")
                self.dump_page_source("open_record_not_found.html")
                return False

            # 优先点它的链接(a.treeLeaf)，找不到就点整个节点
            try:
                click_target = hd_record_node.find_element(
                    By.XPATH, "./div[contains(@class,'tree-anchor-wrap')]/a"
                )
            except (NoSuchElementException, AttributeError):
                click_target = hd_record_node

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", click_target
            )
            click_target.click()
            logger.info("✓ HD Treatment Record node clicked/expanded")
            time.sleep(2)

            # 记住这个节点的定位方式，方便Step5(找最近日期)直接在它的子树里找，
            # 不用重新从头搜索整个页面
            self._hd_record_node = hd_record_node

            return True
            
        except Exception as e:
            logger.error(f"❌ Open HD record error: {e}")
            self.take_screenshot("open_record_error.png")
            return False

    def click_most_recent_date_record(self):
        """
        步骤5: 在HD Treatment Record的列表里，自动找出"日期最新"的那一条记录并点击。
        Step 5: Automatically find and click the record with the most recent date.

        真实页面结构(从调试HTML确认过): 这是树状目录，不是表格。
        Step4展开的"HAEMODIALYSIS UNIT TREATMENT RECORD"节点下面，
        直接子节点(<span>下的<div data-type="19">)就是各个日期条目，
        其中第一个是"Open Full View"(不是日期，要排除)，
        最后可能有一个"... N more file(s)"(也要排除)，
        中间的才是真正的日期条目，比如 data-unitname="01 Jul 2026_12:15"。
        这些条目在页面上本来就是按最新排在最前面的。

        做法:
        1. 优先用Step4保存的节点引用(self._hd_record_node)，直接在它子树里找日期条目
           (排除"Open Full View"和"more file"这两种非日期条目)
        2. 用严格的日期正则+dateutil解析出真正日期值，选出最新的那个点击
           (如果解析都失败，就直接点子树里第一个日期条目，因为本来就是排好序的)
        3. 如果树状结构定位失败(比如self._hd_record_node不存在)，
           才退回旧的"扫描表格"方式(兜底，避免完全无法工作)
        """
        try:
            from dateutil import parser as date_parser
            import re

            logger.info("📅 Step 5: Finding most recent date record...")
            time.sleep(2)

            date_pattern = re.compile(
                r'^\s*('
                r'\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}'
                r'|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}'
                r'|\d{1,2}[-\s][A-Za-z]{3,9}[-\s]\d{2,4}'
                r'|[A-Za-z]{3,9}\s\d{4}'
                r')'
                r'([_\s]\d{1,2}:\d{2}(:\d{2})?)?'
                r'\s*$'
            )

            def parse_date_text(text):
                if not text or not date_pattern.match(text.strip()):
                    return None
                try:
                    parsed = date_parser.parse(text.strip().replace('_', ' '), fuzzy=False, dayfirst=True)
                except (ValueError, OverflowError, TypeError):
                    return None
                if parsed.year < 2000 or parsed.year > 2100:
                    return None
                return parsed

            # ===== 方法1: 用树状结构精确定位(优先) =====
            hd_node = getattr(self, "_hd_record_node", None)
            if hd_node is not None:
                try:
                    date_entry_divs = hd_node.find_elements(
                        By.XPATH,
                        "./span/div[@data-type='19']"
                    )
                except Exception:
                    date_entry_divs = []

                entries = []  # [(text, link_element), ...]
                for d in date_entry_divs:
                    try:
                        name = (d.get_attribute("data-unitname") or "").strip()
                    except Exception:
                        continue
                    # 排除非日期条目
                    if not name or "open full view" in name.lower() or "more file" in name.lower():
                        continue
                    try:
                        link = d.find_element(By.XPATH, ".//a[contains(@class,'treeLeaf')]")
                    except NoSuchElementException:
                        continue
                    entries.append((name, link))

                if entries:
                    logger.info(f"✓ Found {len(entries)} date entries under HD record tree node")
                    best_name, best_link, best_date = None, None, None
                    for name, link in entries:
                        parsed = parse_date_text(name)
                        if parsed is not None and (best_date is None or parsed > best_date):
                            best_date, best_name, best_link = parsed, name, link

                    # 解析全部失败就直接用第一个(树本身已经按最新排在最前面)
                    if best_link is None:
                        best_name, best_link = entries[0]
                        logger.info(f"ℹ️  日期解析失败，直接使用列表第一项: {best_name}")
                    else:
                        logger.info(f"✓ Most recent date found: {best_name}")

                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", best_link
                    )
                    time.sleep(0.3)
                    best_link.click()
                    logger.info(f"✓ Clicked date record: {best_name}")
                    time.sleep(2)
                    return True
                else:
                    logger.info("ℹ️  树节点下没找到日期条目，改用兜底方式")
            else:
                logger.info("ℹ️  没有保存的HD记录树节点引用，改用兜底方式")

            # ===== 方法2(兜底): 原来的"扫描表格"方式 =====
            def collect_candidates_scoped():
                heading = self._find_element_prefer_current_frame(
                    By.XPATH,
                    "//*[contains(text(),'HAEMODIALYSIS') and contains(text(),'TREATMENT')"
                    " and contains(text(),'RECORD')]"
                )
                if heading is None:
                    return []
                try:
                    return heading.find_elements(
                        By.XPATH, "./following::table[1]//td | ./following::table[1]//a"
                    )
                except Exception:
                    return []

            def collect_candidates_broad():
                return self._find_elements_prefer_current_frame(
                    By.XPATH, "//table//td | //table//a"
                )

            def pick_best_date(candidates):
                best_element, best_date = None, None
                for el in candidates:
                    try:
                        text = el.text.strip()
                    except Exception:
                        continue
                    parsed = parse_date_text(text)
                    if parsed is None:
                        continue
                    if best_date is None or parsed > best_date:
                        best_date, best_element = parsed, el
                return best_element, best_date

            candidates = collect_candidates_scoped()
            best_element, best_date = pick_best_date(candidates) if candidates else (None, None)

            if best_element is None:
                logger.info("ℹ️  在HD记录标题附近没找到日期，改为全页面扫描...")
                candidates = collect_candidates_broad()
                if candidates:
                    best_element, best_date = pick_best_date(candidates)

            if best_element is not None:
                logger.info(f"✓ Most recent date found: {best_date.strftime('%Y-%m-%d')}")
                target = best_element
                if best_element.tag_name.lower() == "td":
                    try:
                        row = best_element.find_element(By.XPATH, "./ancestor::tr[1]")
                        link = row.find_element(By.TAG_NAME, "a")
                        target = link
                    except NoSuchElementException:
                        target = best_element

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", target
                )
                time.sleep(0.3)
                target.click()
                logger.info("✓ Clicked most recent date record")
                time.sleep(2)
                return True

            logger.info("ℹ️  Could not match any strict date pattern, falling back to first row")
            first_row = self._find_element_prefer_current_frame(
                By.XPATH, "//table//tbody//tr[1]//a | //table//tbody//tr[1]//td"
            )
            if first_row is not None:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", first_row
                )
                first_row.click()
                logger.info("✓ Clicked first row as fallback")
                time.sleep(2)
                return True

            logger.error("❌ Could not find any date record to click")
            self.take_screenshot("most_recent_date_not_found.png")
            self.dump_page_source("most_recent_date_not_found.html")
            return False

        except Exception as e:
            logger.error(f"❌ Click most recent date error: {e}")
            self.take_screenshot("most_recent_date_error.png")
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
            
    def _switch_to_main_frame_if_present(self, timeout=8):
        """
        这个系统有个特殊机制(从main.jsp源码里的OpenEditForm/OpenMainFrame函数看出来的):
        点击病历记录(比如"最近日期"那条记录)后，真正可编辑的表单视图
        (就是带铅笔图标、左上角有存盘/打印/checkmark工具栏的那个页面)，
        是通过 parent.OpenMainFrame() 加载到顶层文档里一个固定id的iframe: id="main-frame"。
        这个iframe和Tab页签(比如NURSING NOTES)所在的iframe是"兄弟"关系，不是嵌套关系，
        所以不能指望"跨iframe扫描"顺理成章地扫到它——必须显式切回顶层文档，
        再精确切换进 id="main-frame"，才能保证后续操作(点编辑/填数据/保存)在正确的地方进行。

        返回True表示成功切换进去了(说明main-frame已经加载了实际内容)，
        返回False表示main-frame不存在或者还是空白(about:blank)，
        这种情况下调用方应该回退到原来的搜索逻辑。
        """
        try:
            self.driver.switch_to.default_content()
            main_frame_el = self.driver.find_element(By.ID, "main-frame")

            # 等待main-frame的src不再是about:blank(说明内容已经加载)
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: main_frame_el.get_attribute("src") not in (None, "", "about:blank")
                )
            except TimeoutException:
                logger.info("ℹ️  #main-frame 的src还是about:blank，可能内容还没加载/这次没有用这个iframe")
                self.driver.switch_to.default_content()
                return False

            self.driver.switch_to.frame(main_frame_el)
            logger.info("✓ 已切换进 #main-frame (patient facesheet 视图)")

            # 再往下切一层: main-frame内部还有一个 id="editFrame" 的iframe，
            # 真正的表单字段(那些没有id/name、靠标签文字定位的input)是在这一层里的。
            # (从DevTools面包屑确认过: div#editregion > iframe#editFrame > table.recordTbl/tbl1)
            try:
                edit_frame_el = self.driver.find_element(By.ID, "editFrame")
                self.driver.switch_to.frame(edit_frame_el)
                logger.info("✓ 已进一步切换进 #editFrame (表单字段实际所在的iframe)")
            except NoSuchElementException:
                logger.info("ℹ️  当前层级没有 #editFrame，维持在 #main-frame 继续操作")
            except Exception as e:
                logger.info(f"ℹ️  切换到#editFrame时出现异常，维持在#main-frame: {e}")

            return True
        except NoSuchElementException:
            logger.info("ℹ️  页面上没有找到 #main-frame 元素")
            self.driver.switch_to.default_content()
            return False
        except Exception as e:
            logger.warning(f"⚠️  切换到 #main-frame 时出错: {e}")
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            return False

    def click_edit_button(self):
        """
        步骤6: 点击编辑按钮（铅笔图标）
        Step 6: Click edit button (pencil icon)
        """
        try:
            logger.info("✏️ Step 6: Clicking edit button...")
            time.sleep(2)

            # 优先尝试精确切换进 #main-frame (数字表单视图所在的iframe)
            switched = self._switch_to_main_frame_if_present()
            if not switched:
                logger.info("ℹ️  未能切换进#main-frame，继续用原来的查找方式(当前frame/跨frame扫描)")
            
            # 方法1(最精确，优先尝试): 根据实际HTML确认过的精确特征
            # <img onmousedown="DoDigitalEdit(this)" src="radial1/edit2.png">
            edit_button = self._find_element_prefer_current_frame(
                By.XPATH,
                "//img[contains(@onmousedown, 'DoDigitalEdit')] | "
                "//img[contains(@src, 'edit2.png')]"
            )
            if edit_button is not None:
                logger.info("✓ 用精确特征(DoDigitalEdit/edit2.png)找到铅笔图标")

            # 方法2: 通过常见的"编辑图标"写法查找(跨iframe查找，范围更宽泛)
            if edit_button is None:
                edit_button = self._find_element_prefer_current_frame(
                    By.XPATH,
                    "//button[contains(@class, 'edit')] | "
                    "//a[contains(@title, 'Edit')] | "
                    "//img[contains(@src, 'edit') or contains(@src, 'pencil') or "
                    "contains(translate(@title,'EDIT','edit'), 'edit') or "
                    "contains(translate(@alt,'EDIT','edit'), 'edit') or "
                    "contains(translate(@title,'EDIT','edit'), 'pencil') or "
                    "contains(translate(@alt,'EDIT','edit'), 'pencil')] | "
                    "//*[contains(@class, 'pencil')] | "
                    "//i[contains(@class, 'fa-pencil') or contains(@class, 'fa-edit') or "
                    "contains(@class, 'glyphicon-pencil') or contains(@class, 'bi-pencil') or "
                    "contains(@class, 'oi-pencil')] | "
                    "//*[@title='Edit' or @title='EDIT' or @alt='Edit' or @alt='EDIT']"
                )
            
            # 方法3: 通过文本(跨iframe查找)
            if edit_button is None:
                edit_button = self._find_element_prefer_current_frame(
                    By.XPATH,
                    "//button[contains(text(), 'Edit')] | //a[contains(text(), 'Edit')] | "
                    "//button[contains(text(), 'EDIT')] | //a[contains(text(), 'EDIT')]"
                )

            # 方法4(兜底): 按坐标位置找。
            if edit_button is None:
                logger.info("ℹ️  常规选择器都没找到，改用坐标位置定位铅笔图标...")
                edit_button = self.driver.execute_script(r"""
                    var re = /^\d{4}-\d{1,2}-\d{1,2}[_\s]\d{1,2}:\d{2}$/;
                    var all = document.querySelectorAll('body *');
                    var heading = null;
                    for (var i=0; i<all.length; i++) {
                        var el = all[i];
                        if (el.children.length === 0) {
                            var t = (el.innerText || el.textContent || '').trim();
                            if (re.test(t)) { heading = el; break; }
                        }
                    }
                    if (!heading) return null;
                    var hRect = heading.getBoundingClientRect();
                    var targetX = hRect.left + hRect.width/2;
                    var targetY = hRect.bottom + 40;

                    var candidates = document.querySelectorAll('img, svg, span, a, i, button, div');
                    var best = null, bestDist = Infinity;
                    for (var j=0; j<candidates.length; j++) {
                        var c = candidates[j];
                        if (c === heading || c.contains(heading)) continue;
                        var r = c.getBoundingClientRect();
                        if (r.width === 0 || r.height === 0 || r.width > 100 || r.height > 100) continue;
                        var cx = r.left + r.width/2;
                        var cy = r.top + r.height/2;
                        var dist = Math.pow(cx-targetX,2) + Math.pow(cy-targetY,2);
                        if (dist < bestDist) { bestDist = dist; best = c; }
                    }
                    return best;
                """)
                if edit_button is not None:
                    logger.info("✓ 用坐标位置找到了疑似铅笔图标的元素")

            if edit_button is None:
                logger.error("❌ Could not find Edit button anywhere (main page or iframes)")
                self.take_screenshot("edit_button_error.png")
                self.dump_page_source("edit_button_not_found.html")
                return False

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", edit_button
            )
            time.sleep(0.3)

            # 这个图标绑定的是 onmousedown 事件(不是onclick!)，
            # Selenium原生的.click()通常会完整模拟mousedown+mouseup+click,应该能触发，
            # 但如果原生click失败，JS兜底也要显式派发mousedown事件(而不是只调用.click())，
            # 否则onmousedown绑定的处理函数不会被触发。
            try:
                edit_button.click()
            except Exception as e:
                logger.info(f"  ⚠️  Native click failed ({e}), trying JS mousedown dispatch...")
                self.driver.execute_script(
                    """
                    var el = arguments[0];
                    var evt = new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window});
                    el.dispatchEvent(evt);
                    var evtUp = new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window});
                    el.dispatchEvent(evtUp);
                    var evtClick = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                    el.dispatchEvent(evtClick);
                    """,
                    edit_button
                )
            logger.info("✓ Edit button clicked")
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

        真实结构确认过(两种表格):
        1. tbl1 (Height/Weight/Dialyzer等): <td>标签</td><td><input></td>，取紧邻的下一个td
        2. recordTbl (DATE/NUMBER OF HD/.../HOURLY OBSERVATION/KT_V等):
           标签在<th>里，且每行有多个<td>(多天并排，日期是预先排好班印好的，
           不是每列都已经有数据)。class="copy"的那个<td>是隐藏列(CSS: .copy{display:none})，
           要跳过，不是要填的目标。

        关键修正: 之前的版本无脑抓"最后一个可见列"去填，这是错的——
        如果那一列已经有真实数据(比如是过去某天已经填过的记录)，会被覆盖篡改！
        现在改成:
        1. 先看DATE那一行，找有没有哪一列的日期已经等于要填的目标日期(排班预先印好的)
        2. 找到就用那一列(不碰其他列)
        3. 找不到就点表格自带的"Add"按钮新增一列，把日期填进新列，再用这一列
        """
        try:
            logger.info("📝 Step 7: Filling data...")
            time.sleep(1)

            if self._accept_alert_if_present(timeout=2):
                logger.info("ℹ️  Step7开始时发现并处理了一个残留弹窗")

            switched = self._switch_to_main_frame_if_present()
            if not switched:
                logger.info("ℹ️  未能切换进#main-frame/#editFrame，继续用当前frame/跨frame扫描")

            self.take_screenshot("step7_start.png")
            self.dump_page_source("step7_start.html")

            UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ/"
            lower = "abcdefghijklmnopqrstuvwxyz "  # 顺便把"/"转成空格,兼容 KT/V <-> KT_V

            def find_current_frame_only(xpath):
                """
                只在当前frame里查找，找不到就返回None，绝不触发昂贵且有副作用的
                跨iframe扫描(_find_element_in_any_frame会来回切换frame，
                连续失败几次后可能把driver"带偏"到别的frame，
                导致后面target_table这个引用失效)。
                适用场景: 已经确定字段应该在哪个范围内(tbl1/recordTbl)，
                找不到就是真的没有，不需要再去别的地方瞎找。
                """
                try:
                    return self.driver.find_element(By.XPATH, xpath)
                except NoSuchElementException:
                    return None
                except Exception:
                    return None

            def locate_tbl1_field(field_name_lower):
                """
                tbl1结构: label在td, 取紧邻的下一个td(单列，不涉及日期列的问题)。
                注意: 必须限定在 table.tbl1 这张表格范围内搜索，
                不然"date"这种词会误撞到页面其他地方(比如病人信息表头的"Date/Time"栏)，
                抓到不相关、不可编辑的元素，导致 invalid element state 报错。
                """
                el = find_current_frame_only(
                    f"//table[contains(@class,'tbl1')]//td[translate(normalize-space(text()), "
                    f"'{UPPER}', '{lower}')='{field_name_lower}']/following-sibling::td[1]//input | "
                    f"//table[contains(@class,'tbl1')]//td[translate(normalize-space(text()), "
                    f"'{UPPER}', '{lower}')='{field_name_lower}']/following-sibling::td[1]//select"
                )
                if el is not None:
                    return el
                # 放宽版: label可能是"包含"而非精确相等(比如带单位符号)，同样限定在tbl1范围内
                return find_current_frame_only(
                    f"//table[contains(@class,'tbl1')]//td[contains(translate("
                    f"normalize-space(text()), '{UPPER}', '{lower}'), '{field_name_lower}')]"
                    f"/following-sibling::td//input | "
                    f"//table[contains(@class,'tbl1')]//td[contains(translate("
                    f"normalize-space(text()), '{UPPER}', '{lower}'), '{field_name_lower}')]"
                    f"/following-sibling::td//select"
                )

            def get_all_recordtbl_tables():
                """
                这个月的记录可能被拆成好几张独立的recordTbl表格并排/堆叠在页面上
                (真实数据验证过: table-number="1"到"5"，每张覆盖几天不同的日期)，
                不能只看文档里第一张，要把全部都找出来。
                """
                return self._find_elements_prefer_current_frame(
                    By.XPATH, "//table[contains(@class,'recordTbl')]"
                ) or []

            def get_row_in_table(table_el, field_name_lower):
                """在指定的某一张表格元素内部找label(th)匹配的那一行<tr>"""
                try:
                    return table_el.find_element(
                        By.XPATH,
                        f".//tr[contains(translate(normalize-space(th[1]), "
                        f"'{UPPER}', '{lower}'), '{field_name_lower}')]"
                    )
                except NoSuchElementException:
                    return None

            def get_visible_cells(row):
                """一行里所有非copy(即可见)的<td>，按顺序"""
                try:
                    return row.find_elements(By.XPATH, "./td[not(contains(@class,'copy'))]")
                except Exception:
                    return []

            def locate_recordtbl_field(field_name_lower, target_table, column_index):
                """recordTbl结构: label在th, 在指定的那张表格里取第column_index个(0-based)可见列"""
                if target_table is None or column_index is None:
                    return None
                row = get_row_in_table(target_table, field_name_lower)
                if row is None:
                    return None
                cells = get_visible_cells(row)
                if column_index >= len(cells):
                    return None
                cell = cells[column_index]
                for tag in ("input", "select", "textarea"):
                    try:
                        return cell.find_element(By.TAG_NAME, tag)
                    except NoSuchElementException:
                        continue
                return None

            def normalize_date(raw):
                """把各种日期格式统一转成Origin要的 DD-MM-YYYY"""
                if not raw:
                    return raw
                try:
                    from dateutil import parser as date_parser
                    parsed = date_parser.parse(str(raw).strip(), dayfirst=True, fuzzy=False)
                    return parsed.strftime("%d-%m-%Y")
                except Exception as e:
                    logger.warning(f"  ⚠️  日期格式规范化失败('{raw}'): {e}，原样使用")
                    return raw

            def find_target_table_and_column(target_date_str):
                """
                在所有recordTbl表格里挨个找DATE行，看哪张表格的哪一列日期等于target_date_str。
                找到了返回 (table_element, column_index)。
                都没找到的话，取【最后一张表格】(table-number最大，代表最新的一期)，
                点它的Add按钮新增一列，返回新列所在的 (table_element, column_index)。
                """
                tables = get_all_recordtbl_tables()
                if not tables:
                    logger.warning("  ⚠️  页面上没有找到任何recordTbl表格")
                    return None, None

                logger.info(f"  ℹ️  页面上共有 {len(tables)} 张recordTbl表格，逐一检查DATE行...")

                for t_idx, table_el in enumerate(tables):
                    date_row = get_row_in_table(table_el, "date")
                    if date_row is None:
                        continue
                    cells = get_visible_cells(date_row)
                    for idx, cell in enumerate(cells):
                        try:
                            date_input = cell.find_element(By.TAG_NAME, "input")
                            cell_date = normalize_date(date_input.get_attribute("value"))
                        except Exception:
                            continue
                        if cell_date and cell_date == target_date_str:
                            logger.info(
                                f"✓ 在第{t_idx+1}张表格(table-number)的第{idx+1}列找到匹配日期 "
                                f"{target_date_str}，使用这一列"
                            )
                            return table_el, idx

                # 所有表格都没有匹配的日期列 -> 用最后一张表格(最新一期)新增一列
                last_table = tables[-1]
                logger.info(
                    f"ℹ️  {len(tables)} 张表格里都没有日期为 {target_date_str} 的列，"
                    f"在最后一张(第{len(tables)}张)表格里尝试点击Add新增一列..."
                )

                date_row = get_row_in_table(last_table, "date")
                if date_row is None:
                    logger.error("❌ 最后一张表格里找不到DATE这一行，无法新增列")
                    return None, None
                cells = get_visible_cells(date_row)

                add_button = None
                try:
                    add_button = last_table.find_element(
                        By.XPATH,
                        ".//button[contains(@class,'btn-addcolumn')] | "
                        ".//*[contains(@onclick,'AddColumnVertical')]"
                    )
                except NoSuchElementException:
                    pass
                if add_button is None:
                    logger.error("❌ 最后一张表格里找不到'Add'按钮，无法新增日期列")
                    return None, None

                before_count = len(cells)
                try:
                    self.driver.execute_script("arguments[0].click();", add_button)
                except Exception as e:
                    logger.error(f"❌ 点击Add按钮失败: {e}")
                    return None, None
                time.sleep(1.5)

                date_row = get_row_in_table(last_table, "date")  # 重新获取，避免stale element
                new_cells = get_visible_cells(date_row) if date_row is not None else []
                if len(new_cells) <= before_count:
                    logger.error("❌ 点击Add后列数没有增加，新增列可能失败了(这个Add按钮可能在当前状态下不可用)")
                    return None, None

                new_idx = len(new_cells) - 1
                try:
                    date_input = new_cells[new_idx].find_element(By.TAG_NAME, "input")
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", date_input)
                    date_input.clear()
                    date_input.send_keys(target_date_str)
                    date_input.send_keys(Keys.ESCAPE)
                    logger.info(f"✓ 新增了第{new_idx+1}列，并填入日期 {target_date_str}")
                except Exception as e:
                    logger.error(f"❌ 新增列后填日期失败: {e}")

                return last_table, new_idx

            basic_data = data.get("basic_data", {})
            filled_count = 0

            # ===== 先确定目标日期对应的表格+列 =====
            # 没有显式提供DATE的话(比如这次只想填HOURLY OBSERVATION，没跑护理记录那部分)，
            # 默认用今天的系统日期去匹配/新增列，而不是直接放弃整个recordTbl。
            target_date = normalize_date(basic_data.get("DATE"))
            if not target_date:
                from datetime import datetime as _dt
                target_date = _dt.now().strftime("%d-%m-%Y")
                logger.info(f"  ℹ️  basic_data里没有DATE，默认使用今天的日期: {target_date}")

            basic_data["DATE"] = target_date  # 规范化后的格式回填，后面统一使用
            target_table, column_index = find_target_table_and_column(target_date)

            # ===== 填入基本数据 =====
            for key, value in basic_data.items():
                if not value:
                    continue
                try:
                    field_name_lower = key.replace("_", " ").strip().lower()

                    input_field = locate_tbl1_field(field_name_lower)
                    if input_field is None:
                        input_field = locate_recordtbl_field(field_name_lower, target_table, column_index)

                    if input_field is None:
                        # 只在当前frame里做一次廉价检查(不触发跨iframe扫描)。
                        # 之前这里用的是 _find_element_prefer_current_frame(By.NAME,...)，
                        # 一旦tbl1/recordTbl都找不到，会触发很耗时的"跨所有iframe扫描"兜底，
                        # 这个扫描过程会来回切换frame，实测发现连续触发几次之后，
                        # 会把driver"带偏"到别的frame上，导致后面target_table这个引用失效、
                        # HOURLY OBSERVATION整个填不进去甚至直接崩溃报错。
                        # 这些字段本来就没有name属性(真实HTML验证过)，这个兜底几乎从没生效过，
                        # 收益很低但风险很高，所以直接去掉，换成不会漂移frame的安全版本。
                        try:
                            input_field = self.driver.find_element(By.NAME, key.lower())
                        except NoSuchElementException:
                            input_field = None

                    if input_field is None:
                        logger.warning(f"  ⚠️  Could not find field for: {key} (尝试匹配的文字: '{field_name_lower}')")
                        # 顺手把这张recordTbl表格里实际存在哪些字段名打进日志，
                        # 这样万一某个字段(比如HRS_OF_HD)一直填不进去，
                        # 直接看日志就知道Origin页面上真实的label文字长什么样，
                        # 不用再另外去翻HTML/截图找。
                        try:
                            if target_table is not None:
                                available = [
                                    th.text.strip()
                                    for th in target_table.find_elements(By.XPATH, ".//tr/th[1]")
                                    if th.text.strip()
                                ]
                                if available:
                                    logger.warning(f"      ℹ️  该表格里实际存在的字段名(recordTbl): {available}")
                        except Exception:
                            pass
                        continue

                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", input_field
                    )

                    tag = input_field.tag_name.lower()
                    if tag == "select":
                        select = Select(input_field)
                        try:
                            select.select_by_visible_text(str(value))
                        except Exception:
                            matched = False
                            for opt in select.options:
                                if opt.text.strip().lower() == str(value).strip().lower():
                                    select.select_by_visible_text(opt.text)
                                    matched = True
                                    break
                            if not matched:
                                raise
                    else:
                        field_class = input_field.get_attribute("class") or ""
                        is_datepicker = "datepicker" in field_class.lower()

                        send_value = str(value)
                        if is_datepicker:
                            # 不管这个日期类字段之前是什么格式(比如"1262025"这种没有分隔符的)，
                            # 统一转成Origin要的 DD-MM-YYYY 格式再填入
                            normalized = normalize_date(send_value)
                            if normalized and normalized != send_value:
                                logger.info(f"  ℹ️  {key} 日期格式已规范化: '{send_value}' → '{normalized}'")
                            send_value = normalized or send_value

                        input_field.clear()
                        input_field.send_keys(send_value)
                        if is_datepicker:
                            input_field.send_keys(Keys.ESCAPE)

                    filled_count += 1
                    logger.info(f"  ✓ {key}: {value}")
                    time.sleep(0.2)

                except Exception as e:
                    logger.warning(f"  ⚠️  Could not fill {key}: {e}")

            # ===== 填入 HOURLY OBSERVATION =====
            # app.py里每条记录的key是: TIME, BP, VP, QB, QD, PULSE, UFR
            # 表单上这一列的input顺序是: TIME, BP, VP, QB, QD, TMP, UFR (7个input)
            # 注意: app的"PULSE"对应表单上的"TMP"位置——两边的数值格式都是"P-xx"这种，
            # 已经用实际数据核实过。
            hourly_obs = data.get("hourly_observations", [])
            filled_hourly = 0

            # 用之前先确认一下target_table这个引用还有效(防御性检查，
            # 万一前面filling basic_data的过程中出现了意外的页面/frame变动，
            # 这里能重新定位一次，而不是直接崩溃或者悄悄填错地方)
            if target_table is not None:
                try:
                    target_table.is_displayed()  # 只是为了触发一次访问，检测是否stale
                except Exception:
                    logger.warning("  ⚠️  target_table引用已失效，重新定位一次...")
                    target_table, column_index = find_target_table_and_column(target_date)

            if hourly_obs and target_table is not None and column_index is not None:
                # 找到目标表格里"HOURLY OBSERVATION"区块所有行，在目标列(column_index)取单元格。
                # 区块从<th>HOURLY OBSERVATION</th>那一行开始，后面紧跟着若干个<th></th>(空标签)
                # 的行都属于同一区块，直到遇到下一个有文字的<th>(比如REMARKS)为止。
                # 注意: 必须限定在target_table这一张具体表格里搜，不能整页面搜。
                rows = target_table.find_elements(By.XPATH, ".//tr[th]")
                hourly_cells = []
                collecting = False
                if rows:
                    for row in rows:
                        try:
                            th_text = row.find_element(By.TAG_NAME, "th").text.strip().upper()
                        except Exception:
                            th_text = ""
                        if "HOURLY OBSERVATION" in th_text:
                            collecting = True
                            cells = get_visible_cells(row)
                            if column_index < len(cells):
                                hourly_cells.append(cells[column_index])
                            continue
                        if collecting:
                            if th_text == "":
                                cells = get_visible_cells(row)
                                if column_index < len(cells):
                                    hourly_cells.append(cells[column_index])
                            else:
                                break  # 遇到下一个有文字的标签(比如REMARKS)，停止收集

                logger.info(f"✓ Found {len(hourly_cells)} hourly observation slot(s) in target column (第{column_index+1}列)")

                field_order = ["TIME", "BP", "VP", "QB", "QD", "PULSE", "UFR"]  # 对应表单里第7个是TMP位置

                for i, obs in enumerate(hourly_obs):
                    if i >= len(hourly_cells):
                        logger.warning(
                            f"  ⚠️  第{i+1}个时间点没有对应的表格行可填"
                            f"(表格里HOURLY OBSERVATION只有{len(hourly_cells)}行空位)"
                        )
                        break
                    if not isinstance(obs, dict):
                        continue

                    cell = hourly_cells[i]
                    try:
                        inputs = cell.find_elements(By.TAG_NAME, "input")
                    except Exception:
                        inputs = []

                    if len(inputs) < 7:
                        logger.warning(f"  ⚠️  第{i+1}个时间点的单元格里input数量不对(找到{len(inputs)}个，预期7个)")

                    for idx, field_key in enumerate(field_order):
                        if idx >= len(inputs):
                            break
                        value = obs.get(field_key, "")
                        if not value:
                            continue
                        try:
                            inp = inputs[idx]
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", inp
                            )
                            inp.clear()
                            inp.send_keys(str(value))
                            filled_hourly += 1
                        except Exception as e:
                            logger.warning(f"  ⚠️  Could not fill hourly[{i}].{field_key}: {e}")

                    time.sleep(0.1)

                logger.info(
                    f"✅ Filled {filled_hourly} hourly-observation field(s) "
                    f"across {min(len(hourly_obs), len(hourly_cells))} time slot(s)"
                )
                filled_count += filled_hourly
            elif hourly_obs and (target_table is None or column_index is None):
                logger.warning("⚠️  没有找到目标日期对应的表格/列，HOURLY OBSERVATION已跳过")

            logger.info(f"✅ Filled {filled_count} fields total")

            if filled_count == 0:
                logger.error("❌ 0个字段被成功填入！很可能是没找到对应的输入框")
                self.dump_page_source("fill_data_zero_filled.html")

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

            # 保持在 #main-frame 里操作
            switched = self._switch_to_main_frame_if_present()
            if not switched:
                logger.info("ℹ️  未能切换进#main-frame，继续用当前frame/跨frame扫描")
            
            # 查找保存按钮(跨iframe查找)
            save_button = self._find_element_prefer_current_frame(
                By.XPATH,
                "//button[contains(text(), 'UPDATE')] | //button[contains(text(), 'SAVE')] | "
                "//input[@value='UPDATE'] | //input[@value='SAVE']"
            )

            if save_button is None:
                logger.error("❌ Could not find Save/Update button anywhere")
                self.take_screenshot("save_error.png")
                self.dump_page_source("save_button_not_found.html")
                return False

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", save_button
            )
            save_button.click()
            logger.info("✓ Save button clicked")
            time.sleep(1.5)

            # 关键: 点击UPDATE/SAVE后，Origin会弹出一个原生JS弹窗("Update Successfully.")，
            # 如果不处理掉，这个弹窗会一直悬在浏览器上，导致【下一步】任何Selenium操作
            # (包括批量处理时return_to_queue()里的driver.get()/switch_to)都会直接抛出
            # UnexpectedAlertPresentException而失败。单个病人模式下影响不大(反正马上就退出关浏览器了)，
            # 但批量模式下如果不在这里确认掉，会导致后面所有病人都处理不了。
            #
            # 之前这里只要"有弹窗就当成功"，哪怕弹窗内容其实是报错(比如某个必填字段
            # 没填、格式不对导致保存被Origin拒绝)，也会被当成保存成功处理；完全没弹窗
            # 出现的时候甚至也直接放行——这就是"日志显示成功、实际Origin里什么都没填上"
            # 这个问题的根本原因。现在改成: 必须真的看到弹窗、而且弹窗文字里明确提到
            # "success"/"成功"，才算真正保存成功；弹窗内容像是报错、或者压根没有弹窗，
            # 都当作保存失败处理，让这个病人在批量结果里正确显示为❌，而不是一个误报的✅。
            alert_text = self._accept_alert_if_present(timeout=5)
            if alert_text:
                if "success" in alert_text.lower() or "成功" in alert_text:
                    logger.info(f"✓ 已确认保存成功弹窗 Confirmed save-success alert: {alert_text}")
                else:
                    logger.error(
                        f"❌ 保存后弹出的提示看起来不是'保存成功'，实际内容: {alert_text}\n"
                        f"很可能是Origin拒绝了这次保存(比如某个必填字段没填/格式不对)，"
                        f"按失败处理，需要人工检查这位病人的数据。"
                    )
                    self.take_screenshot("save_alert_not_success.png")
                    return False
            else:
                logger.error(
                    "❌ 点击保存后没有出现预期的'Update Successfully'确认弹窗，"
                    "无法确认这次保存是否真的生效——按失败处理，需要人工检查这位病人是否真的保存成功。"
                )
                self.take_screenshot("save_no_alert.png")
                self.dump_page_source("save_no_alert.html")
                return False

            time.sleep(1.5)
            
            logger.info("✅ Form saved")
            return True
            
        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            # 即使保存过程中报错，也尝试把可能残留的弹窗关掉，
            # 避免这个异常状态一路带到下一个病人身上
            self._accept_alert_if_present(timeout=2)
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
            
            # 步骤5: 点击最近日期的记录
            log_cb("📅 Step 5/8: 打开最近日期记录 Opening most recent date record...")
            if not self.click_most_recent_date_record():
                log_cb("⚠️  Could not find date record, continuing...")
            log_cb("✅ Step 5 完成")
            
            # 步骤6: 点击编辑
            log_cb("✏️ Step 6/8: 点击编辑 Clicking edit...")
            if not self.click_edit_button():
                log_cb("❌ 找不到编辑按钮，表单未进入可编辑状态，自动化终止")
                log_cb("❌ Edit button not found — form is not in editable mode, stopping")
                return False
            log_cb("✅ Step 6 完成")
            
            # 步骤7: 填入数据
            log_cb("📝 Step 7/8: 填入数据 Filling data...")
            fill_success = self.fill_data_in_form(data)
            if not fill_success:
                log_cb("❌ 没有任何字段被成功填入 No fields were filled")
            log_cb("✅ Step 7 完成")
            
            # 步骤8: 保存
            log_cb("💾 Step 8/8: 保存 Saving...")
            save_success = self.save_form()
            if not save_success:
                log_cb("⚠️  Could not verify save")
            log_cb("✅ Step 8 完成")
            
            if fill_success and save_success:
                log_cb("✅ 自动化完成，数据已填入并保存！Automation completed successfully!")
            else:
                log_cb("⚠️  自动化流程跑完了，但数据可能没有真正填入/保存，请手动检查表单！")
                log_cb("⚠️  Automation ran to completion, but data may NOT actually be filled/saved — please verify manually!")
            self.take_screenshot("success.png")
            return fill_success and save_success
            
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

    # ============================================================
    # 批量处理 Batch Processing
    # ============================================================

    def return_to_queue(self, callback=None):
        """
        批量处理时，处理完一个病人后，尝试回到 Dialysis Queue，
        以便继续处理名单里的下一个病人。

        分三层尝试(跟本文件其他方法一样，从精确到兜底)：
        1. 切回顶层文档，重新导航到 origin_url —— 因为浏览器session还在，
           大概率会直接落回病人列表(Dialysis Queue)页面，不需要重新登录。
        2. 如果重新导航后又落到了部门选择页("WELCOME TO ORIGIN")，
           说明部门选择状态被重置了，重新执行一次 login_step2_department()。
        3. 如果连登录页都被踢出来了(session失效)，返回False，
           交给调用方(run_batch_automation)决定要不要整个重新登录。

        返回True表示已经回到了可以查找病人的页面(Dialysis Queue或部门选择已处理完毕)，
        返回False表示需要调用方重新走一次完整登录流程。
        """
        def log_cb(msg):
            if callback:
                callback(msg)
            logger.info(msg)

        try:
            log_cb("🔙 返回病人队列 Returning to Dialysis Queue...")

            # 防御性处理: 万一上一步(比如保存)留下了没确认的弹窗，
            # 先确认掉，不然接下来的 switch_to/driver.get() 会直接因为
            # UnexpectedAlertPresentException 而失败
            self._accept_alert_if_present(timeout=2)

            self.driver.switch_to.default_content()

            url = self.origin_urls[0] if self.origin_urls else None
            if url:
                self.driver.get(url)
                time.sleep(2)

            page_upper = self.driver.page_source.upper()

            # 情况1: 又落回了部门选择页
            if "WELCOME" in page_upper:
                log_cb("ℹ️  回到了部门选择页，重新选择 HAEMODIALYSIS UNIT...")
                if self.login_step2_department():
                    log_cb("✓ 已回到病人队列")
                    return True
                log_cb("⚠️  重新选择部门失败")
                return False

            # 情况2: session似乎已经失效，被踢回登录页
            # 用真正的DOM元素检测——页面上是否存在一个"密码"类型的<input>——
            # 而不是简单地在整份页面源码文字里搜"PASSWORD"这几个字。
            # 原来的文字匹配方式很容易误判：队列页面本身就可能带有
            # "Change Password"之类的菜单链接，文字里天然含有这几个词，
            # 结果被误判成"被踢出登录页"，触发了根本不需要的重新登录——
            # 而重新登录时session其实还有效，反而会因为页面上真的没有登录表单
            # (被自动跳过，直接落回队列/部门页)而彻底失败，导致该病人被跳过。
            password_inputs = self.driver.find_elements(By.XPATH, "//input[@type='password']")
            if password_inputs:
                log_cb("⚠️  检测到登录表单(密码输入框)，Session可能已失效，需要重新登录")
                return False

            # 情况3: 大概率已经直接落在病人队列页面
            log_cb("✓ 已回到病人队列页面")
            return True

        except Exception as e:
            log_cb(f"⚠️  返回队列时出错 Error returning to queue: {e}")
            return False

    def process_single_patient_in_session(self, mrn, data, callback=None):
        """
        在【已经登录】的会话里，处理单个病人的步骤3-8
        (查找病人 -> 打开治疗记录 -> 打开最近日期 -> 点编辑 -> 填数据 -> 保存)。
        不负责登录/初始化浏览器/关闭浏览器 —— 这些由调用方(run_batch_automation)负责，
        这样多个病人可以复用同一个已登录的session，不用每个病人都重新登录一次。

        返回一个 dict: {"success": bool, "reason": str}
        """
        def log_cb(msg):
            if callback:
                callback(msg)
            logger.info(msg)

        result = {"success": False, "reason": ""}
        try:
            log_cb(f"🔍 查找病人 Finding patient MRN {mrn}...")
            if not self.find_patient_in_queue(mrn):
                result["reason"] = "找不到病人 Patient not found in queue"
                log_cb(f"❌ {result['reason']}")
                return result

            log_cb("📋 打开治疗记录 Opening HD treatment record...")
            if not self.open_hd_treatment_record():
                result["reason"] = "无法打开治疗记录 Could not open HD record"
                log_cb(f"❌ {result['reason']}")
                return result

            log_cb("📅 打开最近日期记录 Opening most recent date record...")
            if not self.click_most_recent_date_record():
                log_cb("⚠️  找不到最近日期记录，继续尝试编辑当前视图...")

            log_cb("✏️ 点击编辑 Clicking edit...")
            if not self.click_edit_button():
                result["reason"] = "找不到编辑按钮，表单未进入可编辑状态 Edit button not found"
                log_cb(f"❌ {result['reason']}")
                return result

            log_cb("📝 填入数据 Filling data...")
            fill_success = self.fill_data_in_form(data)
            if not fill_success:
                log_cb("⚠️  没有任何字段被成功填入 No fields were filled")

            log_cb("💾 保存 Saving...")
            save_success = self.save_form()
            if not save_success:
                log_cb("⚠️  无法确认保存状态 Could not verify save")

            result["success"] = bool(fill_success and save_success)
            if not result["success"]:
                result["reason"] = "数据可能没有完全填入/保存，请手动检查 Please verify manually"
            return result

        except Exception as e:
            result["reason"] = str(e)
            log_cb(f"❌ 处理该病人时出错 Error processing patient: {e}")
            self.take_screenshot(f"batch_error_{mrn}.png")
            return result

    def run_batch_automation(self, username, password, jobs, callback=None):
        """
        批量处理多个病人：只登录一次，依次处理名单里的每一个病人，
        全部处理完才统一关闭浏览器。

        jobs: list of dict，每个dict至少要有:
            {
                "mrn": "22001725",              # 病人MRN(病历号)，必须
                "name": "GOH GAIK MOOI",         # 病人姓名，仅用于显示/日志
                "data": {                        # 跟 collect_all_data() 返回格式一致
                    "basic_data": {...},
                    "hourly_observations": [...]
                }
            }

        返回一个 list，每个元素对应一位病人的处理结果:
            {"mrn": ..., "name": ..., "success": bool, "reason": str}
        """
        def log_cb(msg):
            if callback:
                callback(msg)
            logger.info(msg)

        results = []
        total = len(jobs)

        try:
            log_cb("⏳ 初始化浏览器 Initializing...")
            if not self.initialize_driver():
                log_cb("❌ 浏览器初始化失败，批量处理终止")
                return results

            log_cb("🔐 登录 Login...")
            if not self.login_step1_credentials(username, password):
                log_cb("❌ 登录失败，批量处理终止 Login failed, batch stopped")
                return results
            if not self.login_step2_department():
                log_cb("❌ 部门选择失败，批量处理终止 Department selection failed")
                return results
            log_cb(f"✅ 登录成功，开始批量处理 {total} 位病人")

            for idx, job in enumerate(jobs, start=1):
                mrn = str(job.get("mrn", "")).strip()
                name = job.get("name") or mrn
                data = job.get("data", {})

                log_cb(f"\n{'='*50}")
                log_cb(f"👤 [{idx}/{total}] 处理病人 Processing: {name} (MRN: {mrn})")
                log_cb(f"{'='*50}")

                if not mrn:
                    log_cb(f"❌ [{name}] 缺少MRN，跳过该病人")
                    results.append({"mrn": mrn, "name": name, "success": False, "reason": "缺少MRN"})
                    continue

                # 第一个病人不需要"返回队列"(登录后本来就在队列页附近)
                if idx > 1:
                    back_ok = self.return_to_queue(callback)
                    if not back_ok:
                        log_cb("🔁 尝试重新登录 Re-authenticating...")
                        relogin_ok = (
                            self.login_step1_credentials(username, password)
                            and self.login_step2_department()
                        )
                        if not relogin_ok:
                            log_cb(f"❌ [{name}] 重新登录失败，跳过该病人")
                            results.append({
                                "mrn": mrn, "name": name,
                                "success": False, "reason": "重新登录失败 Re-login failed"
                            })
                            continue

                patient_result = self.process_single_patient_in_session(mrn, data, callback)
                results.append({
                    "mrn": mrn, "name": name,
                    "success": patient_result["success"],
                    "reason": patient_result["reason"]
                })

                status_icon = "✅" if patient_result["success"] else "⚠️"
                log_cb(f"{status_icon} [{name}] 处理完毕")

            # 批量处理总结
            success_count = sum(1 for r in results if r["success"])
            log_cb(f"\n{'='*50}")
            log_cb(f"📊 批量处理完成 Batch complete: {success_count}/{total} 成功")
            for r in results:
                mark = "✅" if r["success"] else "❌"
                extra = f" — {r['reason']}" if r["reason"] else ""
                log_cb(f"  {mark} {r['name']} (MRN: {r['mrn']}){extra}")
            log_cb(f"{'='*50}")

            return results

        except Exception as e:
            log_cb(f"❌ 批量处理发生严重错误 Batch automation error: {e}")
            self.take_screenshot("batch_automation_error.png")
            return results

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