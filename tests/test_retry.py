# ============================================================
# tests/test_retry.py
# Retry / Backoff 故障注入测试
# ============================================================

from pydantic import BaseModel

import app.agent.registry as registry
from app.agent.result import success


# ============================================================
# 1. 测试参数模型
# ============================================================

class RetryTestArgs(BaseModel):
    value: int


# ============================================================
# 2. 故障注入 Tool
#
# 第1次：Timeout
# 第2次：Timeout
# 第3次：成功
# ============================================================

call_count = 0


def retry_test_tool(value: int):

    global call_count

    call_count += 1

    print(f"\nTool实际执行次数：{call_count}")

    if call_count <= 2:
        raise TimeoutError("模拟网络超时")

    return success(
        {
            "value": value,
            "message": "第3次执行成功"
        }
    )


# ============================================================
# 3. 临时注册测试 Tool
# ============================================================

# 用装饰器注册（等价于业务 Tool 的注册方式）
registry.tool(
    "retry_test_tool",
    "用于测试 Retry 的临时 Tool"
)(retry_test_tool)


# ============================================================
# 4. 替换 sleep
#
# 不真正等待 1 秒、2 秒
# 同时记录 Backoff 延迟
# ============================================================

sleep_delays = []


def fake_sleep(seconds):
    sleep_delays.append(seconds)
    print(f"Backoff等待：{seconds} 秒")


registry.time.sleep = fake_sleep


# ============================================================
# 5. 执行 Tool
# ============================================================

print("\n===== 开始 Retry 测试 =====")

result = registry.execute_tool(
    "retry_test_tool",
    {"value": 123}
)

print("\n===== 最终结果 =====")
print(result)


# ============================================================
# 6. 验证 Retry
# ============================================================

assert call_count == 3


# ============================================================
# 7. 验证 Backoff
# ============================================================

assert sleep_delays == [1, 2]


# ============================================================
# 8. 验证最终成功
# ============================================================

assert result["status"] == "success"

assert result["data"]["value"] == 123

assert result["data"]["message"] == "第3次执行成功"


# ============================================================
# 9. 清理测试环境
# ============================================================

registry.TOOLS.pop("retry_test_tool", None)

print("\n===== Retry / Backoff 测试通过 =====")