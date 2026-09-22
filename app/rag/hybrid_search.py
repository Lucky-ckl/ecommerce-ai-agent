# ============================================================
# app/rag/hybrid_search.py
# ============================================================

from app.rag.retriever import collection
from app.rag.bm25_search import load_documents, tokenize
from rank_bm25 import BM25Okapi


# ============================================================
# 1. Min-Max 归一化
# ============================================================

def min_max_normalize(scores: list[float]) -> list[float]:
    """
    将一组分数转换到 0 ~ 1。

    最小值 → 0
    最大值 → 1
    """

    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    # 所有分数相同，无法进行正常归一化
    if max_score == min_score:
        return [1.0 for _ in scores]

    return [
        (score - min_score) / (max_score - min_score)
        for score in scores
    ]


# ============================================================
# 2. 向量检索
# ============================================================

def vector_search(
    query: str,
    k: int = 5
):
    """
    使用 Chroma 进行向量检索。
    """

    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]

    return [
        {
            "id": chunk_id,
            "text": document,
            "distance": distance,
            "metadata": metadata
        }
        for chunk_id, document, distance, metadata
        in zip(
            ids,
            documents,
            distances,
            metadatas
        )
    ]


# ============================================================
# 3. BM25 检索
# ============================================================

# ============================================================
# 3. BM25 检索
# ============================================================

def bm25_search_all(
    query: str,
    k: int = 5
):
    """
    使用 BM25 检索知识库。

    如果知识库为空：
    直接返回 []，避免 BM25Okapi([]) 导致 division by zero。
    """

    ids, documents, metadatas = load_documents()

    # --------------------------------------------------------
    # 3.1 知识库为空
    # --------------------------------------------------------

    if not documents:
        return []

    # --------------------------------------------------------
    # 3.2 文档 Token 化
    # --------------------------------------------------------

    tokenized_documents = [
        tokenize(document)
        for document in documents
    ]

    # --------------------------------------------------------
    # 3.3 Token 化后没有有效文档
    # --------------------------------------------------------

    if not tokenized_documents:
        return []

    # --------------------------------------------------------
    # 3.4 创建 BM25
    # --------------------------------------------------------

    bm25 = BM25Okapi(
        tokenized_documents
    )

    # --------------------------------------------------------
    # 3.5 查询词 Token 化
    # --------------------------------------------------------

    tokenized_query = tokenize(query)

    # 如果查询没有有效 Token，也直接返回
    if not tokenized_query:
        return []

    # --------------------------------------------------------
    # 3.6 计算 BM25 分数
    # --------------------------------------------------------

    scores = bm25.get_scores(
        tokenized_query
    )

    # --------------------------------------------------------
    # 3.7 按分数从高到低排序
    # --------------------------------------------------------

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    # --------------------------------------------------------
    # 3.8 构造结果
    # --------------------------------------------------------

    results = []

    for index in ranked_indexes[:k]:

        results.append({
            "id": ids[index],
            "text": documents[index],
            "bm25_score": float(scores[index]),
            "metadata": metadatas[index]
        })

    return results

# ============================================================
# 4. Hybrid Search
# ============================================================

def hybrid_search(
    query: str,
    k: int = 5,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4
):
    """
    Vector Search + BM25

    最终分数：

    vector_similarity * vector_weight
    +
    bm25_normalized * bm25_weight
    """

    # --------------------------------------------------------
    # 4.1 分别进行两路检索
    # --------------------------------------------------------

    vector_results = vector_search(
        query,
        k=k
    )

    bm25_results = bm25_search_all(
        query,
        k=k
    )


    # --------------------------------------------------------
    # 4.2 Vector distance → similarity
    # --------------------------------------------------------

    vector_distances = [
        item["distance"]
        for item in vector_results
    ]

    # distance 越小越相似
    # 所以先归一化，再反转
    normalized_distances = min_max_normalize(
        vector_distances
    )

    vector_similarities = [
        1 - score
        for score in normalized_distances
    ]


    # --------------------------------------------------------
    # 4.3 BM25 score → 0~1
    # --------------------------------------------------------

    bm25_scores = [
        item["bm25_score"]
        for item in bm25_results
    ]

    normalized_bm25_scores = min_max_normalize(
        bm25_scores
    )


    # --------------------------------------------------------
    # 4.4 建立统一结果表
    # --------------------------------------------------------

    merged = {}


    # --------------------------------------------------------
    # 加入 Vector Search 结果
    # --------------------------------------------------------

    for item, similarity in zip(
        vector_results,
        vector_similarities
    ):

        merged[item["id"]] = {
            "id": item["id"],
            "text": item["text"],
            "metadata": item["metadata"],
            "vector_score": similarity,
            "bm25_score": 0.0
        }


    # --------------------------------------------------------
    # 加入 BM25 结果
    # --------------------------------------------------------

    for item, score in zip(
        bm25_results,
        normalized_bm25_scores
    ):

        if item["id"] not in merged:

            merged[item["id"]] = {
                "id": item["id"],
                "text": item["text"],
                "metadata": item["metadata"],
                "vector_score": 0.0,
                "bm25_score": score
            }

        else:

            merged[item["id"]]["bm25_score"] = score


    # --------------------------------------------------------
    # 4.5 计算最终 Hybrid Score
    # --------------------------------------------------------

    for item in merged.values():

        item["hybrid_score"] = (
            item["vector_score"] * vector_weight
            +
            item["bm25_score"] * bm25_weight
        )


    # --------------------------------------------------------
    # 4.6 最终排序
    # --------------------------------------------------------

    final_results = sorted(
        merged.values(),
        key=lambda item: item["hybrid_score"],
        reverse=True
    )


    # --------------------------------------------------------
    # 4.7 返回 Top-K
    # --------------------------------------------------------

    return final_results[:k]