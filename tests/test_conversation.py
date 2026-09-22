from app.memory.conversation import (
    add_message,
    get_conversation,
    clear_conversation
)


user_id = "memory_test_user"


# ============================================================
# 1. 清理旧数据
# ============================================================

clear_conversation(user_id)


# ============================================================
# 2. 保存多轮对话
# ============================================================

add_message(
    user_id,
    "user",
    "我的订单1001怎么样？"
)

add_message(
    user_id,
    "assistant",
    "订单1001正在等待发货。"
)

add_message(
    user_id,
    "user",
    "那它什么时候能到？"
)


# ============================================================
# 3. 读取历史
# ============================================================

history = get_conversation(user_id)

print("===== Conversation Memory =====")

for message in history:
    print(message)


# ============================================================
# 4. 清理
# ============================================================

clear_conversation(user_id)

print("\n===== 清理后的 Memory =====")

print(
    get_conversation(user_id)
)