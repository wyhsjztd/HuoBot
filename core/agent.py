"""
Agent Core — 基于 DeepSeek 原生 Function Calling
参考 EchoBot 的 ToolRegistry + LLMProvider 模式
"""
import os, subprocess, urllib.parse, json
from core.provider import get_client

_client, _model = get_client()

# ===== ToolRegistry (EchoBot风格) =====

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, desc: str, params: dict, func):
        self._tools[name] = {
            "type": "function",
            "function": {"name": name, "description": desc, "parameters": params},
        }
        self._funcs = getattr(self, "_funcs", {})
        self._funcs[name] = func
        setattr(self, "_funcs", self._funcs)

    def get_definitions(self) -> list:
        return list(self._tools.values())

    def execute(self, name: str, args: dict) -> str:
        func = self._funcs.get(name)
        if not func:
            return f"工具{name}不存在"
        try:
            return str(func(**args))
        except Exception as e:
            return f"执行失败: {e}"


registry = ToolRegistry()


def tool(name, desc, params: dict):
    """注册工具到 ToolRegistry"""
    def decorator(func):
        registry.register(name, desc, params, func)
        return func
    return decorator


# ===== 工具定义 (带 JSON Schema 参数) =====

@tool("search_web", "搜索网页获取信息",
    {"type":"object","properties":{"query":{"type":"string","description":"搜索关键词"}},"required":["query"]})
def search_web(query: str) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(f"https://www.bing.com/search?q={urllib.parse.quote(query)}", headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.select("li.b_algo")[:5]
        if not results: return f"未找到'{query}'结果"
        return "\n".join(f"{i+1}. {r.get_text(strip=True)[:200]}" for i, r in enumerate(results))
    except Exception as e:
        return f"搜索失败: {e}"

@tool("open_app", "打开本地电脑程序",
    {"type":"object","properties":{"app_name":{"type":"string","description":"程序名如QQ音乐/微信/记事本"}},"required":["app_name"]})
def open_app(app_name: str) -> str:
    script = (
        '$s=New-Object -ComObject WScript.Shell;'
        f'$kw="*{app_name}*";'
        'foreach($p in @("$env:ProgramData\\Microsoft\\Windows\\Start Menu","$env:APPDATA\\Microsoft\\Windows\\Start Menu","$env:USERPROFILE\\Desktop")){'
        '$fs=Get-ChildItem $p -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue;'
        'foreach($f in $fs){if($f.Name -like $kw){$sc=$s.CreateShortcut($f.FullName);Write-Output $sc.TargetPath;break}}}'
    )
    try:
        r = subprocess.run(["powershell","-Command",script], capture_output=True, text=True, timeout=8)
        target = r.stdout.strip().split('\n')[0].strip()
        if target and os.path.exists(target):
            os.startfile(target)
            return f"已打开{app_name}"
    except: pass
    return f"未找到{app_name}"

@tool("open_website", "打开网站",
    {"type":"object","properties":{"name":{"type":"string","description":"网站名如百度/b站/抖音"}},"required":["name"]})
def open_website(name: str) -> str:
    sites = {"百度":"baidu.com","b站":"bilibili.com","bilibili":"bilibili.com","抖音":"douyin.com","微博":"weibo.com","知乎":"zhihu.com","淘宝":"taobao.com","京东":"jd.com"}
    for k, v in sites.items():
        if k in name.lower(): os.startfile(f"https://www.{v}"); return f"已打开{k}"
    if not name.startswith("http"): name = f"https://www.{name}.com"
    os.startfile(name)
    return f"已打开{name}"

@tool("execute_command", "执行系统命令",
    {"type":"object","properties":{"cmd":{"type":"string","description":"cmd或powershell命令"}},"required":["cmd"]})
def execute_command(cmd: str) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return (r.stdout or r.stderr or "执行完成")[:600]
    except Exception as e:
        return f"执行失败: {e}"

@tool("write_file", "保存文件到桌面",
    {"type":"object","properties":{"filename":{"type":"string","description":"文件名"},"content":{"type":"string","description":"内容"}},"required":["filename","content"]})
def write_file(filename: str, content: str) -> str:
    path = os.path.join(os.environ["USERPROFILE"], "Desktop", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已保存到桌面: {filename}"

@tool("read_file", "读取本地文件内容",
    {"type":"object","properties":{"filepath":{"type":"string","description":"文件完整路径"}},"required":["filepath"]})
def read_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:3000] if len(content) > 3000 else content
    except Exception as e:
        return f"读取失败: {e}"


# ===== Agent Core (EchoBot风格 Function Calling 循环) =====

def execute_agent_task(user_text: str, history: list = None, max_steps: int = 5) -> str:
    """用 DeepSeek 原生 Function Calling 执行任务"""

    messages = [{
        "role": "system",
        "content": """你是藿藿的Agent后台，负责执行电脑操作任务。用户通过藿藿和你交流。
- 调用工具完成任务，完成后用藿藿温柔的语气简短汇报结果
- 不要过度解释，直接做事
- 如果任务不需要工具，直接简短回复"""
    }]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_text})

    tools = registry.get_definitions()
    final_result = ""

    for step in range(max_steps):
        resp = _client.chat.completions.create(
            model=_model,
            messages=messages,
            tools=tools,
            max_tokens=300,
            temperature=0.3,
        )

        msg = resp.choices[0].message

        # 有工具调用
        if msg.tool_calls:
            messages.append({"role": "assistant", "tool_calls": [{
                "id": tc.id, "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
            } for tc in msg.tool_calls], "content": msg.content or ""})

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except:
                    args = {}
                print(f"   🔧 Agent: {tc.function.name}({args})")
                result = registry.execute(tc.function.name, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                final_result = result
        else:
            # 无工具调用，直接回复
            return msg.content.strip() or final_result or "任务完成"

    return final_result or "任务完成"
