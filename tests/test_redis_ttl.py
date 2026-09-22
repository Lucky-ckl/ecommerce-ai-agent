from app.memory.redis_state import (
    create_state,
    redis_client,
    build_state_key
)


user_id = "ttl_test_user"


create_state(user_id)


key = build_state_key(user_id)


ttl = redis_client.ttl(key)


print(
    "Redis TTL:",
    ttl
)