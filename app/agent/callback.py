# ============================================================
# app/agent/callback.py
# LangChain Callback：统一记录 Tool 调用
# ============================================================

import time

from langchain_core.callbacks import BaseCallbackHandler


class ToolLoggingCallback(BaseCallbackHandler):
    """
    监听 LangChain Tool 生命周期：

    on_tool_start  -> Tool开始
    on_tool_end    -> Tool成功结束
    on_tool_error  -> Tool发生异常
    """

    def __init__(self):
        super().__init__()

        # 保存每个 Tool 的开始时间
        self.start_times = {}

    # ========================================================
    # Tool 开始
    # ========================================================

    def on_tool_start(
        self,
        serialized,
        input_str,
        *,
        run_id,
        parent_run_id=None,
        tags=None,
        metadata=None,
        inputs=None,
        **kwargs
    ):
        self.start_times[str(run_id)] = time.time()

        tool_name = serialized.get(
            "name",
            "unknown"
        )

        print(
            f"[Callback] Tool开始 | "
            f"tool={tool_name} | "
            f"input={input_str}"
        )

    # ========================================================
    # Tool 成功结束
    # ========================================================

    def on_tool_end(
        self,
        output,
        *,
        run_id,
        parent_run_id=None,
        **kwargs
    ):
        start_time = self.start_times.pop(
            str(run_id),
            None
        )

        elapsed = 0

        if start_time is not None:
            elapsed = time.time() - start_time

        print(
            f"[Callback] Tool结束 | "
            f"耗时={elapsed:.2f}s"
        )

    # ========================================================
    # Tool 异常
    # ========================================================

    def on_tool_error(
        self,
        error,
        *,
        run_id,
        parent_run_id=None,
        **kwargs
    ):
        start_time = self.start_times.pop(
            str(run_id),
            None
        )

        elapsed = 0

        if start_time is not None:
            elapsed = time.time() - start_time

        print(
            f"[Callback] Tool异常 | "
            f"耗时={elapsed:.2f}s | "
            f"error={error}"
        )