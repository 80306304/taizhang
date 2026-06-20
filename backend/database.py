import os

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://admin:Admin123456@47.96.254.155:5433/appdb",
)

pool: AsyncConnectionPool | None = None


async def init_pool():
    """启动连接池"""
    global pool
    pool = AsyncConnectionPool(DB_URL, min_size=2, max_size=10)
    await pool.open()
    await _init_db()


async def close_pool():
    """关闭连接池"""
    global pool
    if pool:
        await pool.close()
        pool = None


async def _init_db():
    """建表（幂等）"""
    async with pool.connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS')
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS invite_codes (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                created_by INTEGER NOT NULL,
                used_by INTEGER,
                is_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
                used_at TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id SERIAL PRIMARY KEY,
                customer TEXT NOT NULL DEFAULT '',
                product TEXT NOT NULL DEFAULT '',
                cost_price DOUBLE PRECISION NOT NULL DEFAULT 0,
                buy_price DOUBLE PRECISION NOT NULL DEFAULT 0,
                other_income DOUBLE PRECISION NOT NULL DEFAULT 0,
                profit DOUBLE PRECISION NOT NULL DEFAULT 0,
                tracking_no TEXT NOT NULL DEFAULT '',
                tracking_company TEXT NOT NULL DEFAULT '',
                is_returned INTEGER NOT NULL DEFAULT 0,
                returned_at TEXT,
                note TEXT NOT NULL DEFAULT '',
                raw_input TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
                updated_at TEXT NOT NULL DEFAULT TO_CHAR(NOW(), 'YYYY-MM-DD HH24:MI:SS'),
                tracking_state TEXT NOT NULL DEFAULT '',
                tracking_state_text TEXT NOT NULL DEFAULT '未查询',
                tracking_latest_time TEXT NOT NULL DEFAULT '',
                tracking_latest_context TEXT NOT NULL DEFAULT '',
                tracking_updated_at TEXT,
                estimated_profit DOUBLE PRECISION NOT NULL DEFAULT 0,
                actual_profit DOUBLE PRECISION NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL DEFAULT 0
            )
        """)

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_user_id ON records(user_id)"
        )

        await db.execute("""
            CREATE TABLE IF NOT EXISTS site_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
        """)

        await db.execute("""
            INSERT INTO site_config (key, value) VALUES ('tracking_cron', '0 */3 * * *')
            ON CONFLICT (key) DO NOTHING
        """)

        await db.commit()


async def get_db():
    """FastAPI 依赖：从连接池获取数据库连接，自动设置 dict_row"""
    async with pool.connection() as db:
        db.row_factory = dict_row
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
