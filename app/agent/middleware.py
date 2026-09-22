# ============================================================
# app/agent/middleware.py
# LangChain Agent Middleware
# ============================================================

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

from app.memory.redis_state import set_pending_action
from app.utils.logger import logger


# ============================================================
# Dangerous Tool Confirmation Middleware
# ============================================================

@wrap_tool_call
def dangerous_tool_confirmation(request, handler):
    """
    拦截危险 Tool。

    当前规则：
    - cancel_order：必须先经过用户确认
    - 其他 Tool：直接放行

    request:
        LangChain 当前准备执行的 Tool Call

    handler:
        真正执行 Tool 的函数
    """

    # --------------------------------------------------------
    # ① 获取 Tool 信息
    # --------------------------------------------------------

    tool_name = request.tool_call["name"]
    arguments = request.tool_call["args"]

    logger.info(
        f"Middleware拦截Tool | "
        f"tool={tool_name} | "
        f"arguments={arguments}"
    )

    # --------------------------------------------------------
    # ② 非危险 Tool：直接放行
    # --------------------------------------------------------

    if tool_name != "cancel_order":

        return handler(request)

    # --------------------------------------------------------
    # ③ 获取当前用户
    # --------------------------------------------------------

    user_id = request.runtime.context.user_id

    # --------------------------------------------------------
    # ④ 保存待确认操作
    # --------------------------------------------------------

    set_pending_action(
        user_id=user_id,
        tool_name=tool_name,
        arguments=arguments
    )

    logger.warning(
        f"危险Tool需要用户确认 | "
        f"user_id={user_id} | "
        f"tool={tool_name} | "
        f"arguments={arguments}"
    )

    # --------------------------------------------------------
    # ⑤ 不调用 handler
    #
    # 也就是说：
    #
    # cancel_order
    #     ↓
    # Middleware
    #     ↓
    # 发现没有确认
    #     ↓
    # 不执行真正的 cancel_order
    # --------------------------------------------------------

    return ToolMessage(
        content=(
            "该操作会修改订单状态，"
            "需要用户确认后才能执行。"
            "请回复“确认”或“取消”。"
        ),
        tool_call_id=request.tool_call["id"]
    )