# ============================================================
# app/tools/knowledge.py
# RAG Tool
#
# Agent
#   ↓
# search_knowledge
#   ↓
# LangChain RAG Chain
#   ↓
# Retriever
#   ↓
# Hybrid Search
#   ↓
# Cross-Encoder Reranker
#   ↓
# LLM
#   ↓
# 最终知识库答案
# ============================================================

from app.rag.rag_chain import ask_rag
from app.agent.result import success


# ============================================================
# RAG Tool
# ============================================================

def search_knowledge(
    question: str,
    k: int = 5,
    top_k: int = 3
):
    """
    Agent 使用的知识库查询 Tool。

    k / top_k 保留是为了兼容原来的 Tool 接口。
    实际检索参数由 LangChain Retriever 内部控制。
    """

    # ========================================================
    # 1. 调用 LangChain RAG Chain
    # ========================================================

    answer = ask_rag(question)

    # ========================================================
    # 2. 返回标准 Tool Result
    # ========================================================

    return success(
        data={
            "found": True,
            "answer": answer
        }
    )