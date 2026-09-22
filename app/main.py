# ============================================================
# app/main.py
# FastAPI 服务入口
# ============================================================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router
from app.config import LLM_MODEL
from app.database.db import init_db


# ============================================================
# 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title="Cross Border Ecommerce AI Agent",
    version="1.0.0"
)


# ============================================================
# 初始化数据库
# ============================================================

# 服务启动时自动创建数据库、orders 表和测试订单
init_db()


# ============================================================
# 注册路由
# ============================================================

app.include_router(
    chat_router,
    prefix="/api"
)


# ============================================================
# 前端页面
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)


@app.get("/")
def frontend():
    return FileResponse("frontend/index.html")


# ============================================================
# 健康检查接口
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "running",
        "message": "AI Agent Service is running",
        "model": LLM_MODEL
    }