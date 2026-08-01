"""
HuoBot 桌面窗口 — 无边框、可拖动、置顶、透明背景
"""
import os, time, sys
import http.server
import socketserver
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QMenu, QAction,
    QWidget, QVBoxLayout,
)
from PyQt5.QtCore import Qt, QPoint, QUrl, QEvent, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel
from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_ALWAYS_ON_TOP

HTTP_PORT = 18666


def start_http_server():
    from core.paths import get_path
    ui_dir = get_path("ui")
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=ui_dir, **kwargs)
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    httpd = ReusableTCPServer(("127.0.0.1", HTTP_PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


class Bridge(QObject):
    textSubmitted = pyqtSignal(str)
    micChanged = pyqtSignal(bool)
    @pyqtSlot(str)
    def sendText(self, text):
        self.textSubmitted.emit(text)


class HuohuoWindow(QMainWindow):
    page_ready = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.drag_pos = QPoint()
        self.bridge = Bridge()
        self.space_pressed = False
        self.init_ui()
        self.setFocusPolicy(Qt.StrongFocus)

    def init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central = QWidget(self)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        self.webview.setAttribute(Qt.WA_TranslucentBackground)
        self.webview.setStyleSheet("background: transparent;")
        self.webview.page().setBackgroundColor(Qt.transparent)
        url = f"http://127.0.0.1:{HTTP_PORT}/live2d.html?v={int(time.time())}"
        self.webview.load(QUrl(url))
        self.webview.loadFinished.connect(lambda: self.page_ready.emit())
        self.webview.titleChanged.connect(self._on_title_change)
        QApplication.instance().installEventFilter(self)
        layout.addWidget(self.webview)

    def eventFilter(self, obj, event):
        # 鼠标拖动：底部45px输入区不拦截（让输入框和按钮可点）
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            local = self.mapFromGlobal(event.globalPos())
            if local.y() < self.height() - 45:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                return True
        elif event.type() == QEvent.MouseMove and event.buttons() == Qt.LeftButton:
            if not self.drag_pos.isNull():
                self.move(event.globalPos() - self.drag_pos)
                return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.drag_pos = QPoint()
        return super().eventFilter(obj, event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        always_top = QAction("保持置顶", self, checkable=True)
        always_top.setChecked(WINDOW_ALWAYS_ON_TOP)
        always_top.triggered.connect(self.toggle_always_on_top)
        menu.addAction(always_top)
        menu.addSeparator()
        quit_act = QAction("退出", self)
        quit_act.triggered.connect(QApplication.quit)
        menu.addAction(quit_act)
        menu.exec_(event.globalPos())

    def _on_title_change(self, title):
        if title == "KEY:DOWN":
            self.bridge.micChanged.emit(True)
        elif title == "KEY:UP":
            self.bridge.micChanged.emit(False)
        elif title == "MIC:ON":
            print("🎤 开始录音")
            self.bridge.micChanged.emit(True)
        elif title == "MIC:OFF":
            print("🎤 停止录音")
            self.bridge.micChanged.emit(False)
        elif title.startswith("INPUT:"):
            parts = title.split(":", 2)
            if len(parts) >= 3:
                text = parts[2]
                now = time.time()
                if not hasattr(self, "_last_input"):
                    self._last_input = ("", 0)
                if text == self._last_input[0] and now - self._last_input[1] < 1:
                    return
                self._last_input = (text, now)
                print(f"📝 文字输入: {text}")
                self.bridge.textSubmitted.emit(text)

    def toggle_always_on_top(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def set_emotion(self, emotion: str):
        self.webview.page().runJavaScript(f'setEmotion("{emotion}")')

    def start_lip_sync(self):
        self.webview.page().runJavaScript('startLipSync()')

    def stop_lip_sync(self):
        self.webview.page().runJavaScript('stopLipSync()')

    def show_subtitle(self, text: str, duration: float = 0):
        safe = text.replace('"', '\\"').replace('\n', ' ')
        self.webview.page().runJavaScript(f'showSubtitle("{safe}", {duration})')

    def set_status(self, status: str):
        self.webview.page().runJavaScript(f'setStatus("{status}")')
