# ============================================================
# app/rag/langchain_retriever.py
# 将现有 Hybrid Search + Cross-Encoder 封装成 LangChain Retriever
# ============================================================

from typing import List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.rag.hybrid_search import hybrid_search
from app.rag.reranker import rerank


# ============================================================
# LangChain Retriever
# ============================================================

class EcommerceRetriever(BaseRetriever):

    # --------------------------------------------------------
    # LangChain 会调用这个方法进行检索
    #
    # 输入：
    #   query = 用户的问题
    #
    # 输出：
    #   List[Document]
    # --------------------------------------------------------

    def _get_relevant_documents(self, query: str) -> List[Document]:

        # ====================================================
        # 1. 第一阶段：Hybrid Search
        # ====================================================
        #
        # Chroma 向量检索
        # +
        # BM25 关键词检索
        #
        # 这里先召回 5 条候选知识
        # ====================================================

        candidates = hybrid_search(
            query,
            k=5
        )

        if not candidates:
            return []


        # ====================================================
        # 2. 第二阶段：Cross-Encoder Reranker
        # ====================================================
        #
        # 对召回的候选知识重新计算相关性
        # 最终保留 3 条
        # ====================================================

        results = rerank(
            query,
            candidates,
            top_k=3
        )

        if not results:
            return []


        # ====================================================
        # 3. 转换成 LangChain Document
        # ====================================================

        documents = []

        for item in results:

            documents.append(
                Document(
                    page_content=item["text"],
                    metadata={
                        "id": item["id"],
                        "rerank_score": item["rerank_score"],
                        "hybrid_score": item.get(
                            "hybrid_score",
                            0.0
                        ),
                        "category": item.get(
                            "metadata",
                            {}
                        ).get(
                            "category",
                            "未知"
                        ),
                        "country": item.get(
                            "metadata",
                            {}
                        ).get(
                            "country",
                            "未知"
                        )
                    }
                )
            )

        return documents


# ============================================================
# 创建 Retriever 实例
# ============================================================

ecommerce_retriever = EcommerceRetriever()