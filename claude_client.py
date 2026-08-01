"""
AI 对话模块 — DeepSeek V4 + 命令解析
"""
import re
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, HUOHUO_SYSTEM_PROMPT


class AIClient:
    """藿藿的大脑"""

    def __init__(self, api_key: str | None = None):
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            raise ValueError("请设置 DEEPSEEK_API_KEY")
        self.client = OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL)
        self.model = DEEPSEEK_MODEL
        self.system_prompt = HUOHUO_SYSTEM_PROMPT
        self.history: list[dict] = []

    def chat(self, user_text: str) -> dict:
        """
        返回:
        {
            "text": "要说的文字（干净无标签）",
            "emotion": "开心|紧张|...",
            "command": "操作描述或None"
        }
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        for h in self.history[-20:]:
            messages.append({"role": "user", "content": h["user"]})
            messages.append({"role": "assistant", "content": h["assistant"]})
        messages.append({"role": "user", "content": user_text})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=300,
            temperature=0.9,
        )
        raw = response.choices[0].message.content.strip()

        # 解析格式
        emotion = "平常"
        text = raw
        command = None

        # 提取 EMOTION:xxx
        emo_match = re.match(r'EMOTION:(.+)', raw)
        if emo_match:
            emotion = emo_match.group(1).strip()
            # 从第二行开始取文本
            rest = raw[emo_match.end():].strip()
            text = rest

        # 提取 CMD:xxx
        cmd_match = re.search(r'CMD:(.+)', text)
        if cmd_match:
            command = cmd_match.group(1).strip()
            text = text[:cmd_match.start()].strip()

        # 清理文本中的括号内容
        text = re.sub(r'[（(][^）)]*[）)]', '', text)

        # 保存历史
        self.history.append({"user": user_text, "assistant": raw})

        if not text:
            text = "呜...我不知道该说什么..."

        return {"text": text.strip(), "emotion": emotion, "command": command}
