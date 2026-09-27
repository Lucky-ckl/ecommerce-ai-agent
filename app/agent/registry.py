# ============================================================
# app/agent/registry.py
# Agent Tool Registry（装饰器版）
#
# 变化：
# 1. 注册方式从手写 dict 改为 @tool 装饰器
# 2. 参数信息从函数签名自动提取，不再手写 schema
# 3. execute_tool(tool_name, arguments) 签名保持不变，
#    所以 app/agent/agent.py 和 langchain_tools.py 不用改
#
# 设计参考 browser-use: browser_use/tools/registry/service.py
# ============================================================

import inspect
import time

from app.tools.order import (
    query_order,
    cancel_order
)

from app.tools.knowledge import search_knowledge

from app.tools.ticket import transfer_to_human

from app.tools.business import (
    list_orders,
    query_logistics,
    apply_refund,
    update_address,
    query_coupon,
    estimate_shipping_fee
)

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
# 1. Tool 规格与注册表
# ============================================================

class ToolSpec:
    """
    一个已注册 Tool 的全部信息。
    """

    def __init__(
        self,
        name,
        function,
        description,
        dangerous=False,
        signature=None
    ):

        self.name = name

        self.function = function

        self.description = description

        self.dangerous = dangerous

        # 从函数签名自动生成，不需要手写参数 schema
        self.signature = signature

    def param_names(self):
        """
        返回必填参数名列表（排除有默认值的参数）。
        """

        return [
            name
            for name, param in self.signature.parameters.items()
            if param.default is inspect.Parameter.empty
        ]

    def __repr__(self):

        return f"<ToolSpec {self.name} dangerous={self.dangerous}>"


# 注册表：tool_name -> ToolSpec
TOOLS = {}


def tool(
    name,
    description,
    dangerous=False
):
    """
    注册一个 Tool 的装饰器。

    用法：

        @tool("名字", "给模型看的描述", dangerous=False)
        def 你的函数(参数: 类型):
            ...

    描述会自动成为提示词的一部分，
    参数信息从函数签名自动提取。
    """

    def decorator(func):

        TOOLS[name] = ToolSpec(
            name=name,
            function=func,
            description=description,
            dangerous=dangerous,
            signature=inspect.signature(func)
        )

        logger.info(
            f"Tool已注册 | "
            f"tool={name} | "
            f"dangerous={dangerous}"
        )

        # 原样返回函数本身，不影响任何直接调用
        return func

    return decorator


def is_dangerous(tool_name):
    """
    判断某个 Tool 是否需要人工确认。
    """

    spec = TOOLS.get(tool_name)

    return bool(spec and spec.dangerous)


def describe_tools():
    """
    生成给模型看的 Tool 清单。

    新增 Tool 时这里会自动包含它，不需要手动维护。
    """

    lines = []

    for spec in TOOLS.values():

        params = ", ".join(
            f"{p_name}: {p.annotation.__name__ if hasattr(p.annotation, '__name__') else p.annotation}"
            for p_name, p in spec.signature.parameters.items()
        )

        mark = "【危险操作，需用户确认】" if spec.dangerous else ""

        lines.append(
            f"- {spec.name}({params}): {spec.description}{mark}"
        )

    return "\n".join(lines)


# ============================================================
# 2. 注册业务 Tools
# ============================================================

@tool(
    "get_order_record",
    "根据订单ID查询订单状态"
)
def get_order_record(order_id: int):

    return query_order(order_id)


@tool(
    "cancel_order",
    (
        "取消指定订单。"
        "当用户明确要求取消订单时必须调用此Tool。"
        "该操作会修改订单状态，需要用户确认。"
    ),
    dangerous=True
)
def cancel_order_tool(order_id: int):

    return cancel_order(order_id)


@tool(
    "list_orders",
    "查询某个用户名下的全部订单列表"
)
def list_orders_tool(user_id: int):

    return list_orders(user_id)


@tool(
    "query_logistics",
    "查询订单的物流轨迹、承运商与预计到达时间"
)
def query_logistics_tool(order_id: int):

    return query_logistics(order_id)


@tool(
    "apply_refund",
    (
        "为订单申请退款。"
        "该操作会产生一笔退款单，需要用户确认。"
    ),
    dangerous=True
)
def apply_refund_tool(
    order_id: int,
    reason: str = "用户申请"
):

    return apply_refund(order_id, reason)


@tool(
    "update_address",
    (
        "修改订单的收货地址。"
        "该操作会修改订单信息，需要用户确认。"
    ),
    dangerous=True
)
def update_address_tool(
    order_id: int,
    new_address: str
):

    return update_address(order_id, new_address)


@tool(
    "query_coupon",
    "查询某个用户可用的优惠券、金额与有效期"
)
def query_coupon_tool(user_id: int):

    return query_coupon(user_id)


@tool(
    "estimate_shipping_fee",
    "根据国家与重量估算运费和时效"
)
def estimate_shipping_fee_tool(
    country: str,
    weight_kg: float = 1.0
):

    return estimate_shipping_fee(country, weight_kg)


@tool(
    "transfer_to_human",
    (
        "转接人工客服，创建一张人工工单。"
        "当用户明确要求转人工、"
        "或者你的知识库查不到答案无法准确回答时调用。"
    )
)
def transfer_to_human_tool(reason: str):

    return transfer_to_human(reason)


@tool(
    "search_knowledge",
    (
        "查询跨境电商知识库，"
        "例如退货政策、退款政策、物流规则等。"
    )
)
def search_knowledge_tool(
    question: str,
    k: int = 5,
    top_k: int = 3
):

    return search_knowledge(
        question=question,
        k=k,
        top_k=top_k
    )


# ============================================================
# 3. 执行 Tool
# ============================================================

def check_arguments(spec, arguments):
    """
    用函数签名校验模型传来的参数。

    返回 None 表示通过，
    返回字符串表示错误信息。
    """

    try:

        spec.signature.bind(**arguments)

        return None

    except TypeError as e:

        return str(e)


def execute_tool(
    tool_name,
    arguments
):
    """
    执行已经通过 LangChain Tool Schema 校验的 Tool。

    本函数负责：

    1. Tool 白名单检查
    2. 参数校验
    3. Tool 业务函数执行
    4. Retry / Backoff
    5. 日志记录

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

    if tool_name not in TOOLS:

        logger.error(
            f"Tool不存在 | tool={tool_name}"
        )

        return error(
            code="TOOL_NOT_FOUND",
            message=f"不存在的 Tool：{tool_name}"
        )

    spec = TOOLS[tool_name]

    # ========================================================
    # ② 参数校验
    #
    # 模型可能传错参数名或漏传参数。
    # 这里用签名挡住，避免业务函数抛出难以理解的 TypeError。
    # ========================================================

    argument_error = check_arguments(
        spec,
        arguments or {}
    )

    if argument_error:

        logger.warning(
            f"Tool参数不合法 | "
            f"tool={tool_name} | "
            f"error={argument_error}"
        )

        return error(
            code="TOOL_INVALID_ARGUMENTS",
            message=(
                f"Tool {tool_name} 参数不合法："
                f"{argument_error}"
            )
        )

    # ========================================================
    # ③ 执行 Tool + Retry / Backoff
    # ========================================================

    for attempt in range(MAX_TOOL_RETRIES + 1):

        try:

            logger.info(
                f"开始执行Tool | "
                f"tool={tool_name} | "
                f"attempt={attempt + 1}"
            )

            result = spec.function(
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
