# ============================================================
# app/memory/conversation.py
# Redis Conversation Memory
# ============================================================

import json

from app.memory.redis_state import redis_client


# ============================================================
# 1. Conversation Memory 配置
# ============================================================

CONVERSATION_TTL = 1800

# 最多保存多少轮完整对话
# 一轮 = user + assistant
MAX_HISTORY_ROUNDS = 5


# ============================================================
# 2. 构建 Conversation Key
# ============================================================

def build_conversation_key(user_id):

    return f"conversation:{user_id}"


# ============================================================
# 3. 获取历史消息
# ============================================================

def get_conversation(user_id):

    key = build_conversation_key(user_id)

    data = redis_client.get(key)

    if data is None:
        return []

    return json.loads(data)



# ============================================================
# 4. 保存一条消息
# ============================================================

def add_message(
    user_id,
    role,
    content
):

    key = build_conversation_key(user_id)

    history = get_conversation(user_id)

    new_message = {
        "role": role,
        "content": content
    }

    # ========================================================
    # 防止连续保存完全相同的消息
    #
    # 例如：
    #
    # user: 你好
    # user: 你好
    #
    # 第二条不会重复保存。
    #
    # 但如果是：
    #
    # user: 你好
    # assistant: 你好，有什么可以帮你？
    # user: 你好
    #
    # 第三个 user 仍然会正常保存。
    # ========================================================

    if history and history[-1] == new_message:
        return

    history.append(new_message)

    # ========================================================
    # 只保留最近的完整对话轮次
    #
    # 一轮：
    # user
    # assistant
    #
    # 最多保存 MAX_HISTORY_ROUNDS 轮
    # ========================================================

    max_messages = MAX_HISTORY_ROUNDS * 2

    history = history[-max_messages:]

    # ========================================================
    # 保存到 Redis
    # ========================================================

    redis_client.set(
        key,
        json.dumps(
            history,
            ensure_ascii=False
        ),
        ex=CONVERSATION_TTL
    )

# ============================================================
# 5. 清除历史消息
# ============================================================

def clear_conversation(user_id):

    key = build_conversation_key(user_id)

    redis_client.delete(key)