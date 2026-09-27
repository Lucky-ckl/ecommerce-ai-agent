# ============================================================
# app/database/session_store.py
# 会话持久化存储
#
# 设计：
# Redis  = 热缓存，只保留最近 5 轮，给模型当上下文（30 分钟 TTL）
# SQLite = 冷存储，保留全部历史，用于回看和切换会话
#
# 以前只有 Redis，导致"新建会话 = 清空历史"，旧会话再也找不回来。
# ============================================================

import uuid
from datetime import datetime

from app.database.db import get_connection
from app.utils.logger import logger


# ============================================================
# 1. 建表
# ============================================================

def init_session_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_session
        ON messages(session_id)
    """)

    conn.commit()
    conn.close()


# ============================================================
# 2. 工具函数
# ============================================================

def now():

    return datetime.now().isoformat(
        timespec="seconds"
    )


# ============================================================
# 3. 新建会话
# ============================================================

def create_session(title="新会话"):

    session_id = uuid.uuid4().hex[:12]

    current = now()

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sessions
        (session_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            session_id,
            title,
            current,
            current
        )
    )

    conn.commit()
    conn.close()

    logger.info(
        f"新建会话 | session_id={session_id}"
    )

    return session_id


# ============================================================
# 4. 列出所有会话
# ============================================================

def list_sessions(limit=50):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            s.session_id,
            s.title,
            s.created_at,
            s.updated_at,
            COUNT(m.id) AS message_count
        FROM sessions s
        LEFT JOIN messages m
            ON m.session_id = s.session_id
        GROUP BY s.session_id
        ORDER BY s.updated_at DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    conn.close()

    sessions = []

    for row in rows:

        sessions.append(
            {
                "session_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": row[4]
            }
        )

    return sessions


# ============================================================
# 5. 追加一条消息
#
# 同时维护会话标题：
# 第一条用户消息的前 20 个字作为会话标题
# ============================================================

def append_message(
    session_id,
    role,
    content
):

    current = now()

    conn = get_connection()

    cursor = conn.cursor()

    # --------------------------------------------------------
    # 会话不存在时自动创建（兼容旧数据）
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT title
        FROM sessions
        WHERE session_id = ?
        """,
        (session_id,)
    )

    row = cursor.fetchone()

    if row is None:

        cursor.execute(
            """
            INSERT INTO sessions
            (session_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                "新会话",
                current,
                current
            )
        )

        title = "新会话"

    else:

        title = row[0]

    # --------------------------------------------------------
    # 写入消息
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO messages
        (session_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            current
        )
    )

    # --------------------------------------------------------
    # 用第一条用户消息作为标题
    # --------------------------------------------------------

    if role == "user" and title == "新会话":

        new_title = content[:20]

        cursor.execute(
            """
            UPDATE sessions
            SET title = ?
            WHERE session_id = ?
            """,
            (
                new_title,
                session_id
            )
        )

    cursor.execute(
        """
        UPDATE sessions
        SET updated_at = ?
        WHERE session_id = ?
        """,
        (
            current,
            session_id
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# 6. 读取某个会话的全部消息
# ============================================================

def get_session_messages(session_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    messages = []

    for row in rows:

        messages.append(
            {
                "role": row[0],
                "content": row[1],
                "created_at": row[2]
            }
        )

    return messages


# ============================================================
# 7. 删除会话
# ============================================================

def delete_session(session_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        """,
        (session_id,)
    )

    cursor.execute(
        """
        DELETE FROM sessions
        WHERE session_id = ?
        """,
        (session_id,)
    )

    conn.commit()
    conn.close()

    logger.info(
        f"删除会话 | session_id={session_id}"
    )
