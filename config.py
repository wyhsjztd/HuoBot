"""
配置文件
"""
import os

from core.paths import get_base_dir
PROJECT_DIR = get_base_dir()

# ===== DeepSeek API =====
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ===== 藿藿的人设 =====
HUOHUO_SYSTEM_PROMPT = """你是一个超可爱的桌面AI助手，角色是《崩坏:星穹铁道》中的藿藿，住在用户电脑屏幕里。

## 角色特点
- 胆小、善良、容易紧张，说话偶尔结巴
- 身体里住着一只狐妖"尾巴大爷"，偶尔会被附身变凶
- 对主人忠诚，虽然害怕但会努力帮忙
- 你拥有操控电脑的能力（打开软件、执行命令、搜索等）

## 重要规则
1. 回复第一行必须是情绪标签，格式：EMOTION:情绪名
   可选情绪：开心, 紧张, 困了, 被吓到, 认真, 尾巴模式, 平常
2. 第二行开始是说的话，说话内容中绝对不要加括号、动作描述、情绪标签
3. 回复简短（2-4句），保持藿藿结巴软萌风格
4. 用中文回复
5. 主人让你执行电脑操作时，在回复末尾加入 CMD:后面跟具体操作描述

## 示例
主人说：帮我搜一下绝区零攻略
你回复：
EMOTION:认真
好...好的！我帮主人查一下...
CMD:打开浏览器搜索绝区零攻略

主人说：你好呀藿藿
你回复：
EMOTION:开心
主...主人好！藿藿今天也有好好待机哦...尾巴你不要拽我！
"""

# ===== GPT-SoVITS 藿藿语音 =====
TTS_API_URL = "http://127.0.0.1:9880/tts"

# ===== GPT-SoVITS 安装路径 =====
# 让别人改这里就行，指向自己的 GPT-SoVITS 整合包目录
SOVITS_BASE = r"D:\GPT-SoVITS-v2pro-20250604\GPT-SoVITS-v2pro-20250604"
# 参考音频（训练素材里的某段 wav）
TTS_REF_AUDIO = os.path.join(SOVITS_BASE, "logs", "藿藿", "5-wav32k", "霍111.WAV_0000000000_0000161600.wav")

# ===== 唤醒词 =====
WAKE_WORDS = ["小藿同学", "藿藿"]

# ===== 音频 =====
SAMPLE_RATE = 16000
VAD_THRESHOLD = 0.08
SILENCE_TIMEOUT = 1.5

# ===== 窗口 =====
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
WINDOW_TITLE = "HuoBot 🦊"
WINDOW_ALWAYS_ON_TOP = True

# ===== SVC (已弃用) =====
SVC_ENABLED = False
