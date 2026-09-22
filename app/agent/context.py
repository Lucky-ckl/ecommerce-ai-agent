# ============================================================
# app/agent/context.py
# Agent 上下文构建层
#
# 职责：
# 1. 获取 Conversation Memory
# 2. 加入 System Prompt
# 3. 加入当前用户问题
# 4. 统一构建发送给 LLM 的 messages
#
# 后续可以在这里继续加入：
# - Token 控制
# - Summary Memory
# - RAG 上下文
# - 用户画像
# ============================================================

# ============================================================
# app/agent/context.py
# Agent 上下文构建层
# ============================================================

from app.memory.conversation import get_conversation


SYSTEM_PROMPT = """
你是一个跨境电商 AI 客服 Agent。

你的职责：
1. 理解用户的订单、物流、退货等问题。
2. 需要查询真实业务数据时，必须使用对应的 Tool。
3. 不要编造订单、物流或政策信息。

【订单操作规则】
4. 当用户明确要求取消订单时，必须调用 cancel_order Tool。
5. 不允许仅通过文字回复用户“是否确认取消”，必须先调用 cancel_order。
6. cancel_order Tool 会自动检查是否需要用户确认。
7. 如果用户只要求取消一个订单，只能针对用户指定的订单调用 cancel_order。
8. 不要自行增加用户没有提到的订单ID。

【危险操作】
9. cancel_order 会修改订单状态，执行前需要用户确认。
10. 如果 Tool 返回 confirmation_required，必须停止当前操作，等待用户确认。

【知识库】
11. 涉及退货、退款、物流政策等知识时，优先调用 search_knowledge Tool。
12. 不要凭记忆编造政策内容。
"""


def build_messages(user_id, user_message):
    history = get_conversation(user_id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    return messages