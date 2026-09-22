# ============================================================
# tests/test_knowledge_delete.py
# ============================================================

from app.rag.knowledge import delete_knowledge
from app.rag.retriever import search_knowledge


# ============================================================
# 1. 删除一条知识
# ============================================================

result = delete_knowledge(
    "return_policy_003"
)

print("===== 删除结果 =====")
print(result)


# ============================================================
# 2. 删除后进行检索
# ============================================================

results = search_knowledge(
    "商品已经使用了还能不能无理由退货？",
    k=3,
    threshold=0.8
)

print()
print("===== 删除后的检索结果 =====")

for item in results:

    print(f"距离：{item['distance']}")
    print(f"内容：{item['text']}")
    print()
