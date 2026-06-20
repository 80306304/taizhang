import sys
import asyncio

# Windows 下 psycopg async 需要 SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware

from database import init_pool, close_pool, get_db
from auth import ensure_admin
from routers import records, stats, tracking, auth, admin
from services.scheduler import start_scheduler, stop_scheduler

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


class CacheControlMiddleware(BaseHTTPMiddleware):
    """API 接口禁止浏览器缓存，防止切换账号后看到旧数据"""
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app):
    await init_pool()
    async for db in get_db():
        await ensure_admin(db)
    await start_scheduler()
    yield
    await stop_scheduler()
    await close_pool()


app = FastAPI(title="台账管理系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CacheControlMiddleware)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(records.router)
app.include_router(stats.router)
app.include_router(tracking.router)


# 挂载前端静态文件 (必须放在最后)
# 访问 http://localhost:8000 即可打开前端页面
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    # Windows 环境请使用 uv run python run.py 启动
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
