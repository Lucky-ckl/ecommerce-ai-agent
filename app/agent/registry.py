# ============================================================
# app/agent/registry.py
# Agent Tool Registry
# ============================================================

import time

from app.tools.order import (
    query_order,
    cancel_order
)

from app.tools.knowledge import search_knowledge

from app.agent.result import (
    error,
    system_error
)

from app.utils.logger import logger


# ============================================================
# 0. Retry / Backoff 配置
# ============================================================

# 最多额外重试 2 次
# 一次 Tool 最多执行 3 次：
# 第 1 次 + Retry 1 + Retry 2
MAX_TOOL_RETRIES = 2

# 第一次重试等待 1 秒
RETRY_BASE_DELAY = 1


def is_retryable_error(exception):
    """
    判断异常是否属于可以重试的临时错误。
    """

    return isinstance(
        exception,
        (
            TimeoutError,
            ConnectionError
        )
    )


def get_backoff_delay(retry_number):
    """
    指数退避：

    第 1 次重试：1 秒
    第 2 次重试：2 秒
    第 3 次重试：4 秒
    """

    return RETRY_BASE_DELAY * (2 ** (retry_number - 1))


# ============================================================
# 1. Tool Registry
# ============================================================

tools = {

    "get_order_record": {
        "function": query_order,

        "description": "根据订单ID查询订单状态",

        "dangerous": False
    },

    "cancel_order": {
        "function": cancel_order,

        "description": (
            "取消指定订单。"
            "当用户明确要求取消订单时必须调用此Tool。"
            "该操作会修改订单状态，需要用户确认。"
        ),

        "dangerous": True
    },

    "search_knowledge": {
        "function": None,

        "description": (
            "查询跨境电商知识库，"
            "例如退货政策、退款政策、物流规则等。"
        ),

        "dangerous": False
    }

}


# ============================================================
# 2. RAG Tool
# ============================================================

def search_knowledge_tool(question: str):
    """
    RAG 工具的实际执行入口。
    """

    return search_knowledge(
        question=question,
        k=5,
        top_k=3
    )


# 将 RAG 工具函数放入 Registry
tools["search_knowledge"]["function"] = search_knowledge_tool


# ============================================================
# 3. 执行 Tool
# ============================================================

def execute_tool(
    tool_name,
    arguments
):
    """
    执行已经通过 LangChain Tool Schema 校验的 Tool。

    本函数负责：

    1. Tool 白名单检查
    2. Tool 业务函数执行
    3. Retry / Backoff
    4. 日志记录

    参数结构校验由 LangChain @tool 负责。
    Dangerous Tool 确认由 Middleware 负责。
    """

    logger.info(
        f"Tool调用开始 | "
        f"tool={tool_name} | "
        f"arguments={arguments}"
    )

    # ========================================================
    # ① Tool 白名单检查
    # ========================================================

    if tool_name not in tools:

        logger.error(
            f"Tool不存在 | tool={tool_name}"
        )

        return error(
            code="TOOL_NOT_FOUND",
            message=f"不存在的 Tool：{tool_name}"
        )

    tool = tools[tool_name]

    # ========================================================
    # ② 执行 Tool + Retry / Backoff
    # ========================================================

    for attempt in range(MAX_TOOL_RETRIES + 1):

        try:

            logger.info(
                f"开始执行Tool | "
                f"tool={tool_name} | "
                f"attempt={attempt + 1}"
            )

            result = tool["function"](
                **arguments
            )

            logger.info(
                f"Tool执行完成 | "
                f"tool={tool_name} | "
                f"result={result}"
            )

            return result

        except Exception as e:

            # ------------------------------------------------
            # 不属于临时错误：不重试
            # ------------------------------------------------

            if not is_retryable_error(e):

                logger.exception(
                    f"Tool执行异常 | "
                    f"tool={tool_name}"
                )

                return system_error(
                    message=str(e)
                )

            # ------------------------------------------------
            # 已达到最大重试次数
            # ------------------------------------------------

            if attempt >= MAX_TOOL_RETRIES:

                logger.exception(
                    f"Tool重试次数耗尽 | "
                    f"tool={tool_name}"
                )

                return system_error(
                    message=(
                        f"Tool执行失败，"
                        f"重试{MAX_TOOL_RETRIES}次后仍然失败："
                        f"{str(e)}"
                    )
                )

            # ------------------------------------------------
            # Exponential Backoff
            # ------------------------------------------------

            retry_number = attempt + 1

            delay = get_backoff_delay(
                retry_number
            )

            logger.warning(
                f"Tool执行失败，准备重试 | "
                f"tool={tool_name} | "
                f"retry={retry_number} | "
                f"delay={delay}s | "
                f"error={str(e)}"
            )

            time.sleep(delay)