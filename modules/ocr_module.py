"""
Dialysis OCR Module - Clean Version
透析OCR识别模块 - 干净版

使用EasyOCR识别护理记录纸和透析机屏幕
Uses EasyOCR to recognize nursing records and dialysis machine screens
"""

import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DialysisOCR:
    def __init__(self, use_gpu=False):
        """
        初始化OCR引擎
        Initialize OCR engine
        
        Args:
            use_gpu: 是否使用GPU加速 / Use GPU acceleration
        """
        try:
            import easyocr
            logger.info("⏳ Initializing EasyOCR... 初始化 EasyOCR...")
            self.reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)
            logger.info("✅ EasyOCR initialized successfully! EasyOCR 初始化成功！")
        except Exception as e:
            logger.error(f"❌ Failed to initialize EasyOCR: {e}")
            logger.error("Please install: pip install easyocr")
            self.reader = None
            
    def extract_text_from_image(self, image_path):
        """
        从图片中提取所有文字
        Extract all text from image
        
        Args:
            image_path: 图片路径 / Image path
            
        Returns:
            识别结果列表 / List of recognition results
        """
        if self.reader is None:
            logger.error("❌ OCR engine not initialized")
            return []
            
        try:
            logger.info(f"📷 Reading image: {image_path}")
            
            # OCR识别
            result = self.reader.readtext(image_path)
            
            if not result:
                logger.warning("⚠️  No text detected in image")
                return []
            
            # 提取文字和置信度
            text_results = []
            for detection in result:
                bbox = detection[0]  # 边界框坐标
                text = detection[1]  # 识别的文字
                confidence = detection[2]  # 置信度
                
                text_results.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': bbox
                })
                
            logger.info(f"✓ Detected {len(text_results)} text regions")
            return text_results
            
        except Exception as e:
            logger.error(f"❌ OCR extraction error: {e}")
            return []
            
    def extract_nursing_record(self, image_path):
        """
        识别护理记录纸
        Extract data from nursing record
        
        Args:
            image_path: 护理记录照片路径 / Nursing record image path
            
        Returns:
            提取的数据字典 / Extracted data dictionary
        """
        logger.info("📄 Starting nursing record extraction...")
        
        # 获取所有文字
        text_results = self.extract_text_from_image(image_path)
        
        if not text_results:
            logger.warning("⚠️  No text found in nursing record")
            return {}
        
        # 合并所有文字（用于关键词匹配）
        full_text = ' '.join([item['text'] for item in text_results])
        logger.info(f"📝 Total text extracted: {len(full_text)} characters")
        
        # 初始化数据字典
        data = {
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
            "REMARKS": ""
        }
        
        # 正则表达式模式
        patterns = {
            "DATE": [
                r'(\d{2}[-/]\d{2}[-/]\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
            ],
            "NUMBER_OF_HD": [
                r'(?:NUMBER|NO|#).*?(\d{3,4})',
                r'HD.*?(\d{3,4})',
                r'\b(\d{3,4})\b'  # 任何3-4位数字
            ],
            "HRS_OF_HD": [
                r'(?:HRS|HOURS?).*?(\d+\.?\d*)',
                r'(\d+)\s*(?:HRS?|HOURS?)',
                r'\b([2-6])\b(?:\s*HR|\s*HOUR)'  # 2-6小时
            ],
            "PRE_BP": [
                r'(?:PRE|BEFORE).*?BP.*?(\d{2,3}[/\\]\d{2,3})',
                r'BP.*?(\d{2,3}[/\\]\d{2,3})'
            ],
            "POST_BP": [
                r'(?:POST|AFTER).*?BP.*?(\d{2,3}[/\\]\d{2,3})'
            ],
            "PRE_PULSE": [
                r'(?:PRE|BEFORE).*?PULSE.*?(\d{2,3})',
                r'PULSE.*?(\d{2,3})',
                r'\b([6-9]\d|1[0-2]\d)\b'  # 60-129的数字
            ],
            "TEMPERATURE": [
                r'(?:TEMP|TEMPERATURE).*?(\d{2}\.\d)',
                r'(3[5-9]\.\d)',  # 35.X - 39.X
                r'(\d{2}\.\d)\s*[°C]'
            ],
            "PRE_WEIGHT": [
                r'(?:PRE|BEFORE).*?(?:WEIGHT|WT).*?(\d{2,3}\.\d{1,2})',
                r'(?:WEIGHT|WT).*?(\d{2,3}\.\d{1,2})'
            ],
            "POST_WEIGHT": [
                r'(?:POST|AFTER).*?(?:WEIGHT|WT).*?(\d{2,3}\.\d{1,2})'
            ],
            "IDWG": [
                r'IDWG.*?(\d+\.\d+[/\\]\d+\.\d+)',
                r'(\d+\.\d+[/\\]\d+\.\d+)'
            ],
            "UF": [
                r'UF.*?(\d+\.\d+)',
                r'ULTRAFILTRATION.*?(\d+\.\d+)'
            ],
            "KT_V": [
                r'KT[/\\]V.*?(\d+\.\d+)',
                r'Kt[/\\]V.*?(\d+\.\d+)',
                r'([0-2]\.\d{2})'  # 0.XX - 2.XX
            ],
            "WEIGHT_LOSS": [
                r'(?:WEIGHT.*?LOSS|LOSS).*?(\d+\.\d+)'
            ]
        }
        
        # 使用正则表达式提取数据
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    data[key] = match.group(1)
                    logger.info(f"✓ Extracted {key}: {data[key]}")
                    break
        
        # 特殊处理：如果没有找到日期，尝试查找任何日期格式
        if not data["DATE"]:
            for item in text_results:
                text = item['text']
                date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
                if date_match:
                    data["DATE"] = date_match.group(0)
                    logger.info(f"✓ Found date in separate text: {data['DATE']}")
                    break
        
        filled_count = sum(1 for v in data.values() if v)
        logger.info(f"✅ Nursing record extraction completed. Found {filled_count}/{len(data)} fields")
        
        return data
        
    def extract_machine_screen(self, image_path):
        """
        识别透析机屏幕（每小时观察数据）
        Extract hourly observation data from dialysis machine screen
        
        Args:
            image_path: 透析机照片路径 / Machine screen image path
            
        Returns:
            每小时观察数据字典 / Hourly observation data dictionary
        """
        logger.info("📱 Starting machine screen extraction...")
        
        # 获取所有文字
        text_results = self.extract_text_from_image(image_path)
        
        if not text_results:
            logger.warning("⚠️  No text found in machine screen")
            return {}
        
        # 合并所有文字
        full_text = ' '.join([item['text'] for item in text_results])
        logger.info(f"📝 Total text extracted: {len(full_text)} characters")
        
        # 初始化数据
        data = {
            "TIME": "",
            "BP": "",
            "VP": "",
            "QB": "",
            "QD": "",
            "PULSE": "",
            "UFR": ""
        }
        
        # 正则表达式模式
        patterns = {
            "TIME": [
                r'(\d{2}:\d{2})',  # HH:MM
                r'(\d{1,2}:\d{2})'
            ],
            "BP": [
                r'BP.*?(\d{2,3}[/\\]\d{2,3})',
                r'(\d{2,3}[/\\]\d{2,3})'  # 血压格式
            ],
            "VP": [
                r'VP.*?(\d{2,3})',
                r'(?:VENOUS|V\.?P\.?).*?(\d{2,3})',
                r'\b(1[0-9]{2}|2[0-4]\d)\b'  # 100-249
            ],
            "QB": [
                r'QB.*?(\d{2,3})',
                r'(?:BLOOD.*?FLOW).*?(\d{2,3})',
                r'\b(2[5-9]\d|3[0-9]\d|400)\b'  # 250-400
            ],
            "QD": [
                r'QD.*?(\d{3,4})',
                r'(?:DIALYSATE).*?(\d{3,4})',
                r'\b([4-6]\d{2})\b'  # 400-699
            ],
            "PULSE": [
                r'(P[-:]?\d{2,3})',  # P-84 or P:84 or P84
                r'PULSE.*?(\d{2,3})',
                r'\b([6-9]\d|1[0-2]\d)\b'  # 60-129
            ],
            "UFR": [
                r'UFR.*?(\d{2,4})',
                r'(?:UF.*?RATE).*?(\d{2,4})',
                r'\b([5-9]\d{2})\b'  # 500-999
            ]
        }
        
        # 提取数据
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # 特殊处理PULSE格式
                    if key == "PULSE" and not value.upper().startswith('P'):
                        value = f"P-{value}"
                    data[key] = value
                    logger.info(f"✓ Extracted {key}: {data[key]}")
                    break
        
        filled_count = sum(1 for v in data.values() if v)
        logger.info(f"✅ Machine screen extraction completed. Found {filled_count}/{len(data)} fields")
        
        return data


# 测试代码
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🧪 DIALYSIS OCR MODULE TEST")
    print("="*70 + "\n")
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_module.py <image_path>")
        print("\n📋 Testing OCR initialization...")
        ocr = DialysisOCR()
        if ocr.reader:
            print("✅ OCR Module is ready!")
            print("\n📚 Supported features:")
            print("   - Nursing Record OCR (护理记录识别)")
            print("   - Machine Screen OCR (透析机屏幕识别)")
            print("\n💡 Tip: Run with image path to test extraction")
            print("   Example: python ocr_module.py your_image.jpg")
        else:
            print("❌ OCR initialization failed")
            print("💡 Please install: pip install easyocr")
        print("\n" + "="*70 + "\n")
    else:
        image_path = sys.argv[1]
        print(f"📷 Testing with image: {image_path}\n")
        
        ocr = DialysisOCR()
        
        if ocr.reader:
            # 测试护理记录
            print("\n📄 NURSING RECORD EXTRACTION")
            print("-"*70)
            nursing_data = ocr.extract_nursing_record(image_path)
            for key, value in nursing_data.items():
                print(f"  {'✓' if value else '✗'} {key:20s}: {value if value else '(not found)'}")
            
            # 测试透析机屏幕
            print("\n📱 MACHINE SCREEN EXTRACTION")
            print("-"*70)
            machine_data = ocr.extract_machine_screen(image_path)
            for key, value in machine_data.items():
                print(f"  {'✓' if value else '✗'} {key:20s}: {value if value else '(not found)'}")
            
            print("\n" + "="*70 + "\n")