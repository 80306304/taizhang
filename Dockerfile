FROM python:3.12-slim

WORKDIR /app

# 使用阿里云 PyPI 镜像
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --upgrade pip

# 复制整个项目（保持目录结构）
COPY backend/ backend/
COPY frontend/ frontend/

# 安装依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r backend/requirements.txt

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8000

WORKDIR /app/backend

CMD ["python", "run.py"]
