"""
ai_ocr_module.py
用AI视觉模型(目前用Google Gemini)识别护理记录纸——尤其是手写数据。
Tesseract这类传统OCR引擎对手写字识别率很差，这个模块改用多模态大模型
直接"看图"提取结构化数据，准确率明显更高。

护理记录纸的真实结构(已用实际照片确认过):
1. 表头区块 —— 病人相对固定的信息，很少变化:
   RN(病历号)/DIALYZER/HEPARIN/VASCULAR ACCESS(左右两格)/HEIGHT/DRY WEIGHT/
   CONSTRUCTION(日期)/INSERTION(日期)/ALLERGY/EPO/IV IRON/NOTE/QB/QD
2. 下方是"一周7天"的表格，每一天占一列(日期做表头)，
   每行是 NUMBER OF HD / HRS OF HD / PRE BP / POST BP / PRE PULSE / POST PULSE /
   TEMPERATURE / PRE WEIGHT / IDWG / POST WEIGHT / UF / KT/V / WEIGHT LOSS / REMARKS，
   护士每次透析后手写填一列。不是每一列都有数据——只有已经做过透析的那几天会填。

使用前需要:
1. pip install google-genai
2. 准备一个Gemini API Key (https://aistudio.google.com/apikey 免费申请)
   免费额度有限制(如15次/分钟)，且Google免费层的条款允许用你的输入做模型训练/人工审核，
   如果照片里有真实病人隐私信息(姓名/IC/病历号等)，请自行评估这一点是否符合你们的
   数据保护规范(PDPA/院内规定)，必要时先遮盖/裁掉敏感信息再测试，或改用付费层。
"""

import os
import json
import re
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# 本次程序运行以来，所有Gemini调用累计的用量统计。
# Session-wide cumulative Gemini usage tracker.
#
# 重要: Gemini API本身没有"查询账号还剩多少额度/token"这个接口——
# 免费层/付费层的额度是Google后台按你的API Key/项目算的，只能去
# https://aistudio.google.com/apikey 或 Google Cloud Console 网页上看。
# 这里能做的，是把每次调用返回的 usage_metadata(这一次实际用了多少token)
# 累加起来，给一个"本次会话已经用了多少"的参考指标，方便你自己对照
# 后台额度心里有数，不是真正的"剩余额度"。
# ===================================================================
_SESSION_USAGE = {
    "call_count": 0,
    "prompt_tokens": 0,
    "candidates_tokens": 0,
    "total_tokens": 0,
    "last_error": "",
}


def get_session_usage():
    """返回目前为止累计的用量统计(dict的拷贝，调用方随便改不会影响内部状态)"""
    return dict(_SESSION_USAGE)


def reset_session_usage():
    """清零累计计数，比如护理师想单独看某一段时间内的用量"""
    _SESSION_USAGE.update(
        call_count=0, prompt_tokens=0, candidates_tokens=0, total_tokens=0, last_error=""
    )

# 护理记录纸表头字段 -> main.py里UI字段的key(注意跟Origin表单字段的映射规则保持一致:
# main.py的key用下划线连接、大写，对应Origin表单里label的文字，比如 IV_IRON -> "IV IRON")
HEADER_FIELD_KEYS = [
    "HEIGHT", "WEIGHT", "DIALYZER", "VASCULAR_ACCESS", "QD", "QB",
    "CONSTRUCTION", "INSERTION", "EPO", "IV_IRON", "HEPARIN", "ALLERGY", "NOTE",
]

# 每日数据(周表格每一列)的字段
DAILY_FIELD_KEYS = [
    "DATE", "NUMBER_OF_HD", "HRS_OF_HD", "PRE_BP", "POST_BP", "PRE_PULSE",
    "POST_PULSE", "TEMPERATURE", "PRE_WEIGHT", "IDWG", "POST_WEIGHT",
    "UF", "KT_V", "WEIGHT_LOSS", "REMARKS",
]

EXTRACTION_PROMPT = """你正在识别一张医院透析护理记录纸(Kek Lok Si Charitable Hospital的HD护理记录)的照片，
这张纸上有手写字，请仔细辨认，尤其注意容易混淆的数字(比如1和7、0和6、5和8、3和9)。

这张纸的结构固定分两部分：

【表头区块】(病人固定信息，通常是印刷体或护士早期填的，字迹相对工整):
- RN (病历号/MRN)
- DIALYZER (透析器型号)
- HEPARIN (肝素用量)
- VASCULAR ACCESS (血管通路，可能分左右两格，比如 "LT BCF" 和 "RT CUFF")
- HEIGHT (身高)
- DRY WEIGHT (干体重)
- CONSTRUCTION (建立日期)
- INSERTION (置入日期)
- ALLERGY (过敏史)
- EPO (促红细胞生成素)
- IV IRON (静脉铁剂)
- NOTE (备注，可能包含 Na/T 等化验数值)
- QB (血流速)
- QD (透析液流速)

【周表格区块】(下方7天一排的表格，每列一个日期，是护士每次透析后手写填入的):
表格的列标题是日期(比如 "2/7/2026")，每一列往下的行依次是:
NUMBER OF HD / HRS OF HD / PRE BP / POST BP / PRE PULSE / POST PULSE /
TEMPERATURE °C / PRE WEIGHT / IDWG / POST WEIGHT / UF / KT/V / WEIGHT LOSS / REMARKS

注意：不是每一列都有手写数据，只有"已经做过透析"的那几天才会被填。
【只把有手写数据的日期列包含进结果里，完全空白的日期列直接跳过，不要猜测或编造数值】。
如果某一列里个别格子空着(比如某天没量PRE PULSE)，那个字段就留空字符串，不要编。
如果某个数字实在认不清、有涂改看不出最终结果，用你最大把握的读法，
并在这个字段值的最后加上 "?" 标记不确定(比如 "160/64?")，方便人工核对。

请严格按下面的JSON格式输出，不要输出任何JSON以外的文字、不要用markdown代码块包裹：

{
  "header": {
    "HEIGHT": "",
    "WEIGHT": "",
    "DIALYZER": "",
    "VASCULAR_ACCESS": "",
    "QD": "",
    "QB": "",
    "CONSTRUCTION": "",
    "INSERTION": "",
    "EPO": "",
    "IV_IRON": "",
    "HEPARIN": "",
    "ALLERGY": "",
    "NOTE": ""
  },
  "daily_columns": [
    {
      "DATE": "",
      "NUMBER_OF_HD": "",
      "HRS_OF_HD": "",
      "PRE_BP": "",
      "POST_BP": "",
      "PRE_PULSE": "",
      "POST_PULSE": "",
      "TEMPERATURE": "",
      "PRE_WEIGHT": "",
      "IDWG": "",
      "POST_WEIGHT": "",
      "UF": "",
      "KT_V": "",
      "WEIGHT_LOSS": "",
      "REMARKS": ""
    }
  ]
}
"""


class _GeminiOCRBase:
    """
    Gemini OCR 的公共基类，处理API key/型号的加载逻辑，
    GeminiNursingOCR(护理记录) 和 GeminiMachineOCR(透析机屏幕) 都基于它。
    """

    def __init__(self, api_key=None, api_keys=None, model=None):
        """
        api_key / api_keys: 不传的话会依次尝试:
            1. 环境变量 GEMINI_API_KEY
            2. config.json 里的 "gemini_api_key" 字段
        另外，config.json 里如果配了 "gemini_api_keys"(一个数组)，这些会作为
        【备用Key】自动合并进来——遇到限流/额度用完时，会自动按顺序换下一把Key
        重试，不用你手动切换。比如:
            {
              "gemini_api_key": "主要用这把",
              "gemini_api_keys": ["备用key1", "备用key2"]
            }
        (不同Google账号各申请一把免费Key就能凑出好几把，Gemini免费额度本身
        是长期有效的，不是一次性试用，所以这样"轮流用"是完全免费的备用方案)

        model: 不传的话默认用 "gemini-flash-latest" 这个别名——
               Google会让它自动指向当前最新的Flash模型，不用因为Google下架旧型号
               就要跟着改代码。也可以在config.json里加 "gemini_model": "型号名"
               手动指定(比如账号开通付费层后想用 "gemini-2.5-pro" 效果更好)。
        """
        try:
            from google import genai
        except ImportError as e:
            raise ImportError(
                "缺少 google-genai 这个包。请先运行: pip install google-genai"
            ) from e

        primary_keys = []
        if api_keys:
            primary_keys.extend([str(k).strip() for k in api_keys if str(k).strip()])
        if api_key:
            primary_keys.append(str(api_key).strip())
        if not primary_keys:
            env_key = os.environ.get("GEMINI_API_KEY")
            if env_key:
                primary_keys.append(env_key)
        if not primary_keys:
            cfg_key = self._load_api_key_from_config()
            if cfg_key:
                primary_keys.append(cfg_key)

        # 合并config.json里的备用Key(去重，主Key排最前面优先用)
        backup_keys = self._load_backup_keys_from_config()
        all_keys = []
        for k in primary_keys + backup_keys:
            if k and k not in all_keys:
                all_keys.append(k)

        if not all_keys:
            raise ValueError(
                "没有找到 Gemini API Key。请用以下任一方式提供:\n"
                f"1. 创建 {type(self).__name__}(api_key='你的key')\n"
                "2. 设置环境变量 GEMINI_API_KEY\n"
                "3. 在 config.json 里加一行 \"gemini_api_key\": \"你的key\"\n"
                "免费申请: https://aistudio.google.com/apikey"
            )

        self._genai = genai
        self._api_keys = all_keys
        self._key_index = 0
        self._build_client(self._api_keys[0])

        if model is None:
            model = self._load_model_from_config() or "gemini-flash-latest"
        self.model = model
        logger.info(
            f"{type(self).__name__} using model: {self.model} "
            f"({len(self._api_keys)} 把Gemini Key可用，限流时会自动轮换)"
        )

    def _build_client(self, key):
        self.client = self._genai.Client(api_key=key)

    def _rotate_to_next_key(self):
        """切到下一把Key(遇到限流时用)，按顺序循环"""
        self._key_index = (self._key_index + 1) % len(self._api_keys)
        self._build_client(self._api_keys[self._key_index])

    @staticmethod
    def _load_model_from_config(config_path="config.json"):
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                return cfg.get("gemini_model")
        except Exception as e:
            logger.warning(f"读取config.json里的gemini_model失败: {e}")
        return None

    @staticmethod
    def _load_api_key_from_config(config_path="config.json"):
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                return cfg.get("gemini_api_key")
        except Exception as e:
            logger.warning(f"读取config.json里的gemini_api_key失败: {e}")
        return None

    @staticmethod
    def _load_backup_keys_from_config(config_path="config.json"):
        """读取config.json里的 "gemini_api_keys" 数组(备用Key，限流时轮换用)"""
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                keys = cfg.get("gemini_api_keys", [])
                if isinstance(keys, list):
                    return [str(k).strip() for k in keys if str(k).strip()]
        except Exception as e:
            logger.warning(f"读取config.json里的gemini_api_keys失败: {e}")
        return []

    def _call_gemini(self, prompt, image_path):
        """给一张图+文字prompt，调Gemini拿返回文字。型号失效时给出清楚的中文提示。
        遇到限流/额度用完时，如果还有别的Key没试过，会自动换下一把重试。"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        contents = [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": image_bytes}},
                ],
            }
        ]

        total_keys = len(self._api_keys)
        keys_tried = 0

        while True:
            logger.info(
                f"📤 Sending image to Gemini ({self.model}, key #{self._key_index + 1}/{total_keys})..."
            )
            try:
                response = self.client.models.generate_content(model=self.model, contents=contents)
                break
            except Exception as e:
                err_str = str(e)

                if "NOT_FOUND" in err_str or "404" in err_str:
                    raise RuntimeError(
                        f"模型 '{self.model}' 目前不可用(可能被Google下架了)。\n"
                        f"可以在 config.json 里加一行 \"gemini_model\": \"gemini-2.5-flash-lite\" "
                        f"(或去 https://ai.google.dev/gemini-api/docs/models 看当前有效的型号名)"
                        f" 手动指定一个可用的型号。\n\n原始错误: {err_str}"
                    ) from e

                # 限流/额度用完: 免费层通常是"每分钟请求数"限制(比如15次/分钟)，
                # 也可能是每天的调用次数上限。这是最常见的"识别了几张照片就突然不动了"的原因，
                # 跟"token真的用完"是两回事，通常等一下(免费层一般是按分钟重置)就能继续用。
                is_rate_limited = (
                    "RESOURCE_EXHAUSTED" in err_str or "429" in err_str
                    or "quota" in err_str.lower() or "rate" in err_str.lower()
                )
                if is_rate_limited:
                    keys_tried += 1
                    if keys_tried < total_keys:
                        # 还有别的Key没试过，自动换下一把重试，不用等、也不用人工干预
                        logger.warning(
                            f"⚠️  Key #{self._key_index + 1} 限流/超额了，"
                            f"自动换下一把Key重试({keys_tried}/{total_keys} 把已试过)..."
                        )
                        self._rotate_to_next_key()
                        continue

                    key_note = (
                        f"已经把你配置的全部 {total_keys} 把Gemini Key都轮流试过了，全部都限流/超额。\n"
                        if total_keys > 1 else
                        "只配置了1把Gemini Key。可以在config.json里加一个\"gemini_api_keys\"数组，"
                        "多放几把免费Key进去，限流时会自动轮换重试，不用等。\n"
                    )
                    _SESSION_USAGE["last_error"] = "限流/额度已达上限 Rate limit / quota exceeded"
                    raise RuntimeError(
                        "触发了Gemini的限流或额度上限(常见于免费层的\"每分钟请求数\"限制，"
                        "也可能是每天的调用次数上限)。\n"
                        + key_note +
                        "这通常不是\"token真的用完了\"，等一下(免费层一般按分钟重置)再试通常就能继续。\n"
                        "如果经常发生，可以去 https://aistudio.google.com/apikey 查看目前的额度，"
                        "或考虑升级到付费层。\n\n"
                        "Hit a Gemini rate limit or quota cap (commonly the free tier's per-minute "
                        "request limit, or a daily call limit).\n"
                        "This usually isn't the same as running out of tokens — waiting a bit "
                        "(free tier limits typically reset per minute) and retrying usually works.\n"
                        "Check your current quota at https://aistudio.google.com/apikey, or consider "
                        "upgrading to a paid tier if this happens often.\n\n"
                        f"原始错误 Original error: {err_str}"
                    ) from e

                raise

        # 记录这一次调用实际用了多少token，累加进本次会话的用量统计
        # (用来在界面上显示一个"本次会话已用量"的参考指标)
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            prompt_tok = getattr(usage, "prompt_token_count", 0) or 0
            candidates_tok = getattr(usage, "candidates_token_count", 0) or 0
            total_tok = getattr(usage, "total_token_count", 0) or (prompt_tok + candidates_tok)

            _SESSION_USAGE["call_count"] += 1
            _SESSION_USAGE["prompt_tokens"] += prompt_tok
            _SESSION_USAGE["candidates_tokens"] += candidates_tok
            _SESSION_USAGE["total_tokens"] += total_tok

            logger.info(
                f"📊 Token usage — this call: {total_tok} (prompt {prompt_tok} + output {candidates_tok}); "
                f"session total: {_SESSION_USAGE['total_tokens']} across {_SESSION_USAGE['call_count']} call(s)"
            )

        return response.text or ""

    @staticmethod
    def _parse_json_response(raw_text):
        """
        Gemini有时会在JSON外面包一层```json ... ```代码块，这里做个兜底清理再解析。
        """
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"```\s*$", "", text)
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 兜底: 尝试抠出第一个 { ... } 区块再解析一次
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"无法解析Gemini返回的内容为JSON: {text[:300]}")


class GeminiNursingOCR(_GeminiOCRBase):
    """
    用Gemini视觉模型识别护理记录纸(尤其是手写的每日数据周表)。
    """

    def extract_nursing_record(self, image_path):
        """
        识别护理记录纸照片，返回:
        {
            "header": {...},           # 表头固定信息
            "daily_columns": [...]     # 有数据的日期列列表(按护理记录纸上从左到右顺序)
        }
        """
        raw_text = self._call_gemini(EXTRACTION_PROMPT, image_path)
        result = self._parse_json_response(raw_text)

        header = result.get("header", {}) or {}
        daily_columns = result.get("daily_columns", []) or []

        # 补全缺的key，保证返回结构稳定(main.py按key去basic_fields里找，缺key不会报错，
        # 但补上空字符串更保险，也方便调用方直接遍历所有已知字段)
        header = {k: str(header.get(k, "") or "").strip() for k in HEADER_FIELD_KEYS}
        cleaned_columns = []
        for col in daily_columns:
            if not isinstance(col, dict):
                continue
            cleaned_columns.append(
                {k: str(col.get(k, "") or "").strip() for k in DAILY_FIELD_KEYS}
            )

        logger.info(
            f"✓ Gemini extraction done: {sum(1 for v in header.values() if v)} header "
            f"field(s), {len(cleaned_columns)} daily column(s) with data"
        )

        return {"header": header, "daily_columns": cleaned_columns}


# 透析机屏幕(每小时观察)的字段——跟 origin_automation.py / main.py 的
# add_hourly_observation() 用的key保持一致
MACHINE_FIELD_KEYS = ["TIME", "BP", "VP", "QB", "QD", "PULSE", "UFR"]

# 透析机屏幕(每小时观察)的字段——跟 origin_automation.py / main.py 的
# add_hourly_observation() 用的key保持一致
MACHINE_FIELD_KEYS = ["TIME", "BP", "VP", "QB", "QD", "PULSE", "UFR"]

# VP/QB/QD/UFR这几个是透析开始时设定好、整个疗程基本不变的机器参数
# (不是每次量血压都会变的东西)，所以只在屏幕上读一次"当前设置"，
# 而不是让AI每一行分别猜——这样能保证所有行的这几个值完全一致，
# 不会出现"某几行有值、某几行没值/不一样"这种不合理的情况。
MACHINE_SETTING_KEYS = ["VP", "QB", "QD", "UFR"]

MACHINE_EXTRACTION_PROMPT = """你正在识别一张血液透析机屏幕的照片(Fresenius或类似品牌的透析机显示屏)。

这张屏幕上有两类信息，请分开读取：

【1. 血压历史记录表格 "Blood pressure history"】
这个表格列出了这次治疗过程中【每一次测量】的记录，每一行是一个时间点。
请把这个历史表格里【所有能看到的行】都读出来，每一行读一次
(不要只读最新/最下面那一行，也不要漏掉表格顶部或中间被截断的行)，
每一行只需要读这3个值:
- TIME: 那一行的时间(格式 HH:MM，24小时制)
- BP: 那一行的血压(格式 收缩压/舒张压，比如 179/63。如果分开显示SYS和DIA两个数字，
  拼成"SYS/DIA"这个格式)
- PULSE: 那一行的脉搏(纯数字的话在前面加上"P-"，输出格式统一成"P-数字"，比如"P-64")

【2. 当前机器设置(整个疗程通常是固定的，只需要读屏幕上"当前"显示的这一份，不用逐行读)】
- VP: 静脉压 Venous Pressure(通常显示为VP，纯数字)
- QB: 血流速 Blood Flow Rate(通常显示为QB或"Blood Flow"，纯数字，常见范围200-350)
- QD: 透析液流速 Dialysate Flow(通常显示为QD或"Dialysate"，纯数字，常见值500)
- UFR: 超滤率 UF Rate(通常显示为UFR或"UF Rate"，纯数字)

如果某个字段确实找不到，就留空字符串，不要编造数值。
如果数字模糊看不太清，用你最大把握的读法。

请严格按下面的JSON格式输出，不要输出任何JSON以外的文字、不要用markdown代码块包裹：

{
  "bp_history": [
    {"TIME": "", "BP": "", "PULSE": ""}
  ],
  "current_settings": {
    "VP": "",
    "QB": "",
    "QD": "",
    "UFR": ""
  }
}
"""


class GeminiMachineOCR(_GeminiOCRBase):
    """
    用Gemini视觉模型识别透析机屏幕——读出"血压历史记录"表格里所有时间点的TIME/BP/PULSE，
    再把"当前机器设置"(VP/QB/QD/UFR，整个疗程固定不变)统一套用到每一个时间点上。
    """

    def extract_machine_screen(self, image_path):
        """
        识别透析机屏幕照片，返回一个列表，每一项是一个dict:
        [{"TIME": "...", "BP": "...", "VP": "...", "QB": "...", "QD": "...", "PULSE": "...", "UFR": "..."}, ...]
        按屏幕历史表格从上到下的顺序排列。VP/QB/QD/UFR在所有行里都是同一份"当前设置"的值。
        """
        raw_text = self._call_gemini(MACHINE_EXTRACTION_PROMPT, image_path)
        result = self._parse_json_response(raw_text)

        bp_history = result.get("bp_history", [])
        if not isinstance(bp_history, list):
            bp_history = []

        current_settings = result.get("current_settings", {}) or {}
        settings = {k: str(current_settings.get(k, "") or "").strip() for k in MACHINE_SETTING_KEYS}

        # QD在实际使用中几乎永远是500这个固定值，AI如果没能从屏幕上读到，
        # 用500兜底，而不是留空白让人再手动填
        if not settings.get("QD"):
            settings["QD"] = "500"
            logger.info("ℹ️  AI没有识别到QD，使用默认值500")

        logger.info(f"✓ 当前机器设置(应用到所有行): {settings}")

        cleaned = []
        for row in bp_history:
            if not isinstance(row, dict):
                continue
            entry = {
                "TIME": str(row.get("TIME", "") or "").strip(),
                "BP": str(row.get("BP", "") or "").strip(),
                "PULSE": str(row.get("PULSE", "") or "").strip(),
            }
            entry.update(settings)  # VP/QB/QD/UFR每一行都用同一份设置
            if entry["TIME"] or entry["BP"]:  # TIME和BP都空的行没有意义，跳过
                cleaned.append({k: entry.get(k, "") for k in MACHINE_FIELD_KEYS})

        logger.info(f"✓ Gemini machine screen extraction done: {len(cleaned)} reading(s) found")

        return cleaned



def pick_target_column(daily_columns, target_date=None):
    """
    从识别出的多个日期列里选出要用的那一列。
    target_date: 字符串，比如 "7/7/2026"，不传的话默认取【最后一个】有数据的列
                 (护理记录纸从左到右按时间顺序排列，最后一列通常就是最新一次)。
    """
    if not daily_columns:
        return None
    if target_date:
        target_date_norm = target_date.strip().replace("-", "/")
        for col in daily_columns:
            if col.get("DATE", "").strip().replace("-", "/") == target_date_norm:
                return col
        logger.warning(f"⚠️  没找到日期为 {target_date} 的列，改用最后一列")
    return daily_columns[-1]