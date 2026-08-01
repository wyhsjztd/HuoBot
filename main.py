"""
HuoBot 桌面机器人 — EchoBot 三层架构
决策层 → 角色扮演层/Agent Core → 桌面窗口
"""
import sys, os, threading, time, queue, subprocess
import sounddevice as sd, soundfile as sf
import keyboard

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject

from ui.window import HuohuoWindow, start_http_server
from wake_word import WakeWordDetector
from speech import SpeechRecognizer
from tts import generate_speech
from core.decision import decide
from core.roleplay import roleplay_reply, roleplay_report
from core.agent import execute_agent_task
import server as server_mod
from server import start_server, add_panel_log, state as panel_state


class SignalBridge(QObject):
    status = pyqtSignal(str)
    subtitle = pyqtSignal(str, float)
    emotion = pyqtSignal(str)


class HuohuoApp:
    def __init__(self):
        self.wake_detector = WakeWordDetector()
        self.speech_recognizer = SpeechRecognizer()
        self.command_queue = queue.Queue()
        self.running = True
        self.busy = False
        self.history = []  # 对话历史
        self.mic_event = threading.Event()  # 麦克风按钮触发
        self.recording = False  # 当前是否在录音

    def start(self, window: HuohuoWindow, bridge: SignalBridge):
        self.window = window
        self.bridge = bridge
        threading.Thread(target=self._wake_word_loop, daemon=True).start()
        threading.Thread(target=self._command_loop, daemon=True).start()
        self.start_space_listener()

    def start_space_listener(self):
        """空格监听：按住空格时 recording=True 触发录音"""
        self.space_down = False
        threading.Thread(target=self._space_poll, daemon=True).start()
        print("⌨️ 按住空格说话已启用")

    def _space_poll(self):
        """轮询空格键：按住开始录音线程，松开设停止标志"""
        while self.running:
            try:
                pressed = keyboard.is_pressed("space")
            except:
                time.sleep(0.3)
                continue
            if pressed and not self.space_down:
                self.space_down = True
                print("⌨️ 空格按下 → 开始录音")
                self._start_recording()
            elif not pressed and self.space_down:
                self.space_down = False
                print("⌨️ 空格松开 → 停止")
                self.recording = False
            time.sleep(0.02)

    def _start_recording(self):
        """启动一次录音（独立线程，空格松开或停嘴结束）"""
        if self.recording or self.busy:
            return
        threading.Thread(target=self._do_record, daemon=True).start()

    def _do_record(self):
        self.recording = True
        self.busy = True
        self.bridge.status.emit("listening")
        self.bridge.subtitle.emit("🎤 正在听...松开结束", 0)
        raw = self.speech_recognizer.record_until_release(lambda: self.recording)
        self.recording = False
        self.busy = False
        self.bridge.status.emit("idle")
        if raw is None or len(raw) < 8000:
            self.bridge.subtitle.emit("没听清...", 2)
            return
        text = self.speech_recognizer.transcribe(raw)
        if text and len(text) >= 2:
            print(f"📝 语音: {text}")
            self.bridge.subtitle.emit(f"你说: {text}", 2)
            self.command_queue.put(text)
        else:
            self.bridge.subtitle.emit("没听清...", 2)

    def handle_mic(self, on: bool):
        """麦克风按钮：on=开始录音 off=停止（与空格共用）"""
        if on:
            self._start_recording()
        else:
            self.recording = False

    def _wake_word_loop(self):
        while self.running:
            time.sleep(1)  # 唤醒词已停用，线程空转

    def _command_loop(self):
        _last = ("", 0)
        while self.running:
            try: text = self.command_queue.get(timeout=0.5)
            except queue.Empty: continue
            now = time.time()
            if text == _last[0] and now - _last[1] < 3: continue
            _last = (text, now)

            # ===== 决策层 =====
            self.busy = True
            self.bridge.status.emit("thinking")
            add_panel_log("user", f"用户: {text}")
            panel_state["msg_count"] = panel_state.get("msg_count", 0) + 1

            # 面板路由模式覆盖
            route_mode = panel_state.get("route_mode", "agent_first")
            if route_mode == "chat_only":
                decision = {"route": "roleplay", "intent": "panel_override"}
            elif route_mode == "agent_first":
                decision = decide(text)
                # 纯闲聊仍走角色层（你好/晚安/谢谢/笑话等）
                if decision["route"] == "roleplay":
                    pass  # 保持角色层
            else:
                decision = decide(text)
            print(f"🧠 决策: route={decision['route']} intent={decision['intent']}")

            try:
                if decision["route"] == "agent":
                    # Agent Core 静默执行
                    self.bridge.subtitle.emit("唔…让藿藿想想办法…", 0)
                    self.bridge.emotion.emit("认真")
                    add_panel_log("thinking", f"Agent: {text}")
                    agent_result = execute_agent_task(text, self.history)
                    print(f"⚡ Agent完成: {agent_result[:200]}")
                    add_panel_log("agent", f"完成: {agent_result[:100]}")

                    # 角色层汇报
                    reply = roleplay_report(text, agent_result, self.history)
                    emotion = "认真"

                else:
                    # 角色扮演层直接回复
                    reply = roleplay_reply(text, self.history)
                    # 纯AI模式不用藿藿情绪
                    if panel_state.get("voice_enabled", True):
                        emotion = "平常"
                        if any(w in reply for w in ["嘻", "开心", "太好", "哈哈"]): emotion = "开心"
                        elif any(w in reply for w in ["呜", "怕", "别", "不要"]): emotion = "紧张"
                        elif any(w in reply for w in ["哼", "尾巴", "老子"]): emotion = "尾巴模式"
                    else:
                        emotion = "平常"

                print(f"🦊 藿藿[{emotion}]: {reply}")
                add_panel_log("speak", f"藿藿: {reply[:50]}")

                # TTS + 播放 (语音开关控制)
                voice_ok = panel_state.get("voice_enabled", True)
                audio_path = generate_speech(reply, use_gpt=voice_ok)
                audio_data, sr = sf.read(audio_path)
                duration = len(audio_data) / sr
                self.bridge.status.emit("speaking")
                self.bridge.emotion.emit(emotion)
                self.bridge.subtitle.emit(reply, duration)  # 持续到语音结束
                self.window.start_lip_sync()
                sd.play(audio_data, sr)
                sd.wait()
                self.window.stop_lip_sync()
                try: os.unlink(audio_path)
                except: pass

                # 记录历史
                self.history.append({"role": "user", "content": text})
                self.history.append({"role": "assistant", "content": reply})
                if len(self.history) > 40:
                    self.history = self.history[-40:]

            except Exception as e:
                print(f"❌ 错误: {e}")
                self.bridge.subtitle.emit("呜哇…出错了…", 0)
            finally:
                self.bridge.status.emit("idle")
                self.busy = False


def main():
    print("🦊 HuoBot 桌面端启动")

    # API Key 从 providers.json 读取（core.provider 已处理）

    start_http_server()
    start_server()
    print("📊 控制面板: http://127.0.0.1:18688")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = HuohuoWindow()
    window.show()

    bridge = SignalBridge()
    bridge.status.connect(window.set_status)
    bridge.subtitle.connect(window.show_subtitle)
    bridge.emotion.connect(window.set_emotion)

    huohuo = HuohuoApp()
    def on_page_ready():
        huohuo.start(window, bridge)
        window.bridge.textSubmitted.connect(lambda t: huohuo.command_queue.put(t))
        window.bridge.micChanged.connect(huohuo.handle_mic)
    window.page_ready.connect(on_page_ready)

    print("✅ 就绪")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
