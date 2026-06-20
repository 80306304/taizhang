"""管理接口：用户管理、注册码管理（仅 admin）"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg

from database import get_db
from auth import get_current_admin, generate_invite_code

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ===== 用户管理 =====
@router.get("/users")
async def list_users(
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """列出所有用户"""
    cursor = await db.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY id"
    )
    rows = await cursor.fetchall()
    return {"data": [dict(r) for r in rows]}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """删除用户（不能删自己）"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    await db.execute("DELETE FROM users WHERE id = %s", (user_id,))
    await db.commit()
    return {"message": "用户已删除"}


class RoleUpdate(BaseModel):
    role: str


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    body: RoleUpdate,
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """修改用户角色"""
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="角色必须是 user 或 admin")
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    await db.execute("UPDATE users SET role = %s WHERE id = %s", (body.role, user_id))
    await db.commit()
    return {"message": "角色已更新"}


# ===== 注册码管理 =====
@router.get("/invite-codes")
async def list_invite_codes(
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """列出所有注册码"""
    cursor = await db.execute(
        """SELECT ic.*, u1.username AS creator_name, u2.username AS used_by_name
           FROM invite_codes ic
           LEFT JOIN users u1 ON ic.created_by = u1.id
           LEFT JOIN users u2 ON ic.used_by = u2.id
           ORDER BY ic.id DESC"""
    )
    rows = await cursor.fetchall()
    return {"data": [dict(r) for r in rows]}


@router.post("/invite-codes")
async def create_invite_code(
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """生成新注册码"""
    code = generate_invite_code()
    cursor = await db.execute(
        "INSERT INTO invite_codes (code, created_by) VALUES (%s, %s) RETURNING id",
        (code, admin["id"]),
    )
    row = await cursor.fetchone()
    await db.commit()
    return {"data": {"id": row["id"], "code": code}}


@router.delete("/invite-codes/{code_id}")
async def delete_invite_code(
    code_id: int,
    admin: dict = Depends(get_current_admin),
    db: psycopg.AsyncConnection = Depends(get_db),
):
    """删除注册码"""
    await db.execute("DELETE FROM invite_codes WHERE id = %s", (code_id,))
    await db.commit()
    return {"message": "注册码已删除"}
