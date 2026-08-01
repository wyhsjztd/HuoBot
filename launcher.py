"""HuoBot 一键启动"""
import subprocess, time, os, sys
from config import SOVITS_BASE

def main():
    print("🦊 HuoBot 启动中...")

    # 1. 启动语音引擎 (GPT-SoVITS)
    api_dir = SOVITS_BASE
    api_py = os.path.join(api_dir, "runtime", "python.exe")
    api = subprocess.Popen(
        [api_py, "api_v2.py"],
        cwd=api_dir,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    print("  语音引擎启动中...")

    # 等API就绪
    import urllib.request
    ready = False
    for i in range(60):
        try:
            urllib.request.urlopen("http://127.0.0.1:9880/docs", timeout=1)
            ready = True
            break
        except:
            time.sleep(1)
    if ready:
        print("  ✅ 语音引擎就绪")
    else:
        print("  ⚠️ 语音引擎未就绪（将用Edge TTS备用语音）")

    # 2. 启动桌面端（含控制面板，同一进程）
    print("  桌面端启动中...")
    subprocess.Popen(
        ["cmd", "/c", "python main.py"],
        cwd=os.path.dirname(__file__),
    )
    print("  ✅ HuoBot 已启动")
    print("  控制面板: http://127.0.0.1:18688")

    # 等待手动关闭
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        api.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
