"""
唤醒词检测 + VAD — Vosk 离线识别
"""
import collections, json, time, os
import numpy as np
import pyaudio
import vosk
from config import WAKE_WORDS, SAMPLE_RATE, VAD_THRESHOLD

from core.paths import get_path
from core.audio import find_mic_index
MODEL_PATH = get_path("vosk-model-small-cn-0.22")


class WakeWordDetector:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Vosk模型未找到: {MODEL_PATH}")
        self.model = vosk.Model(MODEL_PATH)
        self.wake_words = [w.lower() for w in WAKE_WORDS]
        # 谐音匹配（Vosk 可能识别成同音字）
        self.similar = ["小藿同学", "藿藿", "霍霍", "小霍同学", "小货同学", "小获同学", "小活同学"]
        self.sample_rate = SAMPLE_RATE
        self.chunk_size = 512
        self.mic_index = find_mic_index()

    def _energy(self, audio_data: bytes) -> float:
        data = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        return float(np.sqrt(np.mean(data ** 2)) / 32768.0)

    def listen_for_wake_word(self, timeout=None) -> str | None:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16, channels=1,
            rate=self.sample_rate, input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.mic_index if self.mic_index >= 0 else None,
        )
        buffer = collections.deque(maxlen=int(self.sample_rate / self.chunk_size * 3))
        speaking = False
        speech_frames = []

        print("🎤 等待唤醒词：小藿同学 ...")
        try:
            while True:
                chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                buffer.append(chunk)
                energy = self._energy(chunk)

                if energy > VAD_THRESHOLD:
                    if not speaking:
                        speaking = True
                        speech_frames = list(buffer)
                    speech_frames.append(chunk)
                elif speaking:
                    recent = speech_frames[-int(self.sample_rate / self.chunk_size):]
                    recent_data = np.frombuffer(b"".join(recent), dtype=np.int16).astype(np.float32)
                    if float(np.sqrt(np.mean(recent_data ** 2)) / 32768.0) < VAD_THRESHOLD * 0.5:
                        if len(speech_frames) > self.sample_rate / self.chunk_size * 0.5:
                            raw = b"".join(speech_frames)
                            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
                            rec.AcceptWaveform(raw)
                            result = json.loads(rec.FinalResult())
                            text = result.get("text", "").replace(" ", "").lower()
                            print(f"   🔊 听到: {text}")
                            for ww in self.wake_words + self.similar:
                                if ww in text:
                                    return ww
                        speaking = False
                        speech_frames = []
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
