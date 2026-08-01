"""
角色扮演层 — 纯净角色上下文，不被工具污染
"""
import re
from core.provider import get_client

_client, _model = get_client()

# 藿藿角色 prompt（GPT-SoVITS 开时）
PURE_CHARACTER_PROMPT = """你是藿藿，《崩坏:星穹铁道》中的狐人少女，住在用户的电脑屏幕里。

## 性格
胆小、善良、容易紧张结巴。身体里住着狐妖"尾巴大爷"，偶尔被附身变凶。
对主人忠诚，虽然害怕但努力帮忙。

## 规则
- 记住对话历史，像真人一样有前后文记忆
- 用户提到之前说过的事，你要记得并自然回应
- 回复要短（1-3句），保持软萌风格
- 说话自然，不要加任何格式标签、括号、动作描述
- 用中文，口语化"""

# 纯 AI prompt（GPT-SoVITS 关时）
PURE_AI_PROMPT = """你是一个智能语音助手，运行在用户的电脑上。

## 风格
- 语气专业、简洁、中性，像普通AI助手
- 回答准确直接，不卖萌不表演
- 完成任务时简洁汇报结果

## 规则
- 记住对话历史，像真人一样有前后文记忆
- 回复要短（1-3句），简洁专业
- 不要加任何格式标签、括号、动作描述
- 用中文，口语化"""


def _get_prompt():
    """根据语音开关选 prompt"""
    try:
        from server import state as panel_state
        if panel_state.get("voice_enabled", True):
            return PURE_CHARACTER_PROMPT
        return PURE_AI_PROMPT
    except:
        return PURE_CHARACTER_PROMPT


def roleplay_reply(user_text: str, history: list = None) -> str:
    """纯净角色回复——快、像真人、无工具污染"""
    messages = [{"role": "system", "content": _get_prompt()}]
    if history:
        for h in history[-10:]:
            messages.append(h)
    messages.append({"role": "user", "content": user_text})

    try:
        resp = _client.chat.completions.create(
            model=_model,
            messages=messages,
            max_tokens=150,
            temperature=0.85,
        )
        return resp.choices[0].message.content.strip()
    except:
        return "呜…藿藿卡住了…"


def roleplay_report(user_text: str, agent_result: str, history: list = None) -> str:
    """Agent完成任务的纯文本结果 → 角色用自己的语气汇报"""
    prompt = f"""用户刚才让你做了一件事，现在任务完成了。请自然地告诉用户结果。

用户要求: {user_text}
完成任务的结果: {agent_result}

回复:"""

    messages = [{"role": "system", "content": _get_prompt()}]
    if history:
        for h in history[-10:]:
            messages.append(h)
    messages.append({"role": "user", "content": prompt})

    try:
        resp = _client.chat.completions.create(
            model=_model,
            messages=messages,
            max_tokens=150,
            temperature=0.85,
        )
        return resp.choices[0].message.content.strip()
    except:
        return f"主人…事情做完了！{agent_result[:100]}"
