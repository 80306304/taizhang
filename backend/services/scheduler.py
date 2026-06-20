"""物流定时查询调度器"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()
_job_id = "auto_sync_tracking"


def validate_tracking_no(no: str) -> bool:
    """校验快递单号格式：至少6位字母数字"""
    if not no or len(no.strip()) < 6:
        return False
    cleaned = no.strip()
    return cleaned.isalnum()


async def auto_sync_job():
    """定时任务：查询所有未签收且有快递单号的记录"""
    from database import pool
    from services.kuaidi100 import batch_query_tracking, detect_company
    from datetime import datetime

    logger.info("[定时物流] 开始执行...")
    if not pool:
        logger.warning("[定时物流] 数据库连接池未就绪，跳过")
        return

    async with pool.connection() as db:
        cursor = await db.execute(
            "SELECT id, tracking_no, tracking_company FROM records "
            "WHERE tracking_no != '' AND (tracking_state IS NULL OR tracking_state != '3')"
        )
        rows = await cursor.fetchall()

    if not rows:
        logger.info("[定时物流] 无需查询的记录")
        return

    # 过滤：先校验格式，再检测公司
    valid_records = []
    skipped = 0
    for row in rows:
        r = dict(row)
        no = r["tracking_no"].strip()
        if not validate_tracking_no(no):
            logger.warning(f"[定时物流] 记录#{r['id']} 单号格式无效: {no}")
            skipped += 1
            continue
        company = r.get("tracking_company", "").strip()
        if not company:
            company = detect_company(no)
        if not company:
            logger.warning(f"[定时物流] 记录#{r['id']} 无法识别快递公司: {no}")
            skipped += 1
            continue
        r["tracking_company"] = company
        valid_records.append(r)

    logger.info(f"[定时物流] 共{len(rows)}条, 有效{len(valid_records)}条, 跳过{skipped}条")

    if not valid_records:
        return

    results = await batch_query_tracking(valid_records)

    async with pool.connection() as db:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in results:
            state = ""
            state_text = item.get("tracking_status", "查询失败")
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
                   tracking_state=%s, tracking_state_text=%s,
                   tracking_latest_time=%s, tracking_latest_context=%s,
                   tracking_updated_at=%s WHERE id=%s""",
                (state, state_text, item.get("latest_time", ""), item.get("latest_context", ""), now, item["id"]),
            )
        await db.commit()

    logger.info(f"[定时物流] 完成，更新{len(results)}条")


def _parse_cron_expr(expr: str) -> dict:
    """解析5段cron表达式，返回CronTrigger参数dict"""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"无效的cron表达式: {expr}")
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


async def refresh_schedule(cron_expr: str = None):
    """根据数据库中的cron表达式重新调度任务"""
    from database import pool

    if cron_expr is None:
        if not pool:
            return
        async with pool.connection() as db:
            cursor = await db.execute(
                "SELECT value FROM site_config WHERE key='tracking_cron'"
            )
            row = await cursor.fetchone()
            cron_expr = dict(row)["value"] if row else "0 */3 * * *"

    try:
        kwargs = _parse_cron_expr(cron_expr)
    except ValueError as e:
        logger.error(f"[调度器] {e}，使用默认 0 */3 * * *")
        kwargs = _parse_cron_expr("0 */3 * * *")

    if scheduler.get_job(_job_id):
        scheduler.remove_job(_job_id)
    scheduler.add_job(
        auto_sync_job,
        CronTrigger(**kwargs),
        id=_job_id,
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info(f"[调度器] 已设置定时物流查询: {cron_expr}")


async def start_scheduler():
    """应用启动时调用，启动调度器"""
    scheduler.start()
    await refresh_schedule()


async def stop_scheduler():
    """应用关闭时调用"""
    scheduler.shutdown(wait=False)
