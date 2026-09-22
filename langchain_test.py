# ==========================================
# LangChain + IKunCode 最小测试
# ==========================================

import os
from langchain_openai import ChatOpenAI


# ==========================================
# 1. 创建 LangChain Chat Model
# ==========================================

model = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-5.6-terra"),
    api_key=os.getenv("IKUNCODE_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.ikuncode.cc/v1")
)


# ==========================================
# 2. 调用模型
# ==========================================

response = model.invoke(
    "请用一句话介绍你自己。"
)


# ==========================================
# 3. 查看结果
# ==========================================

print("完整返回结果：")
print(response)

print("\nAI回答：")
print(response.content)