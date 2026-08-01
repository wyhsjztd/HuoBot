"""
决策层 — 意图识别 + 路由分发
规则命中 → 直接后台  |  模糊请求 → 轻量LLM分类
"""
import re
import json
from core.provider import get_client

_client, _model = get_client()

# ===== 规则引擎 =====
RULES = [
    # 格式: (正则, 意图类型, 路由目标)
    (r"打开|启动|运行", "open_app", "agent"),
    (r"搜索|搜一下|查一下|帮我找", "search", "agent"),
    (r"播放|放歌|放音乐|来一首", "play_music", "agent"),
    (r"写代码|帮我写|代码|编程", "write_code", "agent"),
    (r"桌面|音量|亮度|设置|系统", "system", "agent"),
    (r"天气|几点了|今天几号|日期|时间", "query", "agent"),
    (r"你好|嗨|哈喽|hello|hi|在吗|你是谁", "greet", "roleplay"),
    (r"笑话|讲个|故事|聊天|无聊|陪我", "chat", "roleplay"),
    (r"背诵|古诗|唐诗|诗词|诗歌|背一下|背一", "recite", "roleplay"),
    (r"你是谁|介绍|名字|叫什么", "intro", "roleplay"),
    (r"再见|拜拜|晚安|走了", "bye", "roleplay"),
    (r"谢谢|感谢|多谢|辛苦", "thanks", "roleplay"),
]

# 快速指令
QUICK_ACTIONS = {
    "打开计算器": ("agent", "calc"),
    "打开记事本": ("agent", "notepad"),
    "打开浏览器": ("agent", "browser"),
}

INTENT_PROMPT = """判断用户输入类型：
- roleplay: 闲聊、打招呼、情感交流、背诵诗歌、讲笑话、知识问答、讲故事（不需要操作电脑）
- agent: 需要执行操作、打开程序、搜索实时信息、写代码、控制电脑

只回复一个词: agent 或 roleplay

用户说: {text}
分类:"""


def decide(user_text: str) -> dict:
    """
    返回: {"route": "agent"|"roleplay", "intent": "open_app"|"chat"|..., "action": str或None}
    """
    # 1. 快速指令匹配
    for key, (route, action) in QUICK_ACTIONS.items():
        if key in user_text:
            return {"route": route, "intent": "quick", "action": action}

    # 2. 规则匹配
    for pattern, intent, route in RULES:
        if re.search(pattern, user_text):
            return {"route": route, "intent": intent, "action": None}

    # 3. 轻量LLM分类（只一句话，很快）
    try:
        resp = _client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": INTENT_PROMPT.format(text=user_text)}],
            max_tokens=5,
            temperature=0,
        )
        route = resp.choices[0].message.content.strip().lower()
        if route not in ("agent", "roleplay"):
            route = "roleplay"
        return {"route": route, "intent": "llm_classified", "action": None}
    except:
        return {"route": "roleplay", "intent": "fallback", "action": None}
