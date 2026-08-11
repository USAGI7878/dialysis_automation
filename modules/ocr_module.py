"""
Dialysis OCR Module - Tesseract Enhanced Version
透析OCR识别模块 - Tesseract增强版

使用Tesseract OCR + 图像预处理提升识别准确率
Uses Tesseract OCR with image preprocessing for better accuracy
"""

import re
import os
import json
import shutil
import logging
from typing import Dict, List, Optional
from pathlib import Path
import cv2
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Windows上常见的Tesseract安装路径，找不到PATH配置时依次尝试这几个
def _get_common_tesseract_paths():
    paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    # 没有用管理员权限装的话，安装程序默认会装到"当前用户"目录下，
    # 比如 C:\Users\某某\AppData\Local\Programs\Tesseract-OCR\tesseract.exe
    # 用环境变量动态拼，不写死用户名，换电脑/换账号也能用
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        paths.append(os.path.join(local_appdata, "Programs", "Tesseract-OCR", "tesseract.exe"))
    return paths


COMMON_TESSERACT_PATHS = _get_common_tesseract_paths()


def find_tesseract_executable(config_path="config.json"):
    """
    自动找Tesseract可执行文件的位置，依次尝试:
    1. config.json 里的 "tesseract_path" 字段(如果你的路径比较特殊，可以在这里手动指定)
    2. 系统PATH环境变量(如果装的时候勾选了"Add to PATH"就能找到)
    3. Windows上几个最常见的默认安装路径

    找不到就返回None，调用方需要自行处理(比如报错提示用户手动安装/配置)。
    """
    # 1. config.json
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            configured = cfg.get("tesseract_path")
            if configured and os.path.exists(configured):
                logger.info(f"✓ 使用config.json里配置的Tesseract路径: {configured}")
                return configured
    except Exception as e:
        logger.warning(f"读取config.json的tesseract_path失败: {e}")

    # 2. PATH环境变量
    found_in_path = shutil.which("tesseract")
    if found_in_path:
        logger.info(f"✓ 在系统PATH里找到Tesseract: {found_in_path}")
        return found_in_path

    # 3. 常见安装路径
    for candidate in COMMON_TESSERACT_PATHS:
        if os.path.exists(candidate):
            logger.info(f"✓ 在默认安装路径找到Tesseract: {candidate}")
            return candidate

    logger.warning(
        "⚠️  没有自动找到Tesseract安装位置。"
        "可以在config.json里加一行 \"tesseract_path\": \"你的tesseract.exe完整路径\" 手动指定。"
    )
    return None


class DialysisOCR:
    """增强版OCR识别类 - 使用Tesseract + OpenCV预处理"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        r"""
        初始化OCR引擎
        Initialize OCR engine
        
        Args:
            tesseract_path: Tesseract安装路径 (Windows需要，不传则自动检测)
                          例如: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        """
        self.tesseract_available = False
        
        try:
            import pytesseract
            from PIL import Image
            
            # 没有显式传tesseract_path的话，自动去找(config.json/PATH/常见安装路径)
            if not tesseract_path:
                tesseract_path = find_tesseract_executable()

            # Windows系统需要指定Tesseract路径
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # 测试Tesseract是否可用
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract OCR {version} initialized successfully!")
            
            self.pytesseract = pytesseract
            self.Image = Image
            self.tesseract_available = True
            
        except ImportError:
            logger.error("❌ pytesseract not installed!")
            logger.error("Please install: pip install pytesseract")
            logger.error("And download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        except Exception as e:
            logger.error(f"❌ Tesseract initialization failed: {e}")
            logger.error("Make sure Tesseract is installed and path is correct")
    def preprocess_image(self, image_path: str, method: str = 'adaptive') -> np.ndarray:
        """
        图像预处理以提升OCR准确率
        Preprocess image for better OCR accuracy
        
        Args:
            image_path: 图片路径
            method: 预处理方法 ('adaptive', 'otsu', 'simple')
            
        Returns:
            处理后的图像
        """
        try:
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # 转灰度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 降噪
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # 根据方法选择二值化
            if method == 'adaptive':
                # 自适应阈值（适合光照不均）
                processed = cv2.adaptiveThreshold(
                    denoised, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
            elif method == 'otsu':
                # Otsu二值化（适合双峰直方图）
                _, processed = cv2.threshold(
                    denoised, 0, 255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            else:
                # 简单阈值
                _, processed = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
            
            # 形态学操作去除噪点
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            logger.info(f"✓ Image preprocessed using '{method}' method")
            return processed
            
        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str, preprocess: bool = True) -> str:
        """
        从图片中提取所有文字
        Extract all text from image
        
        Args:
            image_path: 图片路径
            preprocess: 是否进行预处理
            
        Returns:
            识别的文字
        """
        if not self.tesseract_available:
            logger.error("❌ Tesseract not available")
            return ""
        
        if not Path(image_path).exists():
            logger.error(f"❌ Image not found: {image_path}")
            return ""
        
        try:
            logger.info(f"📷 Reading image: {Path(image_path).name}")
            
            if preprocess:
                # 预处理图像
                processed = self.preprocess_image(image_path, method='adaptive')
                if processed is not None:
                    # 保存临时图像供Tesseract读取
                    temp_path = "temp_processed.png"
                    cv2.imwrite(temp_path, processed)
                    img = self.Image.open(temp_path)
                else:
                    img = self.Image.open(image_path)
            else:
                img = self.Image.open(image_path)
            
            # Tesseract配置
            custom_config = r'--oem 3 --psm 6'  # LSTM OCR, 统一文本块
            
            # 执行OCR
            text = self.pytesseract.image_to_string(img, config=custom_config)
            
            if not text.strip():
                logger.warning("⚠️  No text detected")
                return ""
            
            logger.info(f"✓ Extracted {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"❌ OCR error: {e}")
            return ""
    
    def extract_text_with_confidence(self, image_path: str, preprocess: bool = True) -> List[Dict]:
        """
        提取文字并返回置信度信息
        Extract text with confidence scores
        
        Returns:
            [{'text': '...', 'confidence': 0.95, 'bbox': (x, y, w, h)}, ...]
        """
        if not self.tesseract_available:
            return []
        
        try:
            if preprocess:
                processed = self.preprocess_image(image_path, method='adaptive')
                if processed is not None:
                    temp_path = "temp_processed.png"
                    cv2.imwrite(temp_path, processed)
                    img = self.Image.open(temp_path)
                else:
                    img = self.Image.open(image_path)
            else:
                img = self.Image.open(image_path)
            
            # 获取详细数据
            data = self.pytesseract.image_to_data(img, output_type=self.pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                # 过滤空文本和低置信度
                if text and conf > 30:  # 30%以上
                    results.append({
                        'text': text,
                        'confidence': conf / 100,  # 转为0-1
                        'bbox': (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                    })
            
            logger.info(f"✓ Found {len(results)} text regions with confidence")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return []
    
    def extract_nursing_record(self, image_path: str) -> Dict[str, str]:
        """
        识别护理记录纸
        Extract data from nursing record
        
        Args:
            image_path: 护理记录照片路径
            
        Returns:
            提取的数据字典
        """
        logger.info("📄 Starting nursing record extraction...")
        
        # 提取文字
        full_text = self.extract_text_from_image(image_path, preprocess=True)
        
        if not full_text:
            logger.warning("⚠️  No text found")
            return self._get_empty_nursing_data()
        
        logger.info(f"📝 Extracted {len(full_text)} characters")
        
        # 初始化数据
        data = self._get_empty_nursing_data()
        
        # 定义识别模式
        patterns = {
            "DATE": [
                r'DATE[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            ],
            "NUMBER_OF_HD": [
                r'(?:NUMBER|NO\.?|#).*?HD[:\s]*(\d{3,4})',
                r'HD.*?(?:NO\.?|#)?[:\s]*(\d{3,4})',
                r'DIALYSIS.*?(\d{3,4})',
            ],
            "HRS_OF_HD": [
                r'(?:HRS?|HOURS?).*?HD[:\s]*(\d+\.?\d*)',
                r'HD.*?(\d+\.?\d*)\s*(?:HRS?|HOURS?)',
                r'\b([2-6])\s*(?:HRS?|HOURS?)',
            ],
            "PRE_BP": [
                r'(?:PRE|BEFORE).*?BP[:\s]*(\d{2,3}[/\\]\d{2,3})',
                r'BP.*?PRE[:\s]*(\d{2,3}[/\\]\d{2,3})',
            ],
            "POST_BP": [
                r'(?:POST|AFTER).*?BP[:\s]*(\d{2,3}[/\\]\d{2,3})',
                r'BP.*?POST[:\s]*(\d{2,3}[/\\]\d{2,3})',
            ],
            "PRE_PULSE": [
                r'(?:PRE|BEFORE).*?PULSE[:\s]*(\d{2,3})',
                r'PULSE.*?PRE[:\s]*(\d{2,3})',
            ],
            "TEMPERATURE": [
                r'(?:TEMP|TEMPERATURE)[:\s]*(\d{2}\.\d)',
                r'(3[5-9]\.\d)',
            ],
            "PRE_WEIGHT": [
                r'(?:PRE|BEFORE).*?(?:WEIGHT|WT)[:\s]*(\d{2,3}\.\d{1,2})',
            ],
            "POST_WEIGHT": [
                r'(?:POST|AFTER).*?(?:WEIGHT|WT)[:\s]*(\d{2,3}\.\d{1,2})',
            ],
            "IDWG": [
                r'IDWG[:\s]*(\d+\.?\d*[/\\]\d+\.?\d*)',
            ],
            "UF": [
                r'UF[:\s]*(\d+\.?\d*)',
            ],
            "KT_V": [
                r'KT[/\\]V[:\s]*(\d+\.\d+)',
                r'Kt[/\\]V[:\s]*(\d+\.\d+)',
            ],
            "WEIGHT_LOSS": [
                r'(?:WEIGHT.*?LOSS|LOSS)[:\s]*(\d+\.?\d*)',
            ]
        }
        
        # 提取数据
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    data[key] = match.group(1).strip()
                    logger.info(f"✓ {key}: {data[key]}")
                    break
        
        filled_count = sum(1 for v in data.values() if v)
        logger.info(f"✅ Found {filled_count}/{len(data)} fields")
        
        return data
    
    def extract_machine_screen(self, image_path: str) -> Dict[str, str]:
        """
        识别透析机屏幕
        Extract hourly observation from machine screen
        
        Args:
            image_path: 透析机照片路径
            
        Returns:
            每小时观察数据
        """
        logger.info("📱 Starting machine screen extraction...")
        
        # 提取文字
        full_text = self.extract_text_from_image(image_path, preprocess=True)
        
        if not full_text:
            logger.warning("⚠️  No text found")
            return self._get_empty_machine_data()
        
        logger.info(f"📝 Extracted {len(full_text)} characters")
        
        # 初始化数据
        data = self._get_empty_machine_data()
        
        # 定义识别模式
        patterns = {
            "TIME": [
                r'TIME[:\s]*(\d{1,2}:\d{2})',
                r'(\d{1,2}:\d{2})',
            ],
            "BP": [
                r'BP[:\s]*(\d{2,3}[/\\]\d{2,3})',
                r'(\d{2,3}[/\\]\d{2,3})',
            ],
            "VP": [
                r'VP[:\s]*(\d{2,3})',
                r'VENOUS[:\s]*(\d{2,3})',
            ],
            "QB": [
                r'QB[:\s]*(\d{2,3})',
                r'BLOOD.*?FLOW[:\s]*(\d{2,3})',
            ],
            "QD": [
                r'QD[:\s]*(\d{3,4})',
                r'DIALYSATE[:\s]*(\d{3,4})',
            ],
            "PULSE": [
                r'(P[-:]?\d{2,3})',
                r'PULSE[:\s]*(\d{2,3})',
            ],
            "UFR": [
                r'UFR[:\s]*(\d{2,4})',
                r'UF.*?RATE[:\s]*(\d{2,4})',
            ],
        }
        
        # 提取数据
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if key == "PULSE" and not value.upper().startswith('P'):
                        value = f"P-{value}"
                    data[key] = value
                    logger.info(f"✓ {key}: {data[key]}")
                    break
        
        filled_count = sum(1 for v in data.values() if v)
        logger.info(f"✅ Found {filled_count}/{len(data)} fields")
        
        return data
    
    def _get_empty_nursing_data(self) -> Dict[str, str]:
        """返回空的护理记录数据结构"""
        return {
            "DATE": "",
            "NUMBER_OF_HD": "",
            "HRS_OF_HD": "",
            "PRE_BP": "",
            "POST_BP": "",
            "PRE_PULSE": "",
            "TEMPERATURE": "",
            "PRE_WEIGHT": "",
            "IDWG": "",
            "POST_WEIGHT": "",
            "UF": "",
            "KT_V": "",
            "WEIGHT_LOSS": "",
            "COMFORTABLE": "",
            "DIZZINESS": "",
            "BLEEDING": "",
            "DRESSING": "",
            "REMARKS": ""
        }
    
    def _get_empty_machine_data(self) -> Dict[str, str]:
        """返回空的机器数据结构"""
        return {
            "TIME": "",
            "BP": "",
            "VP": "",
            "QB": "",
            "QD": "",
            "PULSE": "",
            "UFR": ""
        }


# 测试代码
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🧪 TESSERACT OCR MODULE TEST")
    print("="*70 + "\n")
    
    # Windows Tesseract路径（根据实际情况修改）
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    if len(sys.argv) < 2:
        print("📋 Testing OCR initialization...")
        ocr = DialysisOCR(tesseract_path=tesseract_path)
        
        if ocr.tesseract_available:
            print("✅ Tesseract OCR is ready!")
            print("\n📚 Features:")
            print("   - Image preprocessing (denoising, thresholding)")
            print("   - Multiple preprocessing methods")
            print("   - Confidence scores")
            print("   - Better accuracy for medical records")
            print("\n💡 Usage:")
            print("   python ocr_module.py <image_path>")
        else:
            print("❌ Tesseract not available")
            print("\n📥 Installation:")
            print("   1. pip install pytesseract opencv-python")
            print("   2. Download Tesseract:")
            print("      https://github.com/UB-Mannheim/tesseract/wiki")
        
        print("\n" + "="*70 + "\n")
    else:
        image_path = sys.argv[1]
        print(f"📷 Testing with: {image_path}\n")
        
        ocr = DialysisOCR(tesseract_path=tesseract_path)
        
        if ocr.tesseract_available:
            # 测试护理记录
            print("\n📄 NURSING RECORD")
            print("-"*70)
            data = ocr.extract_nursing_record(image_path)
            for key, value in data.items():
                status = '✓' if value else '✗'
                print(f"  {status} {key:20s}: {value or '(not found)'}")
            
            # 测试透析机
            print("\n📱 MACHINE SCREEN")
            print("-"*70)
            data = ocr.extract_machine_screen(image_path)
            for key, value in data.items():
                status = '✓' if value else '✗'
                print(f"  {status} {key:20s}: {value or '(not found)'}")
            
            print("\n" + "="*70 + "\n")
