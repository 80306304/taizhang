import hashlib
import json
import httpx

CUSTOMER = "0FB91C3323905C9173D142D3883F0A71"
KEY = "ZKTyJoXw2672"
API_URL = "https://poll.kuaidi100.com/poll/query.do"

# state 含义
STATE_MAP = {
    "0": "查询出错",
    "1": "暂无记录",
    "2": "运输中",
    "3": "已签收",
    "4": "问题件",
    "5": "疑难件",
    "6": "退件签收",
}

import re

# 快递公司代码 -> 中文名
COMPANY_NAMES = {
    "jd": "京东快递",
    "shunfeng": "顺丰速运",
    "yuantong": "圆通速递",
    "zhongtong": "中通快递",
    "shentong": "申通快递",
    "ems": "EMS",
    "yunda": "韵达快递",
    "youzhengguonei": "邮政国内小包",
    "jitu": "极兔速递",
    "zhaijisong": "宅急送",
}

# 单号前缀 -> 快递公司代码（长前缀在前，避免短前缀误匹配）
PREFIX_MAP = {
    "YUNDA": "yunda",
    "STO": "shentong",
    "EMS": "ems",
    "ZJS": "zhaijisong",
    "DBL": "debangwuliu",
    "SF": "shunfeng",
    "JD": "jd",
    "JT": "jitu",
    "YT": "yuantong",
    "ZT": "zhongtong",
    "YD": "yunda",
    "YZ": "youzhengguonei",
    "DB": "debangwuliu",
    "HT": "huitongkuaidi",
    "HH": "huitongkuaidi",
    "773": "jitu",
    "JP": "jitu",
    "KK": "kuaijiesudi",
    "UA": "youzhengguonei",
    "99": "youzhengguonei",
}


def detect_company(tracking_no: str) -> str:
    """根据快递单号前缀自动识别快递公司。返回公司代码，识别失败返回空字符串。"""
    no = tracking_no.strip().upper()
    for prefix, company in PREFIX_MAP.items():
        if no.startswith(prefix):
            return company
    return ""


async def query_tracking(company: str, tracking_no: str) -> dict:
    """查询快递状态"""
    param = json.dumps({"com": company, "num": tracking_no}, separators=(",", ":"))
    sign = hashlib.md5((param + KEY + CUSTOMER).encode()).hexdigest().upper()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                API_URL,
                data={"customer": CUSTOMER, "param": param, "sign": sign},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            data = resp.json()
    except Exception as e:
        return {
            "success": False,
            "message": f"网络请求失败: {str(e)}",
            "state": "0",
            "state_text": "查询出错",
            "tracking_no": tracking_no,
            "company": COMPANY_NAMES.get(company, company),
            "company_code": company,
        }

    if data.get("status") != "200":
        return {
            "success": False,
            "message": data.get("message", "查询失败"),
            "state": data.get("state", "0"),
            "state_text": STATE_MAP.get(data.get("state", "0"), "未知"),
            "tracking_no": tracking_no,
            "company": COMPANY_NAMES.get(company, company),
            "company_code": company,
        }

    state = data.get("state", "0")
    latest = data["data"][0] if data.get("data") else None

    return {
        "success": True,
        "company": COMPANY_NAMES.get(company, company),
        "tracking_no": tracking_no,
        "state": state,
        "state_text": STATE_MAP.get(state, "未知"),
        "latest_time": latest["ftime"] if latest else "",
        "latest_context": latest["context"] if latest else "",
        "is_delivered": state == "3",
        "history": [
            {"time": item["ftime"], "context": item["context"]}
            for item in (data.get("data") or [])
        ],
    }


async def batch_query_tracking(records: list[dict]) -> list[dict]:
    """批量查询物流状态。
    records: [{"id": 1, "tracking_no": "SF123...", "tracking_company": ""}, ...]
    自动识别快递公司，返回带 tracking_status 字段的结果列表。
    """
    results = []
    for rec in records:
        no = rec.get("tracking_no", "").strip()
        company = rec.get("tracking_company", "").strip()
        if not no:
            continue
        if not company:
            company = detect_company(no)
        if not company:
            results.append({
                "id": rec["id"],
                "tracking_no": no,
                "tracking_company": "",
                "tracking_status": "无法识别快递公司",
                "is_delivered": False,
                "latest_time": "",
                "latest_context": "",
            })
            continue

        info = await query_tracking(company, no)
        results.append({
            "id": rec["id"],
            "tracking_no": no,
            "tracking_company": company,
            "tracking_status": info.get("state_text", "查询失败") if info.get("success") else info.get("message", "查询失败"),
            "is_delivered": info.get("is_delivered", False),
            "latest_time": info.get("latest_time", ""),
            "latest_context": info.get("latest_context", ""),
        })
    return results
