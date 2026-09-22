# ============================================================
# app/agent/result.py
# Tool统一返回格式
# ============================================================


# ============================================================
# 1. 成功
# ============================================================

def success(data):

    return {
        "status": "success",
        "data": data,
        "error": None
    }


# ============================================================
# 2. 错误
# ============================================================

def error(
    code,
    message,
    error_type="business"
):

    return {
        "status": "error",
        "data": None,
        "error": {
            "type": error_type,
            "code": code,
            "message": message
        }
    }


# ============================================================
# 3. 参数错误
# ============================================================

def validation_error(message):

    return error(
        code="INVALID_ARGUMENTS",
        message=message,
        error_type="validation"
    )


# ============================================================
# 4. 系统错误
# ============================================================

def system_error(message):

    return error(
        code="SYSTEM_ERROR",
        message=message,
        error_type="system"
    )


# ============================================================
# 5. 用户确认
# ============================================================

def confirmation_required(
    tool_name,
    arguments,
    message="该操作需要用户确认"
):

    return {
        "status": "confirmation_required",
        "data": None,
        "error": None,
        "action": {
            "tool_name": tool_name,
            "arguments": arguments,
            "message": message
        }
    }