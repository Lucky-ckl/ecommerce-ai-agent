# ============================================================
# app/database/business_store.py
# 扩展业务数据：物流 / 退款 / 优惠券 / 收货地址
#
# 为了让 Agent 覆盖更完整的客服场景，
# 这里补齐除了订单查询与取消之外的业务数据表。
# ============================================================

from datetime import datetime, timedelta

from app.database.db import get_connection


# ============================================================
# 1. 建表
# ============================================================

def init_business_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            order_id     INTEGER PRIMARY KEY,
            carrier      TEXT NOT NULL,
            tracking_no  TEXT NOT NULL,
            current_node TEXT NOT NULL,
            eta          TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id     INTEGER NOT NULL,
            reason       TEXT,
            status       TEXT NOT NULL,
            created_at   TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            coupon_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            code         TEXT NOT NULL,
            amount       REAL NOT NULL,
            status       TEXT NOT NULL,
            expire_at    TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_address (
            order_id     INTEGER PRIMARY KEY,
            address      TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# 2. 演示数据
# ============================================================

def seed_business_data():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM shipments")

    if cursor.fetchone()[0] > 0:

        conn.close()

        return

    now = datetime.now()

    later = now + timedelta(days=3)

    fmt = "%Y-%m-%d"

    cursor.executemany(
        """
        INSERT OR IGNORE INTO shipments
        (order_id, carrier, tracking_no, current_node, eta, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                1001,
                "顺丰国际",
                "SF1001JP",
                "已到达东京转运中心",
                later.strftime(fmt),
                now.isoformat(timespec="seconds")
            ),
            (
                1002,
                "未发货",
                "-",
                "等待付款",
                "-",
                now.isoformat(timespec="seconds")
            ),
            (
                1003,
                "中通国际",
                "ZT1003US",
                "已签收",
                now.strftime(fmt),
                now.isoformat(timespec="seconds")
            )
        ]
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO coupons
        (user_id, code, amount, status, expire_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "NEWCOMER50", 50.0, "unused",
             (now + timedelta(days=60)).strftime(fmt)),
            (1, "SUMMER20", 20.0, "unused",
             (now + timedelta(days=15)).strftime(fmt)),
            (2, "VIP100", 100.0, "used",
             (now + timedelta(days=30)).strftime(fmt))
        ]
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO order_address
        (order_id, address, updated_at)
        VALUES (?, ?, ?)
        """,
        [
            (
                1001,
                "日本 东京都新宿区 1-2-3",
                now.isoformat(timespec="seconds")
            ),
            (
                1002,
                "日本 大阪府大阪市 4-5-6",
                now.isoformat(timespec="seconds")
            )
        ]
    )

    conn.commit()
    conn.close()


# ============================================================
# 3. 查询某个用户的全部订单
# ============================================================

def list_user_orders(user_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT order_id, product_name, status
        FROM orders
        WHERE user_id = ?
        ORDER BY order_id
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    orders = []

    for row in rows:

        orders.append(
            {
                "order_id": row[0],
                "product_name": row[1],
                "status": row[2]
            }
        )

    return orders


# ============================================================
# 4. 查询物流轨迹
# ============================================================

def get_shipment(order_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT order_id, carrier, tracking_no, current_node, eta, updated_at
        FROM shipments
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
        "carrier": row[1],
        "tracking_no": row[2],
        "current_node": row[3],
        "eta": row[4],
        "updated_at": row[5]
    }


# ============================================================
# 5. 创建退款申请
# ============================================================

def create_refund(order_id, reason):

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO refunds
        (order_id, reason, status, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            order_id,
            reason,
            "审核中",
            created_at
        )
    )

    refund_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "refund_id": refund_id,
        "order_id": order_id,
        "reason": reason,
        "status": "审核中",
        "created_at": created_at
    }


# ============================================================
# 6. 修改收货地址
# ============================================================

def update_order_address(order_id, address):

    updated_at = datetime.now().isoformat(
        timespec="seconds"
    )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO order_address
        (order_id, address, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(order_id) DO UPDATE SET
            address = excluded.address,
            updated_at = excluded.updated_at
        """,
        (
            order_id,
            address,
            updated_at
        )
    )

    conn.commit()
    conn.close()

    return {
        "order_id": order_id,
        "address": address,
        "updated_at": updated_at
    }


def get_order_address(order_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT address
        FROM order_address
        WHERE order_id = ?
        """,
        (order_id,)
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:

        return None

    return row[0]


# ============================================================
# 7. 查询优惠券
# ============================================================

def list_coupons(user_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT coupon_id, code, amount, status, expire_at
        FROM coupons
        WHERE user_id = ?
        ORDER BY status, coupon_id
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    coupons = []

    for row in rows:

        coupons.append(
            {
                "coupon_id": row[0],
                "code": row[1],
                "amount": row[2],
                "status": row[3],
                "expire_at": row[4]
            }
        )

    return coupons


# ============================================================
# 8. 运费与时效估算
#
# 纯规则计算，不查数据库
# ============================================================

SHIPPING_RULES = {

    "日本": {"base": 30, "per_kg": 18, "days": "5-8"},

    "美国": {"base": 45, "per_kg": 25, "days": "8-12"},

    "欧盟": {"base": 50, "per_kg": 28, "days": "7-10"},

    "东南亚": {"base": 25, "per_kg": 15, "days": "4-7"},
}


def estimate_shipping(country, weight_kg=1.0):

    rule = SHIPPING_RULES.get(country)

    if rule is None:

        rule = SHIPPING_RULES["美国"]

        country = f"{country}（按默认规则估算）"

    weight = float(weight_kg)

    fee = rule["base"] + rule["per_kg"] * weight

    if fee >= 299:

        shipping_fee = 0.0

        note = "已满 299 元，免运费"

    else:

        shipping_fee = round(fee, 2)

        note = "未满 299 元，需支付运费"

    return {
        "country": country,
        "weight_kg": weight,
        "shipping_fee": shipping_fee,
        "estimated_days": rule["days"],
        "note": note
    }
