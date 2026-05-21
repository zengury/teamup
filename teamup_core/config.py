"""TeamUp 核心配置"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

# ── DeepSeek / LLM ──────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ── 路径 ─────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
WORKSPACES_DIR = ROOT / "workspaces"
PROMPTS_DIR = ROOT / "prompts"
YAML_DIR = ROOT / "agents_yaml"
STATIC_DIR = ROOT / "static"
CLIENTS_FILE = ROOT / ".teamup_clients.json"

# ── 团队定义 ─────────────────────────────────────────────────
TEAM = [
    {"role": "tangseng", "name": "唐僧", "title": "协调者", "icon": "🙏", "model": DEEPSEEK_MODEL},
    {"role": "bajie",    "name": "八戒", "title": "产品经理",   "icon": "💡", "model": DEEPSEEK_MODEL},
    {"role": "wukong",   "name": "猴哥", "title": "软件工程师", "icon": "🐒", "model": DEEPSEEK_MODEL},
    {"role": "shawujing","name": "沙僧", "title": "QA 工程师",  "icon": "🧪", "model": DEEPSEEK_MODEL},
    {"role": "bailongma","name": "白龙马","title": "客户成功",   "icon": "🐴", "model": DEEPSEEK_MODEL},
]

# Agent role → display name 映射
AGENT_DISPLAY: dict[str, str] = {m["role"]: m["name"] for m in TEAM}


def load_agent_prompt(role: str) -> str:
    """读取 agent 的 system prompt。"""
    path = PROMPTS_DIR / f"{role}.md"
    if not path.exists():
        raise FileNotFoundError(f"未找到 prompt 文件: {path}")
    return path.read_text(encoding="utf-8")


def load_agent_yaml(role: str) -> dict:
    path = YAML_DIR / f"{role}.agent.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_agent_model(role: str) -> str:
    """从 yaml 或默认配置读取 agent 使用的 model。"""
    cfg = load_agent_yaml(role)
    return cfg.get("model", DEEPSEEK_MODEL)


def get_agent_name(role: str) -> str:
    return AGENT_DISPLAY.get(role, role)
