# ============================================================
# app/rag/retriever.py
# ============================================================

import chromadb

from app.config import BASE_DIR


# ============================================================
# 1. 初始化 Chroma
# ============================================================

RAG_DB_PATH = BASE_DIR / "data" / "rag_chroma"

client = chromadb.PersistentClient(
    path=str(RAG_DB_PATH)
)

collection = client.get_or_create_collection(
    name="ecommerce_knowledge"
)


# ============================================================
# 2. 添加知识
# ============================================================

def add_knowledge(documents, ids, metadatas):
    """
    documents  : 知识内容
    ids        : 每条知识的唯一 ID
    metadatas  : 每条知识的附加信息
    """

    collection.upsert(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )


# ============================================================
# 3. 搜索知识
# ============================================================

def search_knowledge(
    question,
    k=3,
    threshold=0.8,
    country=None,
    category=None
):
    """
    question  : 用户问题
    k         : 最多返回多少条
    threshold : 距离阈值，越小越相似
    country   : 国家过滤，例如 "日本"
    category  : 知识类别过滤，例如 "退货政策"
    """

    # ========================================================
    # 构造 Metadata 过滤条件
    # ========================================================

    conditions = []

    if country is not None:
        conditions.append({
            "country": {
                "$eq": country
            }
        })

    if category is not None:
        conditions.append({
            "category": {
                "$eq": category
            }
        })

    where = None

    if len(conditions) == 1:
        where = conditions[0]

    elif len(conditions) > 1:
        where = {
            "$and": conditions
        }


    # ========================================================
    # 2. 执行向量检索
    # ========================================================

    query_args = {
        "query_texts": [question],
        "n_results": k
    }

    # 有过滤条件才传 where
    if where:
        query_args["where"] = where

    results = collection.query(**query_args)


    # ========================================================
    # 3. 取出检索结果
    # ========================================================

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]


    # ========================================================
    # 4. Threshold 过滤
    # ========================================================

    relevant_documents = []

    for document, distance, metadata in zip(
        documents,
        distances,
        metadatas
    ):

        if distance <= threshold:

            relevant_documents.append({
                "text": document,
                "distance": distance,
                "metadata": metadata
            })

    return relevant_documents

# ============================================================
# 4. 删除知识
# ============================================================

def delete_knowledge(knowledge_id):
    collection.delete(
        ids=[knowledge_id]
    )

    return {
        "status": "success",
        "deleted_id": knowledge_id
    }