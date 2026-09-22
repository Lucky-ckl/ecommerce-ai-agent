# ============================================================
# app/database/db.py
# ============================================================

import sqlite3

from app.config import DB_PATH


# ============================================================
# 1. 获取数据库连接
# ============================================================

def get_connection():

    # 确保 data 目录存在
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return sqlite3.connect(DB_PATH)


# ============================================================
# 2. 初始化数据库
# ============================================================

def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.executemany(
        """
        INSERT OR IGNORE INTO orders
        (order_id, user_id, product_name, status)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1001, 1, "Sony耳机", "已发货"),
            (1002, 1, "手机壳", "待付款"),
            (1003, 2, "机械键盘", "已完成")
        ]
    )

    conn.commit()
    conn.close()


# ============================================================
# 3. 查询订单
# ============================================================

def get_order_record(order_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT order_id, user_id, product_name, status
        FROM orders
        WHERE order_id = ?
        """,
        (order_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    return {
        "order_id": row[0],
        "user_id": row[1],
        "product_name": row[2],
        "status": row[3]
    }


# ============================================================
# 4. 取消订单
# ============================================================

def cancel_order_in_db(order_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE order_id = ?
        """,
        ("已取消", order_id)
    )

    conn.commit()

    conn.close()

# ============================================================
# 修改订单状态
# ============================================================

def update_order_status(order_id, status):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE order_id = ?
        """,
        (status, order_id)
    )

    # 获取 UPDATE 实际影响的行数
    affected_rows = cursor.rowcount

    conn.commit()
    conn.close()

    # 返回给上层业务 Tool
    return affected_rows


# ============================================================
# 5. 重置测试数据
# ============================================================

def reset_test_data():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("DELETE FROM orders")

    cursor.executemany(
        """
        INSERT INTO orders
        (order_id, user_id, product_name, status)
        VALUES (?, ?, ?, ?)
        """,
        [
            (1001, 1, "Sony耳机", "已发货"),
            (1002, 1, "手机壳", "待付款"),
            (1003, 2, "机械键盘", "已完成")
        ]
    )

    conn.commit()
    conn.close()
