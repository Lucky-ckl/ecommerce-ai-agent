# ============================================================
# Dockerfile
# 跨境电商 AI 客服 Agent
# ============================================================

# 1. Python 基础镜像
FROM python:3.11-slim

# 2. 容器内部工作目录
WORKDIR /app

# 3. 复制依赖文件
COPY requirements.txt .

# 4. 安装 Python 依赖
RUN pip install --no-cache-dir --timeout 300 --retries 5 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 5. 复制应用代码
COPY app ./app

# 复制前端页面
COPY frontend ./frontend

# 6. 暴露 FastAPI 端口
EXPOSE 8000

# 7. 启动 FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]