"""
多模型 Provider — 从 providers.json 读取，支持 DeepSeek/Claude/OpenAI 等
"""
import json, os
from openai import OpenAI

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "providers.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_current_provider():
    cfg = load_config()
    current = cfg["current"]
    return cfg["models"].get(current, {})


def get_client():
    """获取当前激活的 OpenAI 兼容客户端"""
    p = get_current_provider()
    return OpenAI(api_key=p.get("key", ""), base_url=p.get("base_url", "")), p.get("model", "deepseek-chat")


def get_all_models():
    cfg = load_config()
    return cfg


def switch_model(name: str):
    cfg = load_config()
    if name in cfg["models"]:
        cfg["current"] = name
        save_config(cfg)
        return True
    return False


def update_key(name: str, key: str):
    cfg = load_config()
    if name in cfg["models"]:
        cfg["models"][name]["key"] = key
        save_config(cfg)
        return True
    return False
