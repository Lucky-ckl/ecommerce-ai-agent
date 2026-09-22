# ============================================================
# tests/test_knowledge.py
# ============================================================

from app.rag.knowledge import build_knowledge_base
from app.rag.retriever import collection


# ============================================================
# 1. 清空当前测试知识库
# ============================================================

existing = collection.get()

if existing["ids"]:
    collection.delete(
        ids=existing["ids"]
    )


# ============================================================
# 2. 构建知识库
# ============================================================

count = build_knowledge_base()

print("===== 知识库构建完成 =====")
print(f"本次导入知识数量：{count}")


# ============================================================
# 3. 从 Chroma 读取所有 Chunk
# ============================================================

results = collection.get(
    include=["documents", "metadatas"]
)

ids = results["ids"]
documents = results["documents"]
metadatas = results["metadatas"]


# ============================================================
# 4. 打印所有 Chunk
# ============================================================

print()
print("===== Chroma 中的 Chunk =====")

for chunk_id, document, metadata in zip(
    ids,
    documents,
    metadatas
):
    print("--------------------------------")
    print(f"Chunk ID：{chunk_id}")
    print(f"内容：{document}")
    print(f"Metadata：{metadata}")