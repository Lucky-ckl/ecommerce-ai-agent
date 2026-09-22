# ============================================================
# app/tools/order.py
# 订单业务 Tool
# ============================================================

from app.database.db import (
    get_order_record,
    update_order_status
)

from app.agent.result import (
    success,
    error
)


# ============================================================
# 1. 查询订单
# ============================================================

def query_order(order_id: int):
    
    order = get_order_record(order_id)

    if order is None:
        return error(
            code="ORDER_NOT_FOUND",
            message="订单不存在"
        )

    return success(
        data={
            "order": order
        }
    )


# ============================================================
# 2. 取消订单
# ============================================================

def cancel_order(order_id: int):

    order = get_order_record(order_id)

    if order is None:
        return error(
            code="ORDER_NOT_FOUND",
            message="订单不存在"
        )

    if order["status"] == "已取消":
        return error(
            code="ORDER_ALREADY_CANCELLED",
            message="订单已经取消"
        )

    affected_rows = update_order_status(
        order_id,
        "已取消"
    )

    if affected_rows == 0:
        return error(
            code="ORDER_UPDATE_FAILED",
            message="订单状态修改失败"
        )

    return success(
        data={
            "order_id": order_id,
            "status": "已取消"
        }
    )
