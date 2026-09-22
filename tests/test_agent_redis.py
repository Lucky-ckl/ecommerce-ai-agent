from app.agent.agent import agent
from app.memory.redis_state import clear_pending_action




user_id = "user_001"
clear_pending_action(
    user_id
)

print("===== 第一次请求：取消订单 =====")


result = agent(
    user_id,
    "帮我取消订单1001"
)


print(result)

print("===== 第二次请求：确认取消 =====")


result = agent(
    user_id,
    "确认"
)


print(result)

from app.memory.redis_state import get_state


print(
    "Redis状态:",
    get_state(user_id)
)