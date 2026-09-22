# ==============================
# tests/test_registry.py
# 测试 RAG 是否成功注册为 Tool
# ==============================

from app.agent.registry import (
    tools,
    build_tool_schema,
    execute_tool
)


# =========================================================
# 1. 查看当前有哪些 Tool
# =========================================================

print("===== 当前 Tool =====")

for tool_name in tools:
    print(tool_name)


# =========================================================
# 2. 查看 RAG Tool 的 Schema
# =========================================================

print("\n===== RAG Tool Schema =====")

schema = build_tool_schema(
    "search_knowledge"
)

print(schema)


# =========================================================
# 3. 模拟一次真正的 Tool 调用
# =========================================================

print("\n===== 执行 RAG Tool =====")

result = execute_tool(
    "search_knowledge",
    {
        "question": "日本买的商品几天可以退？"
    }
)

print(result)

# =========================================================
# 4. 测试 System Error
# =========================================================

# =========================================================
# 4. 测试 System Error
# =========================================================

from pydantic import BaseModel


# 临时 Tool 的参数模型
# 不使用 Test 开头，避免被 pytest 当成测试类
class MockSystemErrorArgs(BaseModel):
    message: str


# 故意制造系统异常的函数
# 不使用 test_ 开头，避免被 pytest 当成测试函数
def mock_system_error_tool(message: str):
    raise RuntimeError(message)


# 把临时 Tool 注册到 Registry
tools["test_system_error"] = {
    "function": mock_system_error_tool,
    "args_model": MockSystemErrorArgs,
    "description": "用于测试系统异常",
    "dangerous": False
}


print("\n===== 测试 System Error =====")

system_error_result = execute_tool(
    "test_system_error",
    {
        "message": "模拟数据库连接失败"
    }
)

print(system_error_result)


# 验证错误分类是否正确
assert system_error_result["status"] == "error"
assert system_error_result["error"]["type"] == "system"
assert system_error_result["error"]["code"] == "SYSTEM_ERROR"

print("System Error 测试通过")