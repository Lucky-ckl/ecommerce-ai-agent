# ============================================================
# app/rag/knowledge.py
# 知识库构建 + 删除
# ============================================================

import json
from pathlib import Path

from app.rag.chunker import split_text
from app.rag.retriever import add_knowledge, collection


# ============================================================
# 1. 知识文件路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

KNOWLEDGE_FILE = (
    BASE_DIR
    / "data"
    / "knowledge"
    / "ecommerce_knowledge.json"
)


# ============================================================
# 2. 读取原始知识
# ============================================================

def load_knowledge():

    with open(
        KNOWLEDGE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# 3. 构建知识库
# ============================================================

def build_knowledge_base():

    knowledge = load_knowledge()

    documents = []
    ids = []
    metadatas = []


    # ========================================================
    # 遍历每一条原始知识
    # ========================================================

    for item in knowledge:

        original_id = item["id"]
        text = item["text"]


        # ====================================================
        # 3.1 Chunk 切分
        # ====================================================

        chunks = split_text(
            text,
            chunk_size=500,
            overlap=50
        )


        # ====================================================
        # 3.2 给每个 Chunk 建立数据
        # ====================================================

        for index, chunk in enumerate(chunks):

            chunk_id = f"{original_id}_chunk_{index}"

            documents.append(chunk)

            ids.append(chunk_id)

            metadatas.append({
                "source_id": original_id,
                "chunk_index": index,
                "category": item.get(
                    "category",
                    "未知"
                ),
                "country": item.get(
                    "country",
                    "未知"
                )
            })


    # ========================================================
    # 4. 写入 Chroma
    # ========================================================

    add_knowledge(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )


    # ========================================================
    # 5. 返回本次导入数量
    # ========================================================

    return len(documents)


# ============================================================
# 6. 删除一条原始知识
# ============================================================

def delete_knowledge(source_id):

    # --------------------------------------------------------
    # 根据 metadata 中的 source_id 删除对应的所有 Chunk
    # --------------------------------------------------------

    result = collection.get(
        where={
            "source_id": source_id
        }
    )

    ids = result.get("ids", [])


    # --------------------------------------------------------
    # 没找到对应知识
    # --------------------------------------------------------

    if not ids:
        return {
            "status": "not_found",
            "source_id": source_id,
            "deleted": 0
        }


    # --------------------------------------------------------
    # 删除所有属于该知识的 Chunk
    # --------------------------------------------------------

    collection.delete(
        ids=ids
    )

    
    return {
        "status": "success",
        "source_id": source_id,
        "deleted": len(ids)
    }