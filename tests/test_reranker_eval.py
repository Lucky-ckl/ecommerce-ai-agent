# ============================================================
# tests/test_reranker_eval.py
# Rerank 评估测试
# ============================================================

from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank


# ============================================================
# 1. 评估集
#
# query：用户问题
# expected_id：理论上最相关的知识
# ============================================================

test_cases = [
    {
        "query": "日本退货审核通过后多久退款到账？",
        "expected_id": "refund_policy_001_chunk_0"
    },
    {
        "query": "日本消费者签收商品后几天可以退货？",
        "expected_id": "return_policy_001_chunk_0"
    },
    {
        "query": "如果商品有质量问题，退货运费谁承担？",
        "expected_id": "return_policy_002_chunk_0"
    }
]


# ============================================================
# 2. 评估参数
# ============================================================

retrieval_k = 4
rerank_k = 3

hit_at_1 = 0
hit_at_3 = 0


# ============================================================
# 3. 开始测试
# ============================================================

for test_index, case in enumerate(test_cases, start=1):

    query = case["query"]
    expected_id = case["expected_id"]

    print()
    print("=" * 60)
    print(f"测试 {test_index}")
    print(f"问题：{query}")
    print(f"正确知识：{expected_id}")
    print("=" * 60)


    # ========================================================
    # 3.1 Hybrid Search
    # ========================================================

    candidates = hybrid_search(
        query,
        k=retrieval_k
    )

    candidate_ids = [
        item["id"]
        for item in candidates
    ]

    print()
    print("----- Hybrid Search -----")

    for index, item in enumerate(
        candidates,
        start=1
    ):
        print(
            f"{index}. "
            f"{item['id']} "
            f"(Hybrid={item['hybrid_score']:.4f})"
        )


    # ========================================================
    # 3.2 检查正确知识有没有被召回
    # ========================================================

    if expected_id not in candidate_ids:

        print()
        print("⚠️ 召回失败：正确知识没有进入候选集")
        print("Rerank 无法修复这个问题")

        continue


    # ========================================================
    # 3.3 Cross-Encoder Rerank
    # ========================================================

    results = rerank(
        query,
        candidates,
        top_k=rerank_k
    )

    rerank_ids = [
        item["id"]
        for item in results
    ]

    print()
    print("----- Cross-Encoder Rerank -----")

    for index, item in enumerate(
        results,
        start=1
    ):
        print(
            f"{index}. "
            f"{item['id']} "
            f"(Rerank={item['rerank_score']:.4f})"
        )


    # ========================================================
    # 3.4 Hit@1
    # ========================================================

    if (
        len(rerank_ids) >= 1
        and rerank_ids[0] == expected_id
    ):
        hit_at_1 += 1
        print()
        print("✅ Hit@1：命中")
    else:
        print()
        print("❌ Hit@1：未命中")


    # ========================================================
    # 3.5 Hit@3
    # ========================================================

    if expected_id in rerank_ids[:3]:
        hit_at_3 += 1
        print("✅ Hit@3：命中")
    else:
        print("❌ Hit@3：未命中")


# ============================================================
# 4. 计算最终指标
# ============================================================

total = len(test_cases)

hit_at_1_rate = hit_at_1 / total
hit_at_3_rate = hit_at_3 / total


# ============================================================
# 5. 输出评估结果
# ============================================================

print()
print()
print("=" * 60)
print("最终 Rerank 评估结果")
print("=" * 60)

print(
    f"Hit@1："
    f"{hit_at_1}/{total} "
    f"= {hit_at_1_rate:.2%}"
)

print(
    f"Hit@3："
    f"{hit_at_3}/{total} "
    f"= {hit_at_3_rate:.2%}"
)