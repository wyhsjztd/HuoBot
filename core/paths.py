"""
路径工具 — 兼容 PyInstaller 打包和源码运行
"""
import os, sys


def get_base_dir():
    """获取项目根目录（源码运行 = 项目目录，PyInstaller = _internal）"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_path(*parts):
    return os.path.join(get_base_dir(), *parts)
