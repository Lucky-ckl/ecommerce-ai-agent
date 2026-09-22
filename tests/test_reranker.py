# ============================================================
# tests/test_reranker.py
# ============================================================

from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank


# ============================================================
# 1. 测试问题
# ============================================================

query = "日本退货审核通过后多久退款到账？"


# ============================================================
# 2. Hybrid Search
# ============================================================

candidates = hybrid_search(
    query,
    k=5
)


# ============================================================
# 3. 输出 Hybrid Search 排名
# ============================================================

print("===== 1. Hybrid Search 排名 =====")

for index, item in enumerate(candidates, start=1):

    print("--------------------------------")

    print(f"排名：{index}")
    print(f"ID：{item['id']}")
    print(f"Hybrid Score：{item['hybrid_score']:.4f}")
    print(f"内容：{item['text']}")


# ============================================================
# 4. Cross-Encoder Rerank
# ============================================================

results = rerank(
    query,
    candidates,
    top_k=3
)


# ============================================================
# 5. 输出 Rerank 最终排名
# ============================================================

print()
print()

print("===== 2. Cross-Encoder Rerank 最终排名 =====")

for index, item in enumerate(results, start=1):

    print("--------------------------------")

    print(f"排名：{index}")
    print(f"ID：{item['id']}")

    print(
        f"Hybrid Score："
        f"{item.get('hybrid_score', 0):.4f}"
    )

    print(
        f"Rerank Score："
        f"{item['rerank_score']:.4f}"
    )

    print(f"内容：{item['text']}")