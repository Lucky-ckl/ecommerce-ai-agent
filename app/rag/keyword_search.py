# ============================================================
# app/rag/keyword_search.py
# ============================================================

from app.rag.retriever import collection


# ============================================================
# 1. 关键词检索
# ============================================================

def keyword_search(keyword: str):
    """
    根据关键词，查找知识库中直接包含该关键词的 Chunk。

    注意：
    这只是最简单的关键词匹配实验，
    不是正式的 BM25。
    """

    # --------------------------------------------------------
    # 读取 Chroma 中所有知识
    # --------------------------------------------------------

    results = collection.get(
        include=["documents", "metadatas"]
    )

    documents = results["documents"]
    metadatas = results["metadatas"]

    # --------------------------------------------------------
    # 查找包含关键词的文档
    # --------------------------------------------------------

    matched_documents = []

    for document, metadata in zip(
            documents,
            metadatas
    ):

        if keyword in document:
            matched_documents.append({
                "text": document,
                "metadata": metadata
            })

    return matched_documents