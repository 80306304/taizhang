"""认证与授权工具模块"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import psycopg

from database import get_db

# ===== 配置 =====
SECRET_KEY = "taizhang-ledger-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# ===== 密码哈希 =====
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ===== JWT =====
def create_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ===== FastAPI 依赖 =====
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: psycopg.AsyncConnection = Depends(get_db),
) -> dict:
    """从 Bearer token 解析当前用户，返回 user dict"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    cursor = await db.execute("SELECT * FROM users WHERE id = %s", (int(user_id),))
    user = await cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return dict(user)


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """要求当前用户为 admin 角色"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")
    return current_user


def generate_invite_code() -> str:
    """生成 16 位大写随机注册码"""
    return uuid.uuid4().hex[:16].upper()


# ===== 启动时自动创建默认管理员 =====
async def ensure_admin(db: psycopg.AsyncConnection):
    """若无 admin 用户则自动创建 admin/admin123"""
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'admin'")
    row = await cursor.fetchone()
    if row["cnt"] == 0:
        await db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            ("admin", hash_password("admin123"), "admin"),
        )
        await db.commit()
