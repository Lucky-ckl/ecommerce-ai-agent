# ============================================================
# app/agent/agent.py
# LangChain Agent 核心
#
# 包含：
# 1. LangChain Agent
# 2. Conversation Memory
# 3. Dangerous Tool Confirmation
# 4. Redis pending_action
# 5. Tool Registry
# 6. Tool Retry / Exponential Backoff
# ============================================================

import json

from langchain.agents import create_agent
from app.agent.callback import ToolLoggingCallback
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

from dataclasses import dataclass

from app.agent.registry import execute_tool

from app.memory.redis_state import (
    get_pending_action,
    clear_pending_action
)

from app.memory.conversation import (
    get_conversation,
    add_message
)

from app.config import (
    API_KEY,
    LLM_BASE_URL,
    LLM_MODEL
)

from app.utils.logger import logger

from app.agent.context import SYSTEM_PROMPT

from app.agent.guardrails import (
    INTENT_HANDOFF,
    INTENT_LABELS,
    JAILBREAK_MESSAGE,
    classify_intent,
    detect_jailbreak,
    rejection_for
)

from app.agent.language import build_language_hint

from app.agent.session_context import set_current_session

from app.database.ticket_store import create_ticket

from app.agent.result import system_error

from app.agent.middleware import dangerous_tool_confirmation

@dataclass
class AgentContext:
    user_id: str

# ============================================================
# 1. LangChain Chat Model
# ============================================================

model = ChatOpenAI(
    model=LLM_MODEL,
    api_key=API_KEY,
    base_url=LLM_BASE_URL,

    # 不在这里自动重试整个 Agent。
    #
    # 原因：
    # Agent 可能已经执行了 Tool。
    #
    # 如果整个 Agent 重试：
    #
    # Agent
    #   ↓
    # cancel_order
    #   ↓
    # 已经执行
    #   ↓
    # LLM 请求异常
    #   ↓
    # 整个 Agent 重跑
    #
    # 可能造成重复业务操作。
    max_retries=0
)


# ============================================================
# 2. LangChain Tools
#
# LangChain负责：
# - Tool名称
# - Tool描述
# - Tool参数Schema
#
# Registry负责：
# - Tool白名单
# - Dangerous确认
# - Retry / Backoff
# - 真正业务函数执行
# ============================================================


@tool
def get_order_record(order_id: int) -> dict:
    """
    根据订单ID查询订单状态。
    """

    logger.info(
        f"LangChain Tool调用 | "
        f"tool=get_order_record | "
        f"order_id={order_id}"
    )

    return execute_tool(
        tool_name="get_order_record",
        arguments={
            "order_id": order_id
        }
    )


@tool
def cancel_order(order_id: int) -> dict:
    """
    取消指定订单。

    Dangerous Tool 的确认由 Middleware 负责。
    """

    logger.info(
        f"LangChain Tool调用 | "
        f"tool=cancel_order | "
        f"order_id={order_id}"
    )

    return execute_tool(
        tool_name="cancel_order",
        arguments={
            "order_id": order_id
        }
    )

@tool
def transfer_to_human(reason: str) -> dict:
    """
    转接人工客服，创建一张人工工单。

    适用情况：

    1. 用户明确要求转人工客服
    2. 知识库查不到答案，无法准确回答
    3. 用户情绪激动、问题反复得不到解决
    """

    logger.info(
        f"LangChain Tool调用 | "
        f"tool=transfer_to_human | "
        f"reason={reason}"
    )

    return execute_tool(
        tool_name="transfer_to_human",
        arguments={
            "reason": reason
        }
    )


@tool
def search_knowledge(question: str) -> dict:
    """
    查询跨境电商知识库，例如退货政策、退款政策、物流规则等。
    """

    logger.info(
        f"LangChain Tool调用 | "
        f"tool=search_knowledge | "
        f"question={question}"
    )

    return execute_tool(
        tool_name="search_knowledge",
        arguments={
            "question": question
        }
    )


# ============================================================
# 3. LangChain Tool集合
# ============================================================

LANGCHAIN_TOOLS = [
    get_order_record,
    cancel_order,
    search_knowledge,
    transfer_to_human
]


# ============================================================
# 4. 当前用户ID
#
# 说明：
# LangChain Tool函数本身只接收模型提供的参数。
#
# 但是我们的Dangerous Tool需要知道当前user_id，
# 才能把pending_action保存到对应Redis Key。
#
# 当前先使用模块级变量连接现有架构。
# 后续如果需要进一步工程化，可以改成ToolRuntime Context。
# ============================================================




# ============================================================
# 5. 创建 LangChain Agent
# ============================================================

agent_executor = create_agent(
    model=model,
    tools=LANGCHAIN_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    context_schema=AgentContext,
    middleware=[
        dangerous_tool_confirmation
    ]
)


# ============================================================
# 5.1 提前返回
#
# 护栏命中、或已转人工时，
# 不调用模型，但要照常把消息存进历史，
# 保证用户切回会话时还能看到完整对话。
# ============================================================

def finish_early(
    user_id,
    user_message,
    reply,
    ticket=None
):

    add_message(
        user_id,
        "user",
        user_message
    )

    add_message(
        user_id,
        "assistant",
        reply
    )

    result = {
        "status": "success",
        "message": reply
    }

    if ticket is not None:

        result["data"] = {
            "ticket": ticket
        }

    return result


# ============================================================
# 6. 用户确认 / 取消处理
# ============================================================

def handle_pending_action(
    user_id,
    user_message
):
    """
    处理Redis中的待确认危险操作。
    """

    pending_action = get_pending_action(user_id)

    if pending_action is None:
        return None


    logger.info(
        f"检测到待确认操作 | "
        f"user_id={user_id} | "
        f"pending_action={pending_action}"
    )


    message = user_message.strip().lower()


    # ========================================================
    # 用户确认
    # ========================================================

    if message in [
        "确认",
        "确定",
        "是",
        "yes",
        "y"
    ]:

        tool_name = pending_action["tool_name"]

        arguments = pending_action["arguments"]

        logger.info(
            f"用户确认危险操作 | "
            f"tool={tool_name} | "
            f"arguments={arguments}"
        )


        result = execute_tool(
            tool_name,
            arguments,
        )


        clear_pending_action(user_id)


        logger.info(
            f"确认操作执行完成 | "
            f"result={result}"
        )


        # 保存这次确认后的结果
        add_message(
            user_id,
            "assistant",
            json.dumps(
                result,
                ensure_ascii=False
            )
        )


        return result


    # ========================================================
    # 用户取消
    # ========================================================

    if message in [
        "取消",
        "不用了",
        "不要",
        "no",
        "n"
    ]:

        logger.info(
            "用户取消危险操作"
        )


        clear_pending_action(user_id)


        result = {
            "status": "cancelled",
            "message": "已取消该操作"
        }


        add_message(
            user_id,
            "assistant",
            result["message"]
        )


        return result


    # ========================================================
    # 用户没有明确确认 / 取消
    # ========================================================

    return {
        "status": "waiting_for_confirmation",
        "message": (
            "当前有一个待确认操作，"
            "请回复“确认”或“取消”。"
        )
    }


# ============================================================
# 7. Agent
# ============================================================

def agent(user_id, user_message):



    logger.info(
        f"Agent收到用户请求 | "
        f"user_id={user_id} | "
        f"message={user_message}"
    )


    # ========================================================
    # ① 处理Redis中的待确认操作
    # ========================================================

    pending_result = handle_pending_action(
        user_id=user_id,
        user_message=user_message
    )


    if pending_result is not None:

        return pending_result


    # ========================================================
    # ② 入口治理
    #
    # 在调用 LLM 之前先做三件事：
    #
    # 1. 提示词注入检测
    # 2. 意图分类（Triage）
    # 3. 无关问题拦截（Relevance Guardrail）
    #
    # 命中就直接返回，不再调用模型：
    # 省钱、省时间，也不会被带跑偏。
    # ========================================================

    if detect_jailbreak(user_message):

        logger.warning(
            f"命中提示词注入护栏 | "
            f"user_id={user_id} | "
            f"message={user_message}"
        )

        return finish_early(
            user_id,
            user_message,
            JAILBREAK_MESSAGE
        )


    intent = classify_intent(user_message)

    logger.info(
        f"意图识别结果 | "
        f"intent={intent}"
    )


    rejected, rejection_message = rejection_for(
        intent
    )

    if rejected:

        logger.info(
            f"命中无关问题护栏 | "
            f"intent={intent}"
        )

        return finish_early(
            user_id,
            user_message,
            rejection_message
        )


    # 用户明确要求转人工：直接开工单，不走模型
    if intent == INTENT_HANDOFF:

        ticket = create_ticket(
            session_id=user_id,
            user_message=user_message,
            reason="user_request"
        )

        return finish_early(
            user_id,
            user_message,
            (
                f"已为你转接人工客服 🎧\n"
                f"工单号：{ticket['ticket_id']}\n"
                f"客服会尽快与你联系，请留意消息通知。"
            ),
            ticket=ticket
        )


    # ========================================================
    # ③ 读取Conversation Memory
    # ========================================================

    history = get_conversation(user_id)


    logger.info(
        f"读取Conversation Memory | "
        f"user_id={user_id} | "
        f"history_count={len(history)}"
    )


    # ========================================================
    # ③ 保存用户消息
    # ========================================================




    # ========================================================
    # ④ 构造LangChain Messages
    #
    # Redis中的：
    #
    # {
    #     "role": "user",
    #     "content": "..."
    # }
    #
    # 可以直接转换成LangChain message格式。
    # ========================================================

    messages = []

    for item in history:

        messages.append({
            "role": item["role"],
            "content": item["content"]
        })


    # --------------------------------------------------------
    # 语言指令和意图提示只追加给模型看
    # 存进历史的是用户的原始消息，避免污染上下文
    # --------------------------------------------------------

    language, language_hint = build_language_hint(
        user_message
    )

    intent_hint = (
        f"\n\n[问题类型] "
        f"{INTENT_LABELS.get(intent, '普通咨询')}"
    )

    logger.info(
        f"应答语言 | "
        f"language={language} | "
        f"intent={intent}"
    )

    messages.append({
        "role": "user",
        "content": (
            user_message
            + language_hint
            + intent_hint
        )
    })

    add_message(
        user_id,
        "user",
        user_message
    )

    # Tool 需要知道当前会话（转人工工单要用）
    set_current_session(user_id)


    # ========================================================
    # ⑤ LangChain Agent执行
    #
    # 以前：
    #
    # for iteration:
    #     LLM
    #     ↓
    #     Tool
    #     ↓
    #     LLM
    #     ↓
    #     Tool
    #
    # 现在：
    #
    # create_agent()
    #     ↓
    # LangChain自动管理Agent Loop
    # ========================================================

    try:

        logger.info(
            "开始执行LangChain Agent"
        )


        result = agent_executor.invoke(
            {
                "messages": messages
            },
            context=AgentContext(
                user_id=user_id
            ),
            config={
                "callbacks": [
                    ToolLoggingCallback()
                ]
            }
        )


        logger.info(
            f"LangChain Agent执行完成 | "
            f"result={result}"
        )


    except Exception as e:

        logger.exception(
            f"LangChain Agent执行异常 | "
            f"error={str(e)}"
        )


        return system_error(
            message=(
                "AI服务暂时不可用，"
                "请稍后再试。"
            )
        )


    # ========================================================
    # ⑥ 获取最终AI消息
    # ========================================================

    result_messages = result.get(
        "messages",
        []
    )


    if not result_messages:

        logger.error(
            "LangChain Agent返回messages为空"
        )


        return system_error(
            message="AI服务返回结果异常，请稍后再试。"
        )


    final_message = result_messages[-1]


    # ========================================================
    # ⑦ 获取最终回答
    # ========================================================

    content = final_message.content


    logger.info(
        f"LLM最终回答 | "
        f"{content}"
    )


    # ========================================================
    # ⑧ 保存Assistant Memory
    # ========================================================

    add_message(
        user_id,
        "assistant",
        content
    )


    return content