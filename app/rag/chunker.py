# ============================================================
# app/rag/chunker.py
# ============================================================


# ============================================================
# 1. 文本切块
# ============================================================

def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    """
    将长文本切成多个 Chunk。

    参数：
    text        ：原始文本
    chunk_size  ：每个 Chunk 的最大长度
    overlap     ：相邻 Chunk 重叠的字符数

    返回：
    list[str]
    """

    # --------------------------------------------------------
    # 参数检查
    # --------------------------------------------------------

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")


    # --------------------------------------------------------
    # 开始切块
    # --------------------------------------------------------

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        # ----------------------------------------------------
        # 下一块从当前位置往回退 overlap
        # ----------------------------------------------------

        start = end - overlap


    return chunks