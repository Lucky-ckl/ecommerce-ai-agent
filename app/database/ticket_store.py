# ============================================================
# app/database/ticket_store.py
# 人工客服工单
#
# 当 Agent 答不上来、或用户明确要求人工时，
# 生成一张工单，交给真人客服跟进。
# ============================================================

import uuid
from datetime import datetime

from app.database.db import get_connection
from app.utils.logger import logger


def init_tickets_table():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id    TEXT PRIMARY KEY,
            session_id   TEXT,
            user_message TEXT NOT NULL,
            reason       TEXT,
            status       TEXT NOT NULL,
            created_at   TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_ticket(
    session_id,
    user_message,
    reason=None
):

    ticket_id = "T" + uuid.uuid4().hex[:8].upper()

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets
        (ticket_id, session_id, user_message, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            session_id,
            user_message,
            reason,
            "pending",
            created_at
        )
    )

    conn.commit()
    conn.close()

    logger.info(
        f"创建人工工单 | "
        f"ticket={ticket_id} | "
        f"session={session_id}"
    )

    return {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "user_message": user_message,
        "reason": reason,
        "status": "pending",
        "created_at": created_at
    }


def list_tickets(limit=50):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id, session_id, user_message, reason, status, created_at
        FROM tickets
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    conn.close()

    tickets = []

    for row in rows:

        tickets.append(
            {
                "ticket_id": row[0],
                "session_id": row[1],
                "user_message": row[2],
                "reason": row[3],
                "status": row[4],
                "created_at": row[5]
            }
        )

    return tickets
