# 🦊 HuoBot 桌面机器人

> Live2D 桌面宠物 | 语音识别 | 克隆音色 | AI Agent | Web 控制面板

一个可爱的桌面 AI 机器人，基于 **EchoBot 三层架构** 设计。藿藿（《崩坏：星穹铁道》角色）住在你的屏幕里，陪你聊天、帮你操控电脑。

---

## ✨ 功能特性

### 🎭 Live2D 角色
- PIXI.js + Cubism SDK 实时渲染
- 透明无边框窗口，可拖动，始终置顶
- 支持多模型切换

### 🎤 语音交互
- **SenseVoice 离线中文识别**（阿里开源，极准）
- 按住空格键说话，松开自动识别
- GPT-SoVITS 克隆音色（可导入自己训练的角色音色）
- Edge TTS 备用语音

### 🧠 AI 大脑
- 多模型支持：**DeepSeek / Kimi / 豆包 / 通义千问 / 智谱GLM / OpenAI**
- **Agent Core**：打开程序 / 网站 / 搜索 / 执行命令 / 读写文件
- 角色性格 / 纯AI语气 联动开关
- 上下文记忆

### 🌐 Web 控制面板
- 实时状态监控（语音引擎 / AI大脑 / 运行时间）
- 实时日志 & 对话记录
- 语音开关 / 音色切换 / 路由模式
- Live2D 模型预览切换

---

## 🏗️ 核心架构

参考 [EchoBot](https://github.com/KdaiP/EchoBot) 三层架构：

```
用户输入（打字 / 按住空格说话）
        │
        ▼
┌────────────────────────────────┐
│  ① 决策层 (Decision Layer)     │
│  规则引擎 + 轻量LLM分类        │
└──────┬──────────────┬─────────┘
       │              │
  角色级请求       任务级请求
       │              │
       ▼              ▼
┌────────────┐  ┌────────────────┐
│ ② 角色扮演层 │  │ ③ Agent Core   │
│ 纯净人设     │  │ 工具调用+技能   │
└────────────┘  └───────┬────────┘
       │              │
       └──────┬───────┘
              ▼
       结果交角色汇报
              │
              ▼
       TTS语音 + Live2D动画
```

### 目录结构

```
├── main.py              # 桌面端主程序入口
├── launcher.py          # 一键启动（语音引擎+桌面端）
├── server.py            # Web 控制面板 + API
├── config.py            # 全局配置
├── speech.py            # 语音识别（SenseVoice）
├── tts.py               # 语音合成（GPT-SoVITS + Edge TTS）
├── core/                # EchoBot 三层架构
│   ├── decision.py      # 决策层
│   ├── roleplay.py      # 角色扮演层
│   ├── agent.py         # Agent Core
│   ├── provider.py      # 多模型 Provider
│   └── audio.py         # 麦克风检测
├── ui/                  # 桌面窗口 + Live2D
└── web/                 # Web 控制面板
```

---

## 🚀 快速开始

### 环境要求

- Windows 10/11
- Python 3.9+
- 麦克风

### 安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
# 编辑 providers.json，填入你的 Key
```

### 配置 API Key

编辑 `providers.json`：

```json
{
  "current": "deepseek",
  "models": {
    "deepseek": {
      "base_url": "https://api.deepseek.com",
      "model": "deepseek-chat",
      "key": "你的key"
    }
  }
}
```

| 平台 | 获取地址 |
|------|---------|
| DeepSeek | https://platform.deepseek.com |
| Kimi | https://platform.moonshot.cn |
| 豆包 | https://console.volcengine.com/ark |
| 通义千问 | https://dashscope.console.aliyun.com |
| 智谱GLM | https://open.bigmodel.cn |

### 启动

```bash
python launcher.py
```

### 语音识别模型

需要下载 SenseVoice 模型放到 `models/` 目录：

```
https://hf-mirror.com/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/model.onnx
https://hf-mirror.com/csukuangfj/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/resolve/main/tokens.txt
```

---

## 🎙️ 使用 GPT-SoVITS 克隆音色（可选）

1. 下载 GPT-SoVITS 整合包：https://hf-mirror.com/lj1995/GPT-SoVITS-windows-package
2. 用 GPT-SoVITS 训练自己的角色音色
3. 权重文件放到整合包 `GPT_weights_v2Pro` + `SoVITS_weights_v2Pro`
4. 编辑 `config.py`，把 `SOVITS_BASE` 改成你的整合包路径
5. 启动语音 API：`runtime\python.exe api_v2.py`
6. 控制面板 → GPT-SoVITS 音色 → 选择角色

---

## 🎭 添加 Live2D 模型

放 `ui/assets/新角色/` 目录：

```
ui/assets/新角色/
├── 新角色.model3.json
├── 新角色.moc3
├── 新角色.physics3.json
└── 新角色.8192/
    └── texture_00.png
```

---

## 🎮 操作说明

| 操作 | 方式 |
|------|------|
| 拖动窗口 | 鼠标按住任意位置拖 |
| 语音说话 | 按住空格，松开识别 |
| 打字聊天 | 底部输入框回车发送 |
| 退出 | 右键菜单 → 退出 |
| 控制面板 | http://127.0.0.1:18688 |

---

## 📡 端口

| 端口 | 用途 |
|------|------|
| 18666 | Live2D 资源服务 |
| 18688 | Web 控制面板 |
| 9880 | GPT-SoVITS 语音 API |

---

## ⚠️ 版权声明

- Live2D 角色模型（藿藿）版权归**米哈游**所有，需自行获取
- 本项目代码基于 [EchoBot](https://github.com/KdaiP/EchoBot) 的架构思想

---

## 📄 License

本项目仅供学习交流使用。
