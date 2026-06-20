FROM python:3.12-slim

WORKDIR /app

# 复制整个项目（保持目录结构）
COPY backend/ backend/
COPY frontend/ frontend/

# 安装依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "run.py"]
