"""
后台控制面板 — 纯 HTTP 轮询，无 WebSocket 复杂度
"""
import json, time, threading, os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="HuoBot 控制台")

state = {
    "voice_enabled": True, "wake_enabled": True,
    "route_mode": "agent_first", "ai_connected": True,
    "tts_ready": False, "msg_count": 0, "_start": time.time(),
}
logs: list = []
mic_requested = threading.Event()  # 网页端麦克风触发


def add_panel_log(category: str, message: str):
    """主进程调用"""
    entry = {"time": time.strftime("%H:%M:%S"), "category": category, "msg": message}
    logs.append(entry)
    if len(logs) > 200: logs.pop(0)


# === API ===
@app.get("/api/state")
def get_state():
    state["uptime"] = int(time.time() - state.get("_start", 0))
    return state

@app.get("/api/mic")
def api_mic():
    """网页端麦克风按钮"""
    mic_requested.set()
    add_panel_log("info", "🎤 网页端请求录音")
    return {"ok": True}

@app.get("/api/logs")
def get_logs(after: int = 0):
    return logs[after:]

@app.get("/api/toggle_voice")
def toggle_voice():
    state["voice_enabled"] = not state["voice_enabled"]
    add_panel_log("setting", f"语音:{'开' if state['voice_enabled'] else '关'}")
    return {"ok": True, "voice_enabled": state["voice_enabled"]}

@app.get("/api/toggle_wake")
def toggle_wake():
    state["wake_enabled"] = not state["wake_enabled"]
    add_panel_log("setting", f"唤醒:{'开' if state['wake_enabled'] else '关'}")
    return {"ok": True, "wake_enabled": state["wake_enabled"]}

@app.get("/api/route_mode")
def set_route_mode(mode: str = "agent_first"):
    state["route_mode"] = mode
    add_panel_log("setting", f"路由:{mode}")
    return {"ok": True, "route_mode": mode}

@app.get("/api/models")
def get_models():
    from core.provider import get_all_models
    return get_all_models()

@app.get("/api/live2d_models")
def get_live2d_models():
    assets = os.path.join(os.path.dirname(__file__), "ui", "assets")
    models = []
    for d in os.listdir(assets):
        dpath = os.path.join(assets, d)
        if os.path.isdir(dpath):
            for f in os.listdir(dpath):
                if f.endswith(".model3.json"):
                    models.append({"name": d, "json": f, "path": f"assets/{d}/{f}"})
    return {"models": models, "current": state.get("live2d_model", "")}

@app.get("/api/tts_voices")
def get_tts_voices():
    """扫描 GPT-SoVITS 已训练的音色"""
    from config import SOVITS_BASE
    base = SOVITS_BASE
    gpt_dir = os.path.join(base, "GPT_weights_v2Pro")
    sovits_dir = os.path.join(base, "SoVITS_weights_v2Pro")
    voices = {}
    try:
        for f in os.listdir(gpt_dir):
            if f.endswith(".ckpt"):
                name = f.replace(".ckpt", "").rsplit("-e", 1)[0]
                epoch = f.rsplit("-e", 1)[-1].replace(".ckpt", "")
                if name not in voices:
                    voices[name] = {"gpt": [], "sovits": []}
                voices[name]["gpt"].append({"file": f, "epoch": epoch})
        for f in os.listdir(sovits_dir):
            if f.endswith(".pth"):
                name = f.rsplit("_e", 1)[0]
                if name in voices:
                    voices[name]["sovits"].append({"file": f})
    except:
        pass
    return {"voices": voices, "current": state.get("tts_voice", "藿藿")}

@app.get("/api/switch_tts_voice")
def api_switch_tts_voice(voice: str):
    """切换 GPT-SoVITS 音色"""
    from config import SOVITS_BASE
    base = SOVITS_BASE
    gpt_dir = os.path.join(base, "GPT_weights_v2Pro")
    sovits_dir = os.path.join(base, "SoVITS_weights_v2Pro")

    # 找最佳权重点
    gpt_file = sovits_file = ""
    try:
        for f in os.listdir(gpt_dir):
            if f.startswith(voice) and f.endswith(".ckpt"):
                gpt_file = os.path.join(gpt_dir, f)
                break
        for f in os.listdir(sovits_dir):
            if f.startswith(voice) and f.endswith(".pth"):
                sovits_file = os.path.join(sovits_dir, f)
                break
    except:
        pass

    if gpt_file and sovits_file:
        try:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:9880/set_gpt_weights?weights_path={gpt_file}", timeout=5)
            urllib.request.urlopen(f"http://127.0.0.1:9880/set_sovits_weights?weights_path={sovits_file}", timeout=5)
            state["tts_voice"] = voice
            add_panel_log("setting", f"音色切换: {voice}")
            return {"ok": True, "voice": voice}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "未找到该音色的模型文件"}

@app.get("/api/switch_live2d")
def api_switch_live2d(path: str):
    state["live2d_model"] = path
    add_panel_log("setting", f"Live2D切换: {path}")
    return {"ok": True, "path": path}


@app.get("/api/switch_model")
def api_switch_model(name: str):
    from core.provider import switch_model
    ok = switch_model(name)
    # 通知client重载
    if ok:
        import core.agent as a
        import core.roleplay as r
        import core.decision as d
        c, m = __import__("core.provider", fromlist=["get_client"]).get_client()
        a._client = c; a._model = m
        r._client = c; r._model = m
        d._client = c; d._model = m
        add_panel_log("setting", f"模型切换为: {name}")
    return {"ok": ok, "current": name}

@app.get("/")
def panel():
    return HTMLResponse((Path(__file__).parent / "web" / "panel.html").read_text(encoding="utf-8"))


def start_server():
    # 立即检测语音引擎
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:9880/docs", timeout=2)
        state["tts_ready"] = True
        print("✅ 语音引擎已检测到")
    except Exception as e:
        print(f"⚠️ 语音引擎未检测到: {e}")

    threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=18688, log_level="warning"),
        daemon=True,
    ).start()
