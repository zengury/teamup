#!/usr/bin/env python3
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from agents.elon import ElonAgent
from tools.project_manager import list_projects, save_conversation_history, load_conversation_history

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         TeamUp — AI 交付团队                                   ║
║                                                              ║
║   Elon (CEO)  ·  Jobs (产品)  ·  Linux (工程)                 ║
║   Turing (测试)  ·  Bezos (客户成功)                           ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
## 可用命令

| 命令 | 说明 |
|------|------|
| `/new <项目名>` | 创建或切换到新项目 |
| `/transcript` | 进入多行模式粘贴客户对话录音文字稿 |
| `/status` | 查看当前项目的所有交付文件 |
| `/projects` | 列出所有项目 |
| `/help` | 显示帮助信息 |
| `/quit` 或 `/exit` | 退出程序 |

## 工作流程

1. 使用 `/new <项目名>` 创建客户项目
2. 使用 `/transcript` 粘贴客户对话录音文字稿
3. 与 Elon 讨论并确认需求
4. Elon 会自动指挥团队交付产品文件
5. 使用 `/status` 查看所有交付物
"""


def read_multiline_input() -> str:
    console.print("[dim]请粘贴文字稿内容，完成后在新行输入 END 并按回车:[/dim]")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)


def show_status(agent: ElonAgent) -> None:
    from tools.project_manager import list_files
    files = list_files(agent.project_name)
    if not files:
        console.print(f"[yellow]项目 '{agent.project_name}' 目前没有交付文件。[/yellow]")
        return

    table = Table(title=f"项目: {agent.project_name}", box=box.ROUNDED)
    table.add_column("文件名", style="cyan")
    table.add_column("路径", style="dim")

    from config import PROJECTS_DIR
    for filename in files:
        filepath = PROJECTS_DIR / agent.project_name / filename
        table.add_row(filename, str(filepath))

    console.print(table)


def show_projects() -> None:
    projects = list_projects()
    if not projects:
        console.print("[yellow]还没有任何项目。使用 /new <项目名> 创建第一个项目。[/yellow]")
        return

    table = Table(title="所有项目", box=box.ROUNDED)
    table.add_column("项目名称", style="cyan")

    for project in projects:
        table.add_row(project)

    console.print(table)


def main() -> None:
    console.print(Panel(BANNER, border_style="bold blue"))
    console.print("[dim]输入 /help 查看帮助，输入 /new <项目名> 开始新项目[/dim]\n")

    agent = ElonAgent(project_name="default")

    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]你[/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再见！[/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit"):
            console.print("[dim]再见！[/dim]")
            break

        elif user_input.lower() == "/help":
            console.print(Markdown(HELP_TEXT))

        elif user_input.lower().startswith("/new "):
            project_name = user_input[5:].strip()
            if not project_name:
                console.print("[red]请提供项目名称，例如: /new 客户A-AI客服系统[/red]")
                continue
            agent.set_project(project_name)
            console.print(f"[green]✓ 已切换到项目: {project_name}[/green]")

        elif user_input.lower() == "/transcript":
            transcript = read_multiline_input()
            if not transcript.strip():
                console.print("[yellow]文字稿为空，已取消。[/yellow]")
                continue
            message = f"以下是我与客户的对话录音文字稿，请帮我分析并提炼核心需求：\n\n---\n{transcript}\n---"
            console.print(f"\n[bold red]Elon[/bold red]:")
            response = agent.chat(message)
            console.print(Markdown(response))
            save_conversation_history(agent.project_name, agent.history)

        elif user_input.lower() == "/status":
            show_status(agent)

        elif user_input.lower() == "/projects":
            show_projects()

        else:
            console.print(f"\n[bold red]Elon[/bold red]:")
            response = agent.chat(user_input)
            console.print(Markdown(response))
            save_conversation_history(agent.project_name, agent.history)


if __name__ == "__main__":
    main()
