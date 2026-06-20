"""Windows 开发环境启动入口
解决 psycopg async 在 Windows ProactorEventLoop 下的兼容性问题
用法: uv run python run.py
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
