# ============================================================
# tests/test_hybrid_search.py
# ============================================================

from app.rag.hybrid_search import hybrid_search


# ============================================================
# 1. 测试订单号
# ============================================================

query = "RY20260913001"


results = hybrid_search(
    query,
    k=5
)


# ============================================================
# 2. 输出结果
# ============================================================

print("===== Hybrid Search 检索结果 =====")

for item in results:

    print("--------------------------------")

    print(f"ID：{item['id']}")

    print(f"Vector Score：{item['vector_score']:.4f}")

    print(f"BM25 Score：{item['bm25_score']:.4f}")

    print(f"Hybrid Score：{item['hybrid_score']:.4f}")

    print(f"内容：{item['text']}")

    print(f"Metadata：{item['metadata']}")