# ============================================================
# LangChain Tool 层
#
# LangChain负责：
# 1. Tool Schema
# 2. Tool 参数校验
#
# Registry负责：
# 1. Tool 白名单
# 2. Dangerous Confirmation
# 3. Retry / Backoff
# ============================================================

from langchain_core.tools import tool

from app.agent.registry import execute_tool


# ============================================================
# 1. 查询订单
# ============================================================

@tool
def get_order_record(order_id: int) -> dict:
    """
    根据订单ID查询订单状态。
    """

    return execute_tool(
        tool_name="get_order_record",
        arguments={
            "order_id": order_id
        }
    )


# ============================================================
# 2. 取消订单
# ============================================================

@tool
def cancel_order(order_id: int) -> dict:
    """
    取消指定订单。
    该操作会修改订单状态，需要用户确认。
    """

    return execute_tool(
        tool_name="cancel_order",
        arguments={
            "order_id": order_id
        }
    )


# ============================================================
# 3. 知识库
# ============================================================

@tool
def search_knowledge(question: str) -> dict:
    """
    查询跨境电商知识库，例如退货政策、退款政策、物流规则等。
    """

    return execute_tool(
        tool_name="search_knowledge",
        arguments={
            "question": question
        }
    )


# ============================================================
# 4. LangChain Tool 集合
# ============================================================

LANGCHAIN_TOOLS = [
    get_order_record,
    cancel_order,
    search_knowledge,
]