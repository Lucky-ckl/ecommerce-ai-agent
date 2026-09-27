# ============================================================
# app/tools/business.py
# 扩展业务 Tool：物流 / 退款 / 地址 / 优惠券 / 运费估算
#
# 这些 Tool 和订单 Tool 走同一套注册与分发机制，
# 危险操作（退款、改地址）标记 dangerous=True，
# 复用已有的"人工确认"中间件，不需要重写任何拦截逻辑。
# ============================================================

from app.database.business_store import (
    create_refund,
    estimate_shipping,
    get_order_address,
    get_shipment,
    list_coupons,
    list_user_orders,
    update_order_address
)

from app.database.db import get_order_record

from app.agent.result import (
    error,
    success
)


# ============================================================
# 1. 查询我的全部订单
# ============================================================

def list_orders(user_id: int):

    orders = list_user_orders(user_id)

    if not orders:

        return error(
            code="ORDER_NOT_FOUND",
            message=f"用户 {user_id} 暂无订单"
        )

    return success(
        data={
            "user_id": user_id,
            "orders": orders,
            "count": len(orders)
        }
    )


# ============================================================
# 2. 查询物流轨迹
# ============================================================

def query_logistics(order_id: int):

    order = get_order_record(order_id)

    if order is None:

        return error(
            code="ORDER_NOT_FOUND",
            message="订单不存在"
        )

    shipment = get_shipment(order_id)

    if shipment is None:

        return error(
            code="SHIPMENT_NOT_FOUND",
            message="该订单暂无物流信息"
        )

    return success(
        data={
            "shipment": shipment
        }
    )


# ============================================================
# 3. 申请退款（危险操作，需要用户确认）
# ============================================================

def apply_refund(order_id: int, reason: str = "用户申请"):

    order = get_order_record(order_id)

    if order is None:

        return error(
            code="ORDER_NOT_FOUND",
            message="订单不存在"
        )

    if order["status"] == "已取消":

        return error(
            code="ORDER_ALREADY_CANCELLED",
            message="订单已取消，不能重复申请退款"
        )

    refund = create_refund(
        order_id,
        reason
    )

    return success(
        data={
            "refund": refund
        }
    )


# ============================================================
# 4. 修改收货地址（危险操作，需要用户确认）
# ============================================================

def update_address(order_id: int, new_address: str):

    order = get_order_record(order_id)

    if order is None:

        return error(
            code="ORDER_NOT_FOUND",
            message="订单不存在"
        )

    if order["status"] in ("已签收", "已完成"):

        return error(
            code="ORDER_CLOSED",
            message="订单已完成，不能再修改地址"
        )

    result = update_order_address(
        order_id,
        new_address
    )

    return success(
        data={
            "address": result
        }
    )


# ============================================================
# 5. 查询优惠券
# ============================================================

def query_coupon(user_id: int):

    coupons = list_coupons(user_id)

    if not coupons:

        return error(
            code="COUPON_NOT_FOUND",
            message=f"用户 {user_id} 暂无优惠券"
        )

    return success(
        data={
            "user_id": user_id,
            "coupons": coupons
        }
    )


# ============================================================
# 6. 运费与时效估算
# ============================================================

def estimate_shipping_fee(
    country: str,
    weight_kg: float = 1.0
):

    result = estimate_shipping(
        country,
        weight_kg
    )

    return success(
        data={
            "shipping": result
        }
    )
