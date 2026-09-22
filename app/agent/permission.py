# ============================================================
# app/agent/permission.py
# Agent 权限控制层
# ============================================================


# ============================================================
# 判断 Tool 是否需要用户确认
# ============================================================

def need_confirmation(
    tool,
    user_confirmed=False
):

    # 不是危险操作
    if not tool["dangerous"]:
        return False


    # 已经确认
    if user_confirmed:
        return False


    # 危险操作，没有确认
    return True