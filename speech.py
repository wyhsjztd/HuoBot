"""
语音识别 — SenseVoice 离线中文识别
"""
import json, os
import numpy as np
import pyaudio
import time
from config import SAMPLE_RATE, VAD_THRESHOLD, SILENCE_TIMEOUT

# Vosk 模型路径
from core.paths import get_path
MODEL_PATH = get_path("vosk-model-small-cn-0.22")

import os
from core.audio import find_mic_index

class SpeechRecognizer:
    def __init__(self):
        from core.asr import SenseVoiceASR
        print(f"📥 加载 SenseVoice 中文模型...")
        self.asr = SenseVoiceASR()
        self.sample_rate = SAMPLE_RATE
        self.chunk_size = 512
        self.mic_index = find_mic_index()

    def record_until_silence(self, silence_sec=SILENCE_TIMEOUT) -> bytes | None:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16, channels=1,
            rate=self.sample_rate, input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=self.mic_index if self.mic_index >= 0 else None,
        )
        print("🎤 正在听你说话...")
        frames = []
        last_voice_time = time.time()
        has_voice = False

        try:
            record_start = time.time()
            while True:
                chunk = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(chunk)
                data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
                energy = float(np.sqrt(np.mean(data ** 2)) / 32768.0)
                if energy > VAD_THRESHOLD:
                    last_voice_time = time.time()
                    has_voice = True
                # 停嘴超过 silence_sec 秒 → 结束
                if has_voice and time.time() - last_voice_time > silence_sec:
                    break
                # 绝对最大 12 秒 → 强制结束
                if time.time() - record_start > 12:
                    break
                # 10秒没检测到任何语音 → 放弃
                if time.time() - last_voice_time > 10 and not has_voice:
                    stream.stop_stream(); stream.close(); p.terminate()
                    return None
        finally:
            stream.stop_stream(); stream.close(); p.terminate()

        if not has_voice or len(frames) < 10:
            return None
        raw = b"".join(frames)
        print(f"   📝 录音完成: {len(raw)/(self.sample_rate*2):.1f}秒")
        return raw

    def record_until_release(self, should_continue, silence_sec=SILENCE_TIMEOUT, max_sec=15):
        """
        按住录音：持续录音直到 should_continue() 返回 False 或停嘴
        用 sounddevice 非阻塞，解决 pyaudio read 阻塞问题
        返回 bytes，没声音返回 None
        """
        import sounddevice as sd
        import soundfile as sf
        import io

        frames = []
        last_voice_time = time.time()
        has_voice = False
        record_start = time.time()

        def callback(indata, frames_, time_, status):
            nonlocal last_voice_time, has_voice
            import numpy as _np
            frames.append(indata.copy())
            energy = float(_np.sqrt(_np.mean(indata ** 2)))
            if energy > 0.005:  # sounddevice 返回 float，阈值对应音量
                last_voice_time = time.time()
                has_voice = True

        try:
            with sd.InputStream(
                samplerate=self.sample_rate, channels=1,
                callback=callback, blocksize=self.chunk_size,
                device=self.mic_index if self.mic_index >= 0 else None,
            ):
                while should_continue():
                    # 停嘴超时结束
                    if has_voice and time.time() - last_voice_time > silence_sec:
                        break
                    # 绝对最大时长
                    if time.time() - record_start > max_sec:
                        break
                    time.sleep(0.05)
        except Exception as e:
            print(f"⚠️ 录音错误: {e}")
            return None

        if not has_voice or not frames:
            return None
        # 拼接为 int16 bytes
        import numpy as np
        audio = np.concatenate(frames)
        audio = np.clip(audio, -1, 1)
        pcm = (audio * 32767).astype(np.int16).tobytes()
        print(f"   📝 录音完成: {len(pcm)/(self.sample_rate*2):.1f}秒")
        return pcm

    def transcribe(self, raw_audio: bytes) -> str:
        """SenseVoice 识别 PCM int16 bytes"""
        import numpy as np
        samples = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
        text = self.asr.transcribe_samples(samples)
        return text.strip() if text else ""
