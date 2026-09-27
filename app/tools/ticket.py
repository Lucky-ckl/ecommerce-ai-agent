# ============================================================
# app/tools/ticket.py
# 人工客服工单工具
# ============================================================

from app.agent.session_context import get_current_session
from app.database.ticket_store import create_ticket
from app.utils.logger import logger


def transfer_to_human(reason: str):
    """
    创建人工客服工单。

    当出现下面情况时调用：

    1. 用户明确要求转人工客服
    2. 用户的问题知识库里查不到，无法准确回答
    3. 用户情绪激动、反复追问同一个没有得到解决的问题

    参数：
        reason: 简短说明为什么要转人工
    """

    session_id = get_current_session()

    logger.info(
        f"转人工工具被调用 | "
        f"session={session_id} | "
        f"reason={reason}"
    )

    ticket = create_ticket(
        session_id=session_id,
        user_message=reason,
        reason="agent_escalation"
    )

    return {
        "status": "success",
        "data": ticket,
        "message": (
            f"已为你转接人工客服，"
            f"工单号 {ticket['ticket_id']}，"
            f"客服会尽快与你联系。"
        )
    }
