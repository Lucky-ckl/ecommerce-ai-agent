# ==========================================
# LangChain Agent + 项目真实订单 Tool
# ==========================================

import os

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

# 导入你项目原来的订单查询函数
from app.tools.order import get_order_record as query_order


# ==========================================
# 1. 创建 Chat Model
# ==========================================

model = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-5.6-terra"),
    api_key=os.getenv("IKUNCODE_API_KEY"),
    base_url=os.getenv(
        "LLM_BASE_URL",
        "https://api.ikuncode.cc/v1"
    )
)


# ==========================================
# 2. 把原项目函数包装成 LangChain Tool
# ==========================================

@tool
def get_order_record(order_id: str) -> dict:
    """
    根据订单ID查询真实订单信息。
    """

    # 调用你项目原来的业务函数
    return query_order(order_id)


# ==========================================
# 3. 创建 LangChain Agent
# ==========================================

agent = create_agent(
    model=model,
    tools=[get_order_record],
    system_prompt="""
你是一个跨境电商 AI 客服。

规则：
1. 用户询问具体订单时，必须调用 get_order_record。
2. 不允许自己编造订单信息。
3. Tool 返回什么，就根据 Tool 返回的数据回答。
"""
)


# ==========================================
# 4. 调用 Agent
# ==========================================

import time

start = time.time()

result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "帮我取消订单1001"
        }
    ]
})

print(f"\nAgent总耗时：{time.time() - start:.2f} 秒")


# ==========================================
# 5. 输出结果
# ==========================================

print("================================")
print("Agent完整返回：")
print(result)

print("\n================================")
print("最终AI回答：")
print(result["messages"][-1].content)