# ============================================================
# app/agent/session_context.py
# 当前会话上下文
#
# Tool 函数只能拿到模型传来的参数，
# 拿不到当前 session_id（工单需要它）。
#
# 用 ContextVar 在 Agent 执行前设置，
# Tool 执行期间读取，避免为此大改 Tool 调用链。
# ============================================================

from contextvars import ContextVar


_current_session_id: ContextVar[str] = ContextVar(
    "current_session_id",
    default=None
)


def set_current_session(session_id):

    _current_session_id.set(session_id)


def get_current_session():

    return _current_session_id.get()
