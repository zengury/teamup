import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

_CONFIG_FILE = Path("agents_config.yaml")


def load_agent_configs() -> dict:
    if not _CONFIG_FILE.exists():
        raise FileNotFoundError(f"配置文件不存在: {_CONFIG_FILE}")
    with _CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_agent_config(role: str) -> dict:
    configs = load_agent_configs()
    if role not in configs:
        raise KeyError(f"agents_config.yaml 中找不到角色: {role}")
    return configs[role]


def get_api_key(env_name: str) -> str:
    key = os.getenv(env_name, "")
    if not key:
        raise RuntimeError(f"环境变量 {env_name} 未设置，请检查 .env 文件")
    return key
