"""
语音识别 — Sherpa-ONNX SenseVoice (阿里开源, 中文极准)
"""
import os
import numpy as np
import sounddevice as sd
import time

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model.onnx")

class SenseVoiceASR:
    def __init__(self):
        import sherpa_onnx
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"模型未找到: {MODEL_PATH}")
        print(f"📥 加载 SenseVoice 模型...")
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=MODEL_PATH,
            tokens=os.path.join(os.path.dirname(MODEL_PATH), "tokens.txt"),
            num_threads=2,
            use_itn=True,
            debug=False,
        )
        self.sample_rate = 16000

    def transcribe(self, pcm_bytes: bytes) -> str:
        """识别 PCM int16 bytes"""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return self.transcribe_samples(samples)

    def transcribe_samples(self, samples: np.ndarray) -> str:
        """直接传 float32 采样数组"""
        stream = self.recognizer.create_stream()
        stream.accept_waveform(self.sample_rate, samples)
        self.recognizer.decode_stream(stream)  # 结果在 stream.result
        text = stream.result.text.strip() if stream.result else ""
        import re
        text = re.sub(r'<\|[^|]+\|>', '', text).strip()
        return text
