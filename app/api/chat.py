# ============================================================
# app/api/chat.py
# Agent 对话接口 + 会话管理
#
# 以前只有一个写死的 demo_user，"新建会话"直接清空 Redis，
# 旧会话再也找不回来。
#
# 现在：
# - 每次对话归属一个 session_id
# - 消息同时写 Redis（热缓存）和 SQLite（持久化）
# - 支持新建 / 列表 / 回看 / 删除会话
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.agent import agent
from app.database.session_store import (
    create_session,
    delete_session,
    get_session_messages,
    list_sessions
)
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
    session_id: str | None = None


class ClearRequest(BaseModel):
    session_id: str | None = None


# ============================================================
# Chat 接口
#
# 不传 session_id 时自动创建一个新会话
# ============================================================

@router.post("/chat")
def chat(request: ChatRequest):

    session_id = (
        request.session_id
        or create_session()
    )

    result = agent(
        session_id,
        request.message
    )

    return {
        "result": result,
        "session_id": session_id
    }


# ============================================================
# 会话管理
# ============================================================

@router.post("/sessions")
def new_session():

    return {
        "session_id": create_session()
    }


@router.get("/sessions")
def get_sessions():

    return {
        "sessions": list_sessions()
    }


@router.get("/sessions/{session_id}/messages")
def session_messages(session_id: str):

    return {
        "session_id": session_id,
        "messages": get_session_messages(
            session_id
        )
    }


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):

    delete_session(session_id)

    # 同时清掉 Redis 里的热缓存和待确认状态
    clear_conversation(session_id)
    clear_pending_action(session_id)

    return {
        "status": "success",
        "message": "会话已删除"
    }


# ============================================================
# 兼容旧接口
#
# 旧前端会调 /chat/clear。
# 现在它只清空指定会话的 Redis 缓存，
# 历史消息在 SQLite 里仍然保留。
# ============================================================

@router.post("/chat/clear")
def clear_chat(request: ClearRequest = None):

    session_id = (
        request.session_id
        if request
        else None
    )

    if session_id:

        clear_conversation(session_id)
        clear_pending_action(session_id)

    return {
        "status": "success",
        "message": "会话缓存已清除"
    }
