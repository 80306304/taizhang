from fastapi import APIRouter, Depends, Query
from typing import Optional
import psycopg

from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取统计数据"""
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    where = " WHERE 1=1"
    params = []

    # 非管理员只统计自己的记录
    if not is_admin:
        where += " AND user_id = %s"
        params.append(user_id)

    if date_from:
        where += " AND created_at >= %s"
        params.append(date_from)
    if date_to:
        where += " AND created_at <= %s"
        params.append(date_to + " 23:59:59")

    cursor = await db.execute(f"SELECT COUNT(*) as cnt FROM records{where}", params)
    row = await cursor.fetchone()
    total_orders = row["cnt"]

    cursor = await db.execute(f"SELECT COALESCE(SUM(cost_price), 0) as v FROM records{where}", params)
    row = await cursor.fetchone()
    total_cost = row["v"]

    cursor = await db.execute(f"SELECT COALESCE(SUM(profit), 0) as v FROM records{where}", params)
    row = await cursor.fetchone()
    total_profit = row["v"]

    cursor = await db.execute(f"SELECT COALESCE(SUM(buy_price), 0) as v FROM records{where}", params)
    row = await cursor.fetchone()
    total_buy_price = row["v"]

    cursor = await db.execute(f"SELECT COALESCE(SUM(actual_profit), 0) as v FROM records{where}", params)
    row = await cursor.fetchone()
    total_actual = row["v"]

    cursor = await db.execute(
        f"SELECT COUNT(*) as cnt FROM records{where} AND is_returned = 1", params
    )
    row = await cursor.fetchone()
    returned_count = row["cnt"]

    cursor = await db.execute(
        f"SELECT COUNT(*) as cnt FROM records{where} AND is_returned = 0", params
    )
    row = await cursor.fetchone()
    unreturned_count = row["cnt"]

    cursor = await db.execute(
        f"SELECT COUNT(*) as cnt FROM records{where} AND tracking_state = '2'", params
    )
    row = await cursor.fetchone()
    shipping_count = row["cnt"]

    cursor = await db.execute(
        f"SELECT COUNT(*) as cnt FROM records{where} AND tracking_state = '3'", params
    )
    row = await cursor.fetchone()
    delivered_count = row["cnt"]

    return_rate = (returned_count / total_orders * 100) if total_orders > 0 else 0

    return {
        "data": {
            "total_orders": total_orders,
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "total_actual_profit": round(total_actual, 2),
            "total_buy_price": round(total_buy_price, 2),
            "returned_count": returned_count,
            "unreturned_count": unreturned_count,
            "return_rate": round(return_rate, 1),
            "shipping_count": shipping_count,
            "delivered_count": delivered_count,
        }
    }
