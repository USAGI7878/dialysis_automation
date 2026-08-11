"""
patient_directory.py
本地的"病人名录"——存一份 姓名 <-> RN(MRN) 对照表，
这样不用每次都死记RN号码，打病人名字前几个字就能搜出来选。

存成本地的 patients.json，跟 config.json 一样属于包含病人信息的敏感文件，
不应该提交到git仓库(已经在.gitignore里加了)。
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

PATIENTS_FILE = "patients.json"


def load_patients():
    """读取病人名录，文件不存在就返回空列表"""
    if not os.path.exists(PATIENTS_FILE):
        return []
    try:
        with open(PATIENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.warning(f"读取{PATIENTS_FILE}失败: {e}")
        return []


def save_patients(patients):
    """保存病人名录，按姓名排序后存盘，方便管理时浏览"""
    try:
        patients_sorted = sorted(patients, key=lambda p: p.get("name", "").upper())
        with open(PATIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(patients_sorted, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存{PATIENTS_FILE}失败: {e}")
        return False


def search_patients(patients, query):
    """按姓名或MRN模糊搜索(大小写不敏感)，query为空就返回全部"""
    q = (query or "").strip().lower()
    if not q:
        return patients
    return [
        p for p in patients
        if q in str(p.get("name", "")).lower() or q in str(p.get("mrn", "")).lower()
    ]


def add_or_update_patient(patients, name, mrn):
    """新增病人，如果姓名已存在(大小写不敏感)就改成更新MRN，避免同一个人存两条"""
    name = name.strip()
    mrn = mrn.strip()
    for p in patients:
        if p.get("name", "").strip().lower() == name.lower():
            p["mrn"] = mrn
            return patients
    patients.append({"name": name, "mrn": mrn})
    return patients


def remove_patient(patients, name):
    """按姓名删除(大小写不敏感)"""
    return [p for p in patients if p.get("name", "").strip().lower() != name.strip().lower()]


def parse_bulk_text(text):
    """
    批量导入用: 把一大段文字(每行 "姓名, RN" 或 "姓名\tRN" 或 "姓名 RN")解析成列表，
    方便一次性把24个/100个病人导进来，不用一个一个手动加。
    """
    import re
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 支持逗号、制表符、多个空格作为分隔符
        parts = re.split(r"[,\t]+|\s{2,}", line)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            name, mrn = parts[0], parts[1]
            results.append({"name": name, "mrn": mrn})
        elif len(parts) == 1:
            # 只有一段内容的话，尝试用最后一个"看起来像数字"的token当MRN，其余当姓名
            tokens = line.split()
            if len(tokens) >= 2 and tokens[-1].isdigit():
                results.append({"name": " ".join(tokens[:-1]), "mrn": tokens[-1]})
    return results
