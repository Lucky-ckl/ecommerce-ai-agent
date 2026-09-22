# ============================================================
# app/rag/rag_chain.py
# LangChain 标准 RAG Chain
#
# 流程：
#
# 用户问题
#     ↓
# LangChain Retriever
#     ↓
# Documents
#     ↓
# Prompt
#     ↓
# LLM
#     ↓
# 最终答案
# ============================================================

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.config import API_KEY, LLM_BASE_URL, LLM_MODEL
from app.rag.langchain_retriever import ecommerce_retriever


# ============================================================
# 1. 创建 LLM
# ============================================================

llm = ChatOpenAI(
    api_key=API_KEY,
    base_url=LLM_BASE_URL,
    model=LLM_MODEL,
    max_retries=0,
)


# ============================================================
# 2. 创建 RAG Prompt
# ============================================================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
你是跨境电商客服助手。

请严格根据提供的知识库内容回答用户问题。

要求：
1. 优先使用知识库中的信息。
2. 不要编造知识库中不存在的政策。
3. 如果知识库没有相关信息，明确告诉用户暂时无法确认。
4. 回答简洁、准确、符合客服场景。
"""
        ),
        (
            "human",
            """
知识库内容：

{context}

用户问题：

{question}
"""
        ),
    ]
)


# ============================================================
# 3. Document → 文本
# ============================================================

def format_docs(documents):

    return "\n\n".join(
        document.page_content
        for document in documents
    )


# ============================================================
# 4. 构建 LangChain RAG Chain
# ============================================================

rag_chain = (
    {
        "context": ecommerce_retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)


# ============================================================
# 5. 对外调用函数
# ============================================================

def ask_rag(question: str) -> str:

    return rag_chain.invoke(question)