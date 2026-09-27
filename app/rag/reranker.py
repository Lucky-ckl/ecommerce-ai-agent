# ============================================================
# app/rag/reranker.py
# ============================================================

# ============================================================
# 1. 加载本地 Cross-Encoder Reranker
# ============================================================

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

# 延迟加载：
# 以前这里在模块导入时就 new CrossEncoder，会触发模型下载。
# 结果是只要 import 到 registry（订单查询也会），整个项目就启动不了。
# 改成第一次真正需要重排时才加载。
_reranker_model = None


def get_reranker_model():
    """
    获取 Reranker 模型（首次调用时才加载）。
    """

    global _reranker_model

    if _reranker_model is None:

        # 在这里才 import，避免仅需订单查询时也拖进整套 ML 依赖
        from sentence_transformers import CrossEncoder

        _reranker_model = CrossEncoder(
            MODEL_NAME
        )

    return _reranker_model


# ============================================================
# 2. Rerank
# ============================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 3
) -> list[dict]:
    """
    使用 Cross-Encoder 对候选文档重新排序。

    参数：

    query:
        用户问题

    candidates:
        Hybrid Search 返回的候选文档

    top_k:
        最终保留多少条

    返回：

        按 Cross-Encoder 相关性分数
        从高到低排序后的结果
    """

    # --------------------------------------------------------
    # 没有候选文档
    # --------------------------------------------------------

    if not candidates:
        return []


    # ========================================================
    # 3. 构造 Query + Document 对
    # ========================================================

    pairs = []

    for candidate in candidates:

        pairs.append(
            (
                query,
                candidate["text"]
            )
        )


    # ========================================================
    # 4. Cross-Encoder 推理
    # ========================================================

    scores = get_reranker_model().predict(
        pairs
    )


    # ========================================================
    # 5. 将分数写回候选结果
    # ========================================================

    reranked_candidates = []

    for candidate, score in zip(
        candidates,
        scores
    ):

        item = candidate.copy()

        item["rerank_score"] = float(score)

        reranked_candidates.append(
            item
        )


    # ========================================================
    # 6. 按 Rerank Score 从高到低排序
    # ========================================================

    reranked_candidates.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )


    # ========================================================
    # 7. 返回最终 Top-K
    # ========================================================

    return reranked_candidates[:top_k]