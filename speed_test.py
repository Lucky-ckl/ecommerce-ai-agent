import time

start = time.time()

print("1. 开始")

from langchain_openai import ChatOpenAI
print(f"2. LangChain：{time.time() - start:.2f} 秒")

from app.tools.order import get_order_record
print(f"3. 导入 order.py：{time.time() - start:.2f} 秒")

from app.tools.order import cancel_order
print(f"4. 导入 cancel_order：{time.time() - start:.2f} 秒")

print("5. 全部完成")