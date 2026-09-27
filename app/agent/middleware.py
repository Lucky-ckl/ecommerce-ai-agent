# ============================================================
# app/agent/middleware.py
# LangChain Agent Middleware
# ============================================================

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

from app.agent.registry import is_dangerous
from app.agent.result import confirmation_required
from app.memory.redis_state import set_pending_action
from app.utils.logger import logger


# ============================================================
# 危险操作确认（可复用）
#
# 以前这里硬编码只拦 cancel_order，
# 导致新增的危险 Tool（退款、改地址）绕过确认直接执行。
#
# 现在改为查注册表里的 dangerous 标记，
# 新增危险 Tool 时不用再改中间件。
# ============================================================

def require_confirmation(
    tool_name,
    arguments,
    user_id
):
    """
    如果是危险 Tool：写入待确认状态并返回确认请求。
    如果不是：返回 None，表示可以直接执行。
    """

    if not is_dangerous(tool_name):

        return None

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

    return confirmation_required(
        tool_name=tool_name,
        arguments=arguments,
        message=(
            f"即将执行 {tool_name}，"
            f"该操作会修改订单数据，请确认是否继续。"
            f"请回复“确认”或“取消”。"
        )
    )


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

    user_id = request.runtime.context.user_id

    confirmation = require_confirmation(
        tool_name=tool_name,
        arguments=arguments,
        user_id=user_id
    )

    # --------------------------------------------------------
    # ③ 非危险 Tool：直接放行
    # --------------------------------------------------------

    if confirmation is None:

        return handler(request)

    # --------------------------------------------------------
    # ④ 不调用 handler
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