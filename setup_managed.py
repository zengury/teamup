"""
TeamUp — Managed Agents 一次性 setup 脚本

读取 agents_yaml/ 下的定义，在 Anthropic Managed Agents 平台创建：
  - 1 个 environment
  - 4 个专业 agent（jobs / linux / turing / bezos）
  - 1 个 coordinator agent（elon），其 multiagent.agents 引用上面四位

创建后把 ID 写到 .teamup_ids.json，供 teamup_managed.py 在运行时加载。

幂等：如果 .teamup_ids.json 里已记录的资源仍存在于 Anthropic 端，本脚本不会重复创建。

运行：
    pip install -r requirements.txt
    cp .env.example .env  # 填入 ANTHROPIC_API_KEY
    python setup_managed.py

可选：本脚本也可以替换成 `ant beta:agents create < agents_yaml/jobs.agent.yaml`
等 CLI 命令（推荐用于 CI/CD），见 https://platform.claude.com/docs/en/api/sdks/cli
"""

import json
from pathlib import Path

import anthropic
import yaml
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()
client = anthropic.Anthropic()

IDS_FILE = Path(".teamup_ids.json")
YAML_DIR = Path("agents_yaml")
PROMPTS_DIR = Path("prompts")


def load_ids() -> dict:
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text(encoding="utf-8"))
    return {"environment_id": None, "agent_ids": {}}


def save_ids(ids: dict) -> None:
    IDS_FILE.write_text(json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")


def load_yaml(filename: str) -> dict:
    return yaml.safe_load((YAML_DIR / filename).read_text(encoding="utf-8"))


def load_prompt(path: str) -> str:
    # path 形如 "prompts/elon.md"
    return Path(path).read_text(encoding="utf-8")


def ensure_environment(ids: dict) -> str:
    if ids.get("environment_id"):
        try:
            env = client.beta.environments.retrieve(ids["environment_id"])
            console.print(f"[green]✓[/green] Environment 已存在: [cyan]{env.id}[/cyan] ({env.name})")
            return env.id
        except anthropic.NotFoundError:
            console.print("[yellow]环境 ID 失效，重新创建[/yellow]")

    cfg = load_yaml("environment.yaml")
    env = client.beta.environments.create(
        name=cfg["name"],
        config={
            "type": "cloud",
            "networking": cfg.get("networking", {"type": "unrestricted"}),
        },
    )
    console.print(f"[green]✓[/green] Environment 已创建: [cyan]{env.id}[/cyan]")
    ids["environment_id"] = env.id
    save_ids(ids)
    return env.id


def build_agent_kwargs(cfg: dict, multiagent_resolved: list[str] | None = None) -> dict:
    kwargs: dict = {
        "name": cfg["name"],
        "model": cfg["model"],
        "tools": cfg.get("tools", [{"type": "agent_toolset_20260401"}]),
    }
    if "system_prompt_file" in cfg:
        kwargs["system"] = load_prompt(cfg["system_prompt_file"])
    if "skills" in cfg:
        kwargs["skills"] = cfg["skills"]
    if multiagent_resolved:
        kwargs["multiagent"] = {
            "type": "coordinator",
            "agents": multiagent_resolved,
        }
    return kwargs


def ensure_agent(role: str, ids: dict, multiagent_resolved: list[str] | None = None) -> str:
    existing = ids["agent_ids"].get(role)
    if existing:
        try:
            agent = client.beta.agents.retrieve(existing)
            console.print(f"[green]✓[/green] Agent [bold]{role}[/bold] 已存在: [cyan]{agent.id}[/cyan]")
            return agent.id
        except anthropic.NotFoundError:
            console.print(f"[yellow]Agent {role} ID 失效，重新创建[/yellow]")

    cfg = load_yaml(f"{role}.agent.yaml")
    agent = client.beta.agents.create(**build_agent_kwargs(cfg, multiagent_resolved))
    console.print(f"[green]✓[/green] Agent [bold]{role}[/bold] 已创建: [cyan]{agent.id}[/cyan] (model={cfg['model']})")
    ids["agent_ids"][role] = agent.id
    save_ids(ids)
    return agent.id


def main() -> None:
    console.print("[bold blue]TeamUp — Managed Agents Setup[/bold blue]\n")

    ids = load_ids()
    ensure_environment(ids)

    console.print("\n[bold]第一步: 创建专业 agent[/bold]")
    for role in ["jobs", "linux", "turing", "bezos"]:
        ensure_agent(role, ids)

    console.print("\n[bold]第二步: 创建协调者 Elon（引用上面 4 位）[/bold]")
    elon_cfg = load_yaml("elon.agent.yaml")
    subagent_names = elon_cfg.get("multiagent_subagents", [])
    roster = [ids["agent_ids"][name] for name in subagent_names]
    if not roster:
        raise ValueError("elon.agent.yaml 中 multiagent_subagents 为空")
    ensure_agent("elon", ids, multiagent_resolved=roster)

    console.print("\n[bold green]✅ Setup 完成[/bold green]")
    console.print(f"所有 ID 已写入 [cyan]{IDS_FILE}[/cyan]")
    console.print("\n下一步: [bold]python teamup_managed.py[/bold]")


if __name__ == "__main__":
    main()
