# ==========================================
# LangChain Prompt + Model 测试
# ==========================================

import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


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
# 2. 创建 Prompt 模板
# ==========================================

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个专业的跨境电商 AI 客服。"
    ),
    (
        "human",
        "{question}"
    )
])


# ==========================================
# 3. 把 Prompt 和 Model 连接起来
# ==========================================

chain = prompt | model


# ==========================================
# 4. 调用 Chain
# ==========================================

response = chain.invoke({
    "question": "订单1001现在是什么状态？"
})


# ==========================================
# 5. 查看结果
# ==========================================

print("完整返回结果：")
print(response)

print("\nAI回答：")
print(response.content)