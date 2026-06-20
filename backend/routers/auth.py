"""认证接口：注册、登录、获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import psycopg

from database import get_db
from auth import (
    hash_password, verify_password, create_token,
    get_current_user, generate_invite_code,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ===== 请求模型 =====
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    invite_code: str = Field(..., min_length=1, max_length=32)


class LoginRequest(BaseModel):
    username: str
    password: str


# ===== 注册 =====
@router.post("/register")
async def register(req: RegisterRequest, db: psycopg.AsyncConnection = Depends(get_db)):
    """用户注册（需注册码）"""
    # 验证注册码
    cursor = await db.execute(
        "SELECT * FROM invite_codes WHERE code = %s AND is_used = 0",
        (req.invite_code,),
    )
    code_row = await cursor.fetchone()
    if not code_row:
        raise HTTPException(status_code=400, detail="注册码无效或已被使用")

    # 检查用户名
    cursor = await db.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if await cursor.fetchone():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    cursor = await db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
        (req.username, hash_password(req.password), "user"),
    )
    row = await cursor.fetchone()
    user_id = row["id"]

    # 标记注册码已使用
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await db.execute(
        "UPDATE invite_codes SET is_used = 1, used_by = %s, used_at = %s WHERE id = %s",
        (user_id, now, code_row["id"]),
    )
    await db.commit()

    return {"message": "注册成功，请登录"}


# ===== 登录 =====
@router.post("/login")
async def login(req: LoginRequest, db: psycopg.AsyncConnection = Depends(get_db)):
    """用户登录"""
    cursor = await db.execute(
        "SELECT * FROM users WHERE username = %s", (req.username,)
    )
    user = await cursor.fetchone()
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    user = dict(user)
    token = create_token(user["id"], user["role"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }


# ===== 获取当前用户 =====
@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {
        "data": {
            "id": current_user["id"],
            "username": current_user["username"],
            "role": current_user["role"],
        }
    }
