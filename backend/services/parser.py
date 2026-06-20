import re


def parse_record_text(text: str) -> dict:
    """智能解析自然语言台账记录。

    支持格式:
      "新增 老婆 5070显卡 用户成本 4200 买价 4500 其他收入 20 快递单号 SF123 未回款"
      "老婆 5070显卡 4200 4500"
      "回款 老婆" / "已回款 老婆 5070显卡"
    """
    text = text.strip()
    if not text:
        return {"error": "输入为空"}

    result = {
        "customer": "",
        "product": "",
        "cost_price": 0.0,
        "buy_price": 0.0,
        "other_income": 0.0,
        "tracking_no": "",
        "tracking_company": "",
        "is_returned": 0,
        "created_at": "",
        "note": "",
        "raw_input": text,
    }

    # 提取日期（支持 2025-06-18、2025/06/18、06-18、06/18）
    from datetime import datetime
    m = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        result["created_at"] = f"{y:04d}-{mo:02d}-{d:02d} 00:00:00"
        text = text[:m.start()] + text[m.end():]
    else:
        m = re.search(r"\b(\d{1,2})[-/](\d{1,2})\b", text)
        if m:
            mo, d = int(m.group(1)), int(m.group(2))
            y = datetime.now().year
            result["created_at"] = f"{y:04d}-{mo:02d}-{d:02d} 00:00:00"
            text = text[:m.start()] + text[m.end():]

    # 检测操作类型：回款
    for pat in [r"^回款\b", r"^已回款", r"^标记回款", r"^确认回款"]:
        if re.search(pat, text):
            result["is_returned"] = 1
            text = re.sub(pat, "", text, count=1).strip()
            break

    # 移除操作前缀
    text = re.sub(r"^(新增|添加|记录|新建|录入)\s*", "", text, count=1).strip()

    # 提取快递单号
    m = re.search(r"(?:快递单号|快递|单号|运单)[：:\s]*([A-Za-z]{1,4}\d{10,})", text)
    if not m:
        m = re.search(r"\b((?:SF|JD|YT|ZT|STO|EMS|YD|Yunda)\d{10,})\b", text, re.I)
    if m:
        result["tracking_no"] = m.group(1) if m.lastindex else m.group(0)
        no = result["tracking_no"].upper()
        prefix_map = {
            "SF": "shunfeng", "JD": "jd", "YT": "yuantong", "ZT": "zhongtong",
            "STO": "shentong", "EMS": "ems", "YD": "yunda",
        }
        for prefix, company in prefix_map.items():
            if no.startswith(prefix):
                result["tracking_company"] = company
                break
        # 移除快递相关文本
        text = text[:m.start()] + text[m.end():]

    # 提取其他收入
    m = re.search(r"(?:其他收入|额外|补贴|红包|返利)[：:\s]*(\d+(?:\.\d+)?)", text)
    if m:
        result["other_income"] = float(m.group(1))
        text = text[:m.start()] + text[m.end():]

    # 提取成本价
    m = re.search(r"(?:用户成本|成本|进价|拿价|进货|垫付|垫钱)[：:\s]*(\d+(?:\.\d+)?)", text)
    if m:
        result["cost_price"] = float(m.group(1))
        text = text[:m.start()] + text[m.end():]

    # 提取买价（售价）
    m = re.search(r"(?:买价|售价|卖价|出价|定价|报价)[：:\s]*(\d+(?:\.\d+)?)", text)
    if m:
        result["buy_price"] = float(m.group(1))
        text = text[:m.start()] + text[m.end():]

    # 提取回款状态
    if not result["is_returned"]:
        m = re.search(r"(?:未回款|没回款|待回款|没付)", text)
        if m:
            result["is_returned"] = 0
            text = text[:m.start()] + text[m.end():]
        else:
            m = re.search(r"(?:已回款|已付|回款了|付了|已到账)", text)
            if m:
                result["is_returned"] = 1
                text = text[:m.start()] + text[m.end():]

    # 提取备注
    m = re.search(r"(?:备注|说明|注意)[：:\s]*(.+?)(?:\s(?:快递|成本|买价|售价|$))", text)
    if m:
        result["note"] = m.group(1).strip()
        text = text[:m.start()] + text[m.end():]

    # 如果还没有价格，尝试从剩余文本提取数字
    if result["cost_price"] == 0 and result["buy_price"] == 0:
        numbers = re.findall(r"(\d+(?:\.\d+)?)", text)
        numbers = [float(n) for n in numbers if float(n) > 10]
        if len(numbers) >= 2:
            result["cost_price"] = numbers[0]
            result["buy_price"] = numbers[1]
            for n in [str(int(n)) for n in numbers[:2]]:
                text = text.replace(n, "", 1)
        elif len(numbers) == 1:
            result["cost_price"] = numbers[0]
            text = text.replace(str(int(numbers[0])), "", 1)

    # 清理剩余文本，提取客户和商品
    text = re.sub(r"[，。、；：,;]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    parts = [p for p in text.split(" ") if p.strip()]

    if len(parts) >= 2:
        result["customer"] = parts[0]
        result["product"] = " ".join(parts[1:])
    elif len(parts) == 1:
        result["customer"] = parts[0]

    # 计算利润
    result["profit"] = round(
        result["buy_price"] - result["cost_price"] + result["other_income"], 2
    )

    return result
