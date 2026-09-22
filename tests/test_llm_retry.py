# ============================================================
# tests/test_llm_retry.py
# 测试 LLM Retry / Backoff
# ============================================================

import app.agent.agent as agent_module


# ============================================================
# 1. Fake LLM
# ============================================================

class FakeCompletions:

    def __init__(self):

        self.call_count = 0


    def create(self, **kwargs):

        self.call_count += 1

        print(
            f"\nLLM实际请求次数："
            f"{self.call_count}"
        )


        # 前两次模拟超时
        if self.call_count <= 2:

            raise TimeoutError(
                "模拟 LLM 网络超时"
            )


        # 第三次成功
        return FakeResponse()


# ============================================================
# 2. Fake Response
# ============================================================

class FakeMessage:

    def __init__(self):

        # 不调用 Tool
        self.tool_calls = None

        self.content = (
            "这是第3次LLM请求后返回的成功结果。"
        )


class FakeChoice:

    def __init__(self):

        self.message = FakeMessage()


class FakeResponse:

    def __init__(self):

        self.choices = [
            FakeChoice()
        ]


# ============================================================
# 3. Fake Chat
# ============================================================

class FakeChat:

    def __init__(self):

        self.completions = (
            FakeCompletions()
        )


# ============================================================
# 4. Fake Client
# ============================================================

class FakeClient:

    def __init__(self):

        self.chat = FakeChat()


# ============================================================
# 5. 替换真实 LLM Client
# ============================================================

fake_client = FakeClient()

agent_module.client = fake_client


# ============================================================
# 6. 替换 time.sleep
# ============================================================

sleep_delays = []


def fake_sleep(seconds):

    sleep_delays.append(seconds)

    print(
        f"LLM Backoff等待："
        f"{seconds} 秒"
    )


agent_module.time.sleep = fake_sleep


# ============================================================
# 7. 开始测试
# ============================================================

print(
    "\n===== 开始 LLM Retry 测试 ====="
)


result = agent_module.agent(
    "llm_retry_test_user",
    "你好"
)


# ============================================================
# 8. 输出最终结果
# ============================================================

print(
    "\n===== 最终结果 ====="
)

print(result)


# ============================================================
# 9. 验证
# ============================================================

# LLM 应该一共请求 3 次
assert (
    fake_client.chat.completions.call_count
    == 3
)


# Backoff 应该是 1秒、2秒
assert sleep_delays == [
    1,
    2
]


# 最终应该成功返回 LLM 内容
assert result == (
    "这是第3次LLM请求后返回的成功结果。"
)


print(
    "\n===== LLM Retry / Backoff 测试通过 ====="
)