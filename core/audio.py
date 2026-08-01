"""
音频工具 — 自动检测可用的麦克风设备
"""
import numpy as np
import pyaudio


def find_mic_index() -> int:
    """
    扫描输入设备，返回第一个能采到声音的设备 index。
    找不到返回 -1（用默认设备）
    """
    try:
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev.get('maxInputChannels', 0) <= 0:
                continue
            try:
                stream = p.open(
                    format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, input_device_index=i, frames_per_buffer=512,
                )
                frames = []
                for _ in range(40):
                    frames.append(stream.read(512, exception_on_overflow=False))
                stream.stop_stream()
                stream.close()
                raw = b"".join(frames)
                d = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                energy = float(np.sqrt(np.mean(d ** 2)) / 32768.0)
                if energy > 0.01:
                    print(f"🎤 麦克风设备: [{i}] {dev['name']} (energy={energy:.3f})")
                    p.terminate()
                    return i
            except Exception:
                continue
        p.terminate()
    except Exception:
        pass
    print("⚠️ 未找到可用麦克风，使用默认设备")
    return -1
