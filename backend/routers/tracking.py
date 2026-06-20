from fastapi import APIRouter, Depends
import psycopg
from datetime import datetime

from database import get_db, pool
from auth import get_current_user
from services.kuaidi100 import query_tracking, batch_query_tracking, detect_company, COMPANY_NAMES
from services.scheduler import refresh_schedule

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("/{company}/{tracking_no}")
async def get_tracking(
    company: str, tracking_no: str,
    current_user: dict = Depends(get_current_user),
):
    """查询快递状态"""
    result = await query_tracking(company, tracking_no)
    return {"data": result}


@router.get("/companies")
async def list_companies(current_user: dict = Depends(get_current_user)):
    """获取支持的快递公司列表"""
    return {"data": COMPANY_NAMES}


@router.get("/status/{record_id}")
async def get_tracking_status(
    record_id: int,
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询单条记录的物流详情（实时查快递100）"""
    cursor = await db.execute(
        "SELECT id, tracking_no, tracking_company, user_id FROM records WHERE id = %s",
        (record_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return {"error": "记录不存在"}

    row = dict(row)

    # 权限校验：只能查看自己的记录（admin 除外）
    if current_user["role"] != "admin" and row.get("user_id") != current_user["id"]:
        return {"error": "无权查看他人的物流信息"}

    no = row.get("tracking_no", "").strip()
    if not no:
        return {"error": "该记录没有快递单号", "tracking_no": "", "company": ""}

    company = row.get("tracking_company", "").strip()
    if not company:
        company = detect_company(no)
    if not company:
        return {"error": f"无法识别快递公司（单号：{no}），请手动编辑记录补充快递公司代码", "tracking_no": no, "company": ""}

    result = await query_tracking(company, no)

    # 如果查询失败，附加上查询信息方便排查
    if not result.get("success"):
        result["tracking_no"] = no
        result["company_code"] = company

    # 同时更新缓存
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state = result.get("state", "")
    state_text = result.get("state_text", "查询失败")
    latest_time = result.get("latest_time", "")
    latest_context = result.get("latest_context", "")

    await db.execute(
        """UPDATE records SET
           tracking_state = %s, tracking_state_text = %s,
           tracking_latest_time = %s, tracking_latest_context = %s,
           tracking_updated_at = %s
           WHERE id = %s""",
        (state, state_text, latest_time, latest_context, now, record_id),
    )
    await db.commit()

    return {"data": result}


@router.post("/sync")
async def sync_all_tracking(
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """批量刷新所有有快递单号的记录的物流状态"""
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    if is_admin:
        cursor = await db.execute(
            "SELECT id, tracking_no, tracking_company FROM records WHERE tracking_no != ''"
        )
    else:
        cursor = await db.execute(
            "SELECT id, tracking_no, tracking_company FROM records WHERE tracking_no != '' AND user_id = %s",
            (user_id,),
        )
    rows = await cursor.fetchall()

    if not rows:
        return {"data": {"total": 0, "updated": 0, "message": "没有需要同步的记录"}}

    records = [dict(r) for r in rows]
    results = await batch_query_tracking(records)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated = 0
    for item in results:
        state = ""
        state_text = item.get("tracking_status", "查询失败")
        latest_time = item.get("latest_time", "")
        latest_context = item.get("latest_context", "")

        # 从 STATE_MAP 反查 state code
        if item.get("is_delivered"):
            state = "3"
        elif "运输中" in state_text:
            state = "2"
        elif "暂无记录" in state_text:
            state = "1"
        elif "问题件" in state_text:
            state = "4"
        elif "疑难件" in state_text:
            state = "5"
        elif "退件" in state_text:
            state = "6"

        await db.execute(
            """UPDATE records SET
               tracking_state = %s, tracking_state_text = %s,
               tracking_latest_time = %s, tracking_latest_context = %s,
               tracking_updated_at = %s
               WHERE id = %s""",
            (state, state_text, latest_time, latest_context, now, item["id"]),
        )
        updated += 1

    await db.commit()

    return {
        "data": {
            "total": len(records),
            "updated": updated,
            "message": f"已同步 {updated} 条记录的物流状态",
        }
    }


@router.get("/cron")
async def get_cron(current_user: dict = Depends(get_current_user)):
    """获取定时物流查询的cron表达式"""
    async with pool.connection() as db:
        cursor = await db.execute("SELECT value FROM site_config WHERE key='tracking_cron'")
        row = await cursor.fetchone()
    return {"data": {"cron": dict(row)["value"] if row else "0 */3 * * *"}}


@router.put("/cron")
async def update_cron(body: dict, current_user: dict = Depends(get_current_user)):
    """更新定时物流查询的cron表达式"""
    cron_expr = body.get("cron", "").strip()
    if not cron_expr:
        return {"error": "cron表达式不能为空"}
    parts = cron_expr.split()
    if len(parts) != 5:
        return {"error": "cron表达式必须是5段格式，如 0 */3 * * *"}
    # 存储到数据库
    async with pool.connection() as db:
        await db.execute(
            "INSERT INTO site_config(key,value) VALUES('tracking_cron',%s) "
            "ON CONFLICT(key) DO UPDATE SET value=%s",
            (cron_expr, cron_expr),
        )
        await db.commit()
    # 刷新调度器
    await refresh_schedule(cron_expr)
    return {"data": {"cron": cron_expr, "message": "定时任务已更新"}}
