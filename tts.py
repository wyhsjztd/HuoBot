"""
语音合成 — 快速流式 TTS
"""
import tempfile, os, subprocess, asyncio
from config import TTS_REF_AUDIO


def generate_speech(text: str, use_gpt: bool = True) -> str:
    """文字→语音，use_gpt=True 用GPT-SoVITS，否则直接Edge TTS"""
    output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    if not use_gpt:
        return _edge_tts(text, output)

    # 先试GPT-SoVITS
    try:
        import requests
        resp = requests.get(
            "http://127.0.0.1:9880/tts",
            params={
                "text": text, "text_lang": "zh",
                "ref_audio_path": TTS_REF_AUDIO,
                "prompt_lang": "zh",
            },
            timeout=30,
        )
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(output, "wb") as f:
                f.write(resp.content)
            return output
    except:
        pass

    # 备用：Edge TTS
    return _edge_tts(text, output)


def _edge_tts(text: str, output: str) -> str:
    """Edge TTS 合成"""
    import edge_tts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def _run():
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate="+0%")
        await communicate.save(output)
    loop.run_until_complete(_run())
    return output
