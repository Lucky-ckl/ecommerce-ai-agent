# ============================================================
# app/api/chat.py
# Agent 对话接口
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.agent import agent
from app.memory.conversation import clear_conversation
from app.memory.redis_state import clear_pending_action


# ============================================================
# 创建 Router
# ============================================================

router = APIRouter()


# ============================================================
# 请求参数
# ============================================================

class ChatRequest(BaseModel):
    message: str


# ============================================================
# Demo 会话 ID
# ============================================================

DEMO_USER_ID = "demo_user"


# ============================================================
# Chat接口
# ============================================================

@router.post("/chat")
def chat(request: ChatRequest):
    result = agent(
        DEMO_USER_ID,
        request.message
    )

    return {
        "result": result
    }


# ============================================================
# 新建会话
#
# 前端点击“新建会话”时，同时清除：
# 1. Conversation Memory
# 2. Redis pending_action
# ============================================================

@router.post("/chat/clear")
def clear_chat():
    clear_conversation(DEMO_USER_ID)
    clear_pending_action(DEMO_USER_ID)

    return {
        "status": "success",
        "message": "会话已清除"
    }
