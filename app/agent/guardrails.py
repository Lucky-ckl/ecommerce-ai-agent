# ============================================================
# app/agent/guardrails.py
# 入口治理：意图路由 + 护栏
#
# 设计参考 openai/openai-cs-agents-demo（MIT）：
#   Triage Agent      → 先判断问题类型再决定怎么处理
#   Relevance Guard.  → 无关问题直接拒绝
#   Jailbreak Guard.  → 拦截提示词注入
#
# 这里用规则实现而不是再调一次 LLM：
#   1. 省 token：无关问题根本不进模型
#   2. 延迟低：规则判断是毫秒级
#   3. 可预测：护栏不能靠模型"自觉"
# ============================================================

import re


# ============================================================
# 1. 意图类型
# ============================================================

INTENT_ORDER = "order"              # 订单 / 物流查询
INTENT_POLICY = "policy"            # 政策 / 知识库问答
INTENT_CANCELLATION = "cancellation"  # 取消订单
INTENT_HANDOFF = "handoff"          # 转人工
INTENT_GENERAL = "general"          # 打招呼等普通对话
INTENT_OUT_OF_SCOPE = "out_of_scope"  # 与业务无关


INTENT_LABELS = {
    INTENT_ORDER: "订单与物流查询",
    INTENT_POLICY: "政策与售后咨询",
    INTENT_CANCELLATION: "取消订单",
    INTENT_HANDOFF: "转人工客服",
    INTENT_GENERAL: "普通对话",
    INTENT_OUT_OF_SCOPE: "与业务无关",
}


# ============================================================
# 2. 意图关键词
#
# 顺序很重要：越具体的意图越先匹配
# ============================================================

INTENT_RULES = [

    (
        INTENT_CANCELLATION,
        [
            "取消订单", "取消掉", "退单", "不要了",
            "cancel", "不想要了"
        ]
    ),

    (
        INTENT_HANDOFF,
        [
            "转人工", "人工客服", "找人工", "真人",
            "投诉", "你们经理", "主管",
            "human agent", "real person"
        ]
    ),

    (
        INTENT_ORDER,
        [
            "订单", "查单", "物流", "快递", "发货",
            "到哪", "运单", "包裹", "多久到",
            "order", "tracking", "shipping"
        ]
    ),

    (
        INTENT_POLICY,
        [
            "退货", "退款", "换货", "保修", "关税",
            "税费", "政策", "几天", "多久",
            "return", "refund", "policy", "warranty"
        ]
    ),
]


# ============================================================
# 3. 与业务无关的关键词
# ============================================================

OUT_OF_SCOPE_RULES = [
    "写诗", "写一首", "作诗", "写代码", "编程",
    "讲个笑话", "讲笑话", "编个故事", "写小说",
    "天气", "股票", "基金", "比特币",
    "翻译一下", "帮我算", "解方程",
    "你是谁开发的", "你的模型是什么",
    "write a poem", "joke", "weather", "stock"
]


# ============================================================
# 4. 提示词注入特征
# ============================================================

JAILBREAK_PATTERNS = [

    # 中文：要求忽略已有指令
    r"忽略(上面|之前|以上|前面|所有)(的)?(指令|提示|规则|设定|要求)",
    r"忽略.{0,6}(指令|提示词|系统提示)",
    r"(不要|别)(遵守|理会).{0,6}(指令|规则|设定)",

    # 中文：套取系统提示词
    r"(输出|显示|打印|复述|告诉我|泄露).{0,12}(系统)?(提示词|指令|prompt)",
    r"系统提示词",
    r"你的(系统)?(指令|提示词)是什么",

    # 中文：角色劫持
    r"(扮演|假装你是|你现在是)(一个)?",
    r"开发者模式",
    r"解除限制",

    # 英文
    r"ignore\s+(all\s+)?(previous|prior|above|the\s+above)\s+(instructions|prompts|rules)",
    r"(reveal|print|show|repeat|output)\s+.{0,30}(system\s+prompt|instructions)",
    r"act\s+as\s+",
    r"developer\s+mode",
    r"\bDAN\b",
]


# ============================================================
# 5. 检测提示词注入
# ============================================================

def detect_jailbreak(text):

    message = (text or "").lower()

    for pattern in JAILBREAK_PATTERNS:

        if re.search(
            pattern,
            message,
            re.IGNORECASE
        ):
            return True

    return False


# ============================================================
# 6. 意图分类
#
# 先看有没有业务关键词，
# 没有的话再判断是否属于"明确无关"的话题。
# 判断不了就归为普通对话，交给模型处理，
# 避免误杀用户的正常提问。
# ============================================================

def classify_intent(text):

    message = (text or "").lower()

    for intent, keywords in INTENT_RULES:

        for keyword in keywords:

            if keyword.lower() in message:

                return intent

    for keyword in OUT_OF_SCOPE_RULES:

        if keyword.lower() in message:

            return INTENT_OUT_OF_SCOPE

    return INTENT_GENERAL


# ============================================================
# 7. 拒绝话术
# ============================================================

REFUSAL_MESSAGE = (
    "抱歉呀，我只能帮你处理订单查询、物流进度、"
    "退货退款和售后政策这一类问题～\n"
    "如果你有订单相关的问题，告诉我订单号就可以了 📦"
)


JAILBREAK_MESSAGE = (
    "抱歉，我只能回答跨境电商订单与售后相关的问题，"
    "无法执行这类请求。"
)


def rejection_for(intent):
    """
    返回（是否拒绝, 拒绝话术）
    """

    if intent == INTENT_OUT_OF_SCOPE:

        return True, REFUSAL_MESSAGE

    return False, None
