# ============================================================
# app/memory/redis_state.py
# Redis Agent State 管理
# ============================================================

import json
import os

import redis


# ============================================================
# 1. Redis连接
# ============================================================
# 本地直接运行：
#     REDIS_HOST 没有设置 → 使用 localhost
#
# Docker Compose运行：
#     REDIS_HOST=redis
#     → 连接名为 redis 的 Redis 容器

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
)

STATE_TTL = 1800


# ============================================================
# 2. State Key
# ============================================================

def build_state_key(user_id):

    return f"agent_state:{user_id}"


# ============================================================
# 3. 创建默认State
# ============================================================

def create_state(user_id):

    key = build_state_key(user_id)

    state = {
        "pending_action": None
    }

    redis_client.set(
        key,
        json.dumps(state),
        ex=STATE_TTL
    )

    return state


# ============================================================
# 4. 获取State
# ============================================================

def get_state(user_id):

    key = build_state_key(user_id)

    data = redis_client.get(key)

    if data is None:

        return create_state(user_id)

    return json.loads(data)


# ============================================================
# 5. 保存State
# ============================================================

def save_state(user_id, state):

    key = build_state_key(user_id)

    redis_client.set(
        key,
        json.dumps(state),
        ex=STATE_TTL
    )


# ============================================================
# 6. 设置待确认操作
# ============================================================

def set_pending_action(
    user_id,
    tool_name,
    arguments
):

    state = get_state(user_id)

    state["pending_action"] = {
        "tool_name": tool_name,
        "arguments": arguments
    }

    save_state(
        user_id,
        state
    )


# ============================================================
# 7. 获取待确认操作
# ============================================================

def get_pending_action(user_id):

    state = get_state(user_id)

    return state.get(
        "pending_action"
    )


# ============================================================
# 8. 清除
# ============================================================

def clear_pending_action(user_id):

    state = get_state(user_id)

    state["pending_action"] = None

    save_state(
        user_id,
        state
    )