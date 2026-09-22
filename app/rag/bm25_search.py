# ============================================================
# app/rag/bm25_search.py
# ============================================================

import jieba
from rank_bm25 import BM25Okapi

from app.rag.retriever import collection


# ============================================================
# 1. 中文分词
# ============================================================

def tokenize(text: str) -> list[str]:
    """
    将中文文本切分成词。

    例如：
    "日本商品可以申请退货"
    ↓
    ["日本", "商品", "可以", "申请", "退货"]
    """

    return list(jieba.cut(text))


# ============================================================
# 2. 从 Chroma 获取全部知识
# ============================================================

def load_documents():

    results = collection.get(
        include=["documents", "metadatas"]
    )

    documents = results["documents"]
    metadatas = results["metadatas"]
    ids = results["ids"]

    print("========== RAG知识库检查 ==========")
    print("知识数量：", len(documents))
    print("IDs：", ids)
    print("===================================")

    return ids, documents, metadatas

# ============================================================
# 3. BM25 检索
# ============================================================

def bm25_search(
    query: str,
    k: int = 3
):
    """
    使用 BM25 对知识库进行关键词检索。

    query ：用户问题
    k     ：最多返回多少条
    """

    # --------------------------------------------------------
    # 读取知识
    # --------------------------------------------------------

    ids, documents, metadatas = load_documents()


    # --------------------------------------------------------
    # 对所有文档进行分词
    # --------------------------------------------------------

    tokenized_documents = [
        tokenize(document)
        for document in documents
    ]


    # --------------------------------------------------------
    # 创建 BM25
    # --------------------------------------------------------

    bm25 = BM25Okapi(
        tokenized_documents
    )


    # --------------------------------------------------------
    # 对用户问题进行分词
    # --------------------------------------------------------

    tokenized_query = tokenize(query)


    # --------------------------------------------------------
    # 计算每个文档的 BM25 分数
    # --------------------------------------------------------

    scores = bm25.get_scores(
        tokenized_query
    )


    # --------------------------------------------------------
    # 按分数从高到低排序
    # --------------------------------------------------------

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )


    # --------------------------------------------------------
    # 取 Top-K
    # --------------------------------------------------------

    results = []

    for index in ranked_indexes[:k]:

        results.append({
            "id": ids[index],
            "text": documents[index],
            "score": float(scores[index]),
            "metadata": metadatas[index]
        })


    return results