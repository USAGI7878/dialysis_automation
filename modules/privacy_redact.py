"""
privacy_redact.py
在把护理记录照片发给云端AI(Gemini等)之前，先用本地的Tesseract(离线、免费、不联网)
找到"NAME / IC / RN"这类敏感标签的位置，自动打码盖住对应的值，
这样病人姓名、身份证号这些信息永远不会真正离开这台电脑。

用法:
    from modules.privacy_redact import redact_sensitive_fields
    redacted_path = redact_sensitive_fields("nursing_record.jpg")
    # 之后把 redacted_path 这张打码后的图发给Gemini，而不是原图
"""

import os
import logging
from difflib import SequenceMatcher

import pytesseract
from PIL import Image, ImageDraw

from modules.ocr_module import find_tesseract_executable

# 模块加载时就自动检测并设置一次Tesseract路径(config.json/PATH/常见安装路径)，
# 跟ocr_module.py的DialysisOCR用的是同一套检测逻辑，保持一致
_tess_path = find_tesseract_executable()
if _tess_path:
    pytesseract.pytesseract.tesseract_cmd = _tess_path

logger = logging.getLogger(__name__)

# 要打码的标签(这份护理记录纸实际只有NAME和RN两个需要保护的字段，没有IC，
# 之前把IC也列进去、又用了"1C/IG/1G/LC"这种宽松的模糊匹配，
# 结果在表格中间的手写数字区域误判triggering，把不相关的格子也打了码——
# 所以这里去掉IC，只留真正存在且需要保护的NAME/RN)
DEFAULT_LABELS = {
    "NAME": ["NAME"],
    "RN": ["RN", "R.N", "RN.", "RIN"],
}

# 判断"下一列"边界时，用来识别列头的关键词(遇到这些词就代表敏感值列已经结束)
NEXT_COLUMN_ANCHORS = [
    "DRY", "WEIGHT", "DIALYZER", "HEPARIN", "VASCULAR", "ACCESS",
    "CONSTRUCTION", "INSERTION", "EPO", "IRON", "NOTE", "QB", "QD",
]

DEFAULT_REDACT_WIDTH_RATIO = 0.22  # 找不到下一列边界时，兜底遮盖宽度=图片宽度的22%


def _fuzzy_label_match(token, variants, min_ratio=0.75):
    token_clean = token.strip().upper().rstrip(":.")
    if not token_clean:
        return False
    for v in variants:
        if token_clean == v:
            return True
        if SequenceMatcher(None, token_clean, v).ratio() >= min_ratio:
            return True
    return False


def redact_sensitive_fields(
    image_path,
    labels=None,
    output_path=None,
    row_margin=12,
    fill_color=(0, 0, 0),
):
    """
    在image_path这张图上，找到labels指定的标签(默认NAME/IC/RN)，
    把标签右侧对应的值区域用黑色矩形打码，保存成新图片，返回新图片路径。

    labels: dict，形如 {"NAME": ["NAME"], ...}；不传就用DEFAULT_LABELS
    output_path: 不传的话会存成 原文件名_redacted.原后缀
    row_margin: 打码矩形上下各多留几像素，避免文字没盖全
    """
    if labels is None:
        labels = DEFAULT_LABELS

    img = Image.open(image_path).convert("RGB")
    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n = len(data["text"])

    # 先收集所有识别到的词，方便后面找"下一列"边界
    words = []
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        words.append({
            "text": text.upper().rstrip(":."),
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
        })

    redacted_count = 0

    for label_name, variants in labels.items():
        for w in words:
            if not _fuzzy_label_match(w["text"], variants):
                continue

            label_right = w["left"] + w["width"]
            row_top = w["top"] - row_margin
            row_bottom = w["top"] + w["height"] + row_margin

            # 找同一行、在这个标签右边的"下一列"锚点词，作为打码矩形的右边界
            right_boundary = None
            for other in words:
                if other is w:
                    continue
                # 同一行的判定: top大致重叠
                if not (row_top <= other["top"] <= row_bottom):
                    continue
                if other["left"] <= label_right:
                    continue
                if other["text"] in NEXT_COLUMN_ANCHORS:
                    if right_boundary is None or other["left"] < right_boundary:
                        right_boundary = other["left"]

            if right_boundary is None:
                right_boundary = min(
                    label_right + int(img_width * DEFAULT_REDACT_WIDTH_RATIO),
                    img_width,
                )
            else:
                right_boundary = max(right_boundary - 5, label_right + 10)

            rect = [label_right, row_top, right_boundary, row_bottom]
            draw.rectangle(rect, fill=fill_color)
            redacted_count += 1
            logger.info(f"🔒 Redacted '{label_name}' field at {rect}")

    if redacted_count == 0:
        logger.warning(
            "⚠️  No sensitive labels (NAME/IC/RN) were found to redact. "
            "The image will be sent WITHOUT redaction — please check manually "
            "if this photo actually contains patient identifiers."
        )

    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_redacted{ext}"

    img.save(output_path)
    logger.info(f"✓ Redacted image saved to {output_path} ({redacted_count} field(s) redacted)")

    return output_path, redacted_count