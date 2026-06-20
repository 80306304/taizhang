from fastapi import APIRouter, Depends, Query
from typing import Optional
import psycopg

from database import get_db
from auth import get_current_user
from models import RecordCreate, RecordUpdate, ParseRequest
from services.parser import parse_record_text

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("")
async def list_records(
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_returned: Optional[int] = Query(None, description="回款状态筛选"),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取记录列表"""
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    query = "SELECT * FROM records WHERE 1=1"
    params = []

    # 非管理员只能看自己的记录
    if not is_admin:
        query += " AND user_id = %s"
        params.append(user_id)

    if search:
        query += " AND (customer LIKE %s OR product LIKE %s OR tracking_no LIKE %s OR note LIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if is_returned is not None:
        query += " AND is_returned = %s"
        params.append(is_returned)

    if date_from:
        query += " AND created_at >= %s"
        params.append(date_from)

    if date_to:
        query += " AND created_at <= %s"
        params.append(date_to + " 23:59:59")

    query += " ORDER BY created_at DESC"
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return {"data": [dict(row) for row in rows]}


@router.post("")
async def create_record(
    record: RecordCreate,
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建新记录"""
    user_id = current_user["id"]
    profit = record.buy_price - record.cost_price + record.other_income
    cursor = await db.execute(
        """INSERT INTO records
           (customer, product, cost_price, buy_price, other_income, profit,
            actual_profit,
            tracking_no, tracking_company, is_returned, returned_at, note, raw_input, user_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            record.customer,
            record.product,
            record.cost_price,
            record.buy_price,
            record.other_income,
            profit,
            record.actual_profit,
            record.tracking_no,
            record.tracking_company,
            record.is_returned,
            record.returned_at,
            record.note,
            record.raw_input,
            user_id,
        ),
    )
    row = await cursor.fetchone()
    record_id = row["id"]
    await db.commit()

    cursor = await db.execute("SELECT * FROM records WHERE id = %s", (record_id,))
    row = await cursor.fetchone()
    return {"data": dict(row)}


@router.put("/{record_id}")
async def update_record(
    record_id: int,
    record: RecordUpdate,
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新记录"""
    cursor = await db.execute("SELECT * FROM records WHERE id = %s", (record_id,))
    existing = await cursor.fetchone()
    if not existing:
        return {"error": "记录不存在"}

    existing = dict(existing)

    # 权限校验：只能修改自己的记录（admin 除外）
    if current_user["role"] != "admin" and existing.get("user_id") != current_user["id"]:
        return {"error": "无权修改他人的记录"}
    updates = record.model_dump(exclude_unset=True)

    # 如果标记为回款，自动记录回款时间（除非已手动提供）
    auto_returned_at = False
    if "is_returned" in updates and updates["is_returned"] == 1 and not existing["is_returned"]:
        if "returned_at" not in updates or not updates["returned_at"]:
            updates["returned_at"] = "TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')"
            auto_returned_at = True

    # 重新计算利润
    cost = updates.get("cost_price", existing["cost_price"])
    buy = updates.get("buy_price", existing["buy_price"])
    other = updates.get("other_income", existing["other_income"])
    updates["profit"] = buy - cost + other
    updates["updated_at"] = "TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')"

    set_clauses = []
    values = []
    for k, v in updates.items():
        if k == "updated_at" or (k == "returned_at" and auto_returned_at):
            set_clauses.append(f"{k} = {v}")
        else:
            set_clauses.append(f"{k} = %s")
            values.append(v)

    values.append(record_id)
    await db.execute(
        f"UPDATE records SET {', '.join(set_clauses)} WHERE id = %s",
        values,
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM records WHERE id = %s", (record_id,))
    row = await cursor.fetchone()
    return {"data": dict(row)}


@router.delete("/{record_id}")
async def delete_record(
    record_id: int,
    db: psycopg.AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除记录"""
    # 权限校验：只能删除自己的记录（admin 除外）
    if current_user["role"] != "admin":
        cursor = await db.execute("SELECT user_id FROM records WHERE id = %s", (record_id,))
        row = await cursor.fetchone()
        if not row or row.get("user_id") != current_user["id"]:
            return {"error": "无权删除他人的记录"}

    await db.execute("DELETE FROM records WHERE id = %s", (record_id,))
    await db.commit()
    return {"message": "删除成功"}


@router.post("/parse")
async def parse_text(
    req: ParseRequest,
    current_user: dict = Depends(get_current_user),
):
    """智能解析自然语言输入"""
    # Debug: write input to file
    import os
    debug_path = os.path.join(os.path.dirname(__file__), "..", "_debug_input.txt")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(f"INPUT: {repr(req.text)}\n")
        f.write(f"LEN: {len(req.text)}\n")
        f.write(f"CHARS: {[hex(ord(c)) for c in req.text]}\n")
    result = parse_record_text(req.text)
    with open(debug_path, "a", encoding="utf-8") as f:
        f.write(f"PRODUCT: {repr(result.get('product', ''))}\n")
        f.write(f"BUY: {result.get('buy_price', 0)}\n")
    return {"data": result}
