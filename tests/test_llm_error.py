# ============================================================
# tests/test_llm_error.py
# 测试 LLM 请求异常处理
# ============================================================

import app.agent.agent as agent_module


# ============================================================
# 1. 创建一个假的 LLM Client
# ============================================================

class FakeCompletions:

    def create(self, **kwargs):

        print("\n模拟 LLM 请求失败")

        raise TimeoutError(
            "模拟 LLM 网络超时"
        )


class FakeChat:

    def __init__(self):

        self.completions = FakeCompletions()


class FakeClient:

    def __init__(self):

        self.chat = FakeChat()


# ============================================================
# 2. 替换真实 LLM Client
# ============================================================

agent_module.client = FakeClient()


# ============================================================
# 3. 执行 Agent
# ============================================================

print("\n===== 开始 LLM 异常测试 =====")

result = agent_module.agent(
    "llm_error_test_user",
    "查询订单1001"
)


# ============================================================
# 4. 查看结果
# ============================================================

print("\n===== 最终结果 =====")

print(result)


# ============================================================
# 5. 验证
# ============================================================

assert result["status"] == "error"

assert result["error"]["type"] == "system"

assert (
    result["error"]["message"]
    == "LLM服务暂时不可用，请稍后再试。"
)


print("\n===== LLM 异常测试通过 =====")