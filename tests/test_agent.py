# ============================================================
# tests/test_agent.py
# Agent 综合测试
# ============================================================
from app.memory.conversation import clear_conversation
from app.database.db import (
    init_db,
    get_order_record,
    reset_test_data
)

from app.agent.agent import agent

from app.memory.redis_state import (
    get_pending_action,
    clear_pending_action
)


# ============================================================
# 1. 初始化数据库 + 重置测试数据
# ============================================================

init_db()
reset_test_data()


# ============================================================
# 2. 定义测试用户
# ============================================================

user_id = "user_001"

# 清理本次测试用户的历史对话
clear_conversation(user_id)

# 清理可能残留的待确认操作
clear_pending_action(user_id)
# ============================================================
# 3. 第一次请求：取消订单1002
# ============================================================

print("\n===== 第一次请求：取消订单1002 =====")

result = agent(
    user_id,
    "帮我取消订单1002"
)

print(result)


# Agent应该要求用户确认
assert result["status"] == "waiting_for_confirmation"


# ============================================================
# 4. 查看 Redis State
# ============================================================

print("\n===== 当前 Redis State =====")

pending_action = get_pending_action(user_id)

print(pending_action)

assert pending_action is not None

assert pending_action["tool_name"] == "cancel_order"

assert pending_action["arguments"]["order_id"] == 1002


# ============================================================
# 5. 第二次请求：用户确认取消
# ============================================================

print("\n===== 第二次请求：确认取消 =====")

result = agent(
    user_id,
    "确认"
)

print(result)

assert result["status"] == "success"


# ============================================================
# 6. 检查 Redis State 是否已经清除
# ============================================================

print("\n===== 确认后的 Redis State =====")

pending_action = get_pending_action(user_id)

print(pending_action)

assert pending_action is None


# ============================================================
# 7. 再次查询数据库
# ============================================================

print("\n===== 最终订单状态 =====")

order = get_order_record(1002)

print(order)

assert order["status"] == "已取消"


# ============================================================
# 8. 第三次：测试 Agent 自动调用 RAG
# ============================================================

print("\n===== 第三次请求：RAG 知识库 =====")

rag_user_id = "rag_test_user"

result = agent(
    rag_user_id,
    "日本退货审核通过后多久退款到账？"
)


# ============================================================
# 9. 输出 Agent 最终回答
# ============================================================

print("\n===== RAG Agent 最终回答 =====")

print(result)

assert result is not None


# ============================================================
# 10. 测试结束后清理 Redis State
# ============================================================

clear_pending_action(user_id)

print("\n===== Agent 测试完成 =====")