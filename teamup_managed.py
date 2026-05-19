"""
TeamUp — Managed Agents 运行时 CLI

启动一个对话循环，让顾问与唐僧（协调者）交互。唐僧在 Anthropic 云端运行，
会自动委派八戒 / 猴哥 / 沙僧 / 白龙马。每个客户有独立的 session + memory store，
跨对话保留长期上下文，交付物保存到 session 容器的 /mnt/session/outputs/。

前置: 先跑过 `python setup_managed.py`，生成 .teamup_ids.json。

CLI 命令:
    /new <客户名>     创建新客户（或切换到已存在的客户），开启新 session
    /list             列出所有客户
    /files            列出当前 session 输出的文件
    /download         下载当前 session 输出到 downloads/<客户>/
    /transcript       多行输入模式（粘贴客户对话录音文字稿）
    /console          打印当前 session 在 Anthropic Console 的 URL，可在浏览器观察
    /team             显示团队配置（每个 agent 的 ID / model）
    /quit             退出
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

load_dotenv()
console = Console()
client = anthropic.Anthropic()

IDS_FILE = Path(".teamup_ids.json")
CLIENTS_FILE = Path(".teamup_clients.json")
DOWNLOADS_DIR = Path("downloads")

# ────────────────────────────────────────────────────────────────────────────
# 状态加载
# ────────────────────────────────────────────────────────────────────────────


def load_ids() -> dict:
    if not IDS_FILE.exists():
        console.print(f"[red]未找到 {IDS_FILE}，请先运行 `python setup_managed.py`[/red]")
        raise SystemExit(1)
    return json.loads(IDS_FILE.read_text(encoding="utf-8"))


def load_clients() -> dict:
    if not CLIENTS_FILE.exists():
        return {}
    return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))


def save_clients(clients: dict) -> None:
    CLIENTS_FILE.write_text(
        json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8"
    )


IDS = load_ids()
CLIENTS = load_clients()


# ────────────────────────────────────────────────────────────────────────────
# Session / memory store 管理
# ────────────────────────────────────────────────────────────────────────────


def ensure_memory_store(client_name: str) -> str:
    info = CLIENTS.setdefault(client_name, {})
    if "memory_store_id" in info:
        try:
            client.beta.memory_stores.retrieve(info["memory_store_id"])
            return info["memory_store_id"]
        except anthropic.NotFoundError:
            console.print(f"[yellow]Memory store 失效，重建[/yellow]")

    store = client.beta.memory_stores.create(
        name=f"客户-{client_name}",
        description=(
            f"客户 {client_name} 的跨 session 持久记忆库。包含：业务背景、"
            "已确认需求、历史决策、未解决问题、交付物索引。每次对话开始时先读取，"
            "结束前更新。"
        ),
    )
    info["memory_store_id"] = store.id
    save_clients(CLIENTS)
    console.print(f"[green]✓[/green] 创建 memory store: [cyan]{store.id}[/cyan]")
    return store.id


def create_session(client_name: str) -> str:
    memory_store_id = ensure_memory_store(client_name)
    session = client.beta.sessions.create(
        agent=IDS["agent_ids"]["tangseng"],
        environment_id=IDS["environment_id"],
        title=f"{client_name} - {time.strftime('%Y-%m-%d %H:%M')}",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    f"客户 {client_name} 的长期记忆库。对话开始时先用 glob/read 查看历史，"
                    f"结束前更新关键信息（业务背景、已确认需求、未解决问题、下一步计划）。"
                ),
            }
        ],
    )
    CLIENTS[client_name]["current_session_id"] = session.id
    save_clients(CLIENTS)
    console.print(f"[green]✓[/green] 新 session: [cyan]{session.id}[/cyan]")
    print_console_url(session.id)
    return session.id


def get_or_create_session(client_name: str) -> str:
    info = CLIENTS.get(client_name, {})
    sid = info.get("current_session_id")
    if sid:
        try:
            sess = client.beta.sessions.retrieve(sid)
            if sess.status != "terminated":
                console.print(f"[green]✓[/green] 复用 session: [cyan]{sid}[/cyan] ({sess.status})")
                print_console_url(sid)
                return sid
            console.print(f"[yellow]上一个 session 已终止，创建新 session[/yellow]")
        except anthropic.NotFoundError:
            pass
    return create_session(client_name)


def print_console_url(session_id: str) -> None:
    url = f"https://platform.claude.com/workspaces/default/sessions/{session_id}"
    console.print(f"[dim]在浏览器观察: {url}[/dim]")


# ────────────────────────────────────────────────────────────────────────────
# 事件流处理
# ────────────────────────────────────────────────────────────────────────────


AGENT_STYLES = {
    "唐僧": ("bold red", "🙏"),
    "八戒": ("bold cyan", "💡"),
    "猴哥": ("bold green", "🐒"),
    "沙僧": ("bold yellow", "🧪"),
    "白龙马": ("bold magenta", "🐴"),
}


def render_text_blocks(blocks) -> str:
    parts = []
    for b in blocks:
        if hasattr(b, "type") and b.type == "text":
            parts.append(b.text)
    return "".join(parts)


def chat_turn(session_id: str, user_text: str) -> bool:
    """开 stream → 发消息 → 流式处理事件直到 idle。返回 False 表示 session 已终止。"""
    current_text_open = False  # 是否正在打印 Elon 的 text 流

    with client.beta.sessions.events.stream(session_id=session_id) as stream:
        # stream-first：先打开 stream，再发消息（参考 managed-agents-client-patterns.md Pattern 7）
        client.beta.sessions.events.send(
            session_id=session_id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": user_text}],
                }
            ],
        )

        for event in stream:
            t = event.type

            # Elon 在主 thread 发出的文本
            if t == "agent.message":
                if not current_text_open:
                    console.print("\n[bold red]🙏 唐僧[/bold red]:")
                    current_text_open = True
                text = render_text_blocks(event.content)
                if text:
                    console.print(text, end="")

            # 委派给子 agent
            elif t == "session.thread_created":
                style, icon = AGENT_STYLES.get(
                    getattr(event, "agent_name", ""), ("dim", "●")
                )
                console.print(
                    f"\n[dim]{icon} {getattr(event, 'agent_name', 'unknown')} thread 已创建[/dim]"
                )
                current_text_open = False

            elif t == "agent.thread_message_sent":
                name = getattr(event, "to_agent_name", "?")
                preview = render_text_blocks(getattr(event, "content", []))[:80]
                console.print(
                    f"\n[bold red]🙏 唐僧[/bold red] → [bold]{name}[/bold]: [dim]{preview}…[/dim]"
                )
                current_text_open = False

            elif t == "agent.thread_message_received":
                name = getattr(event, "from_agent_name", "?")
                style, icon = AGENT_STYLES.get(name, ("dim", "●"))
                console.print(f"\n[{style}]{icon} {name}[/{style}] 已交付给 Elon")
                current_text_open = False

            # 工具调用 (一行简短提示，避免刷屏)
            elif t in ("agent.tool_use", "agent.mcp_tool_use"):
                name = getattr(event, "name", "?")
                console.print(f"\n[dim yellow]🔧 {name}[/dim yellow]", end="")
                current_text_open = False

            # 上下文压缩通知
            elif t == "agent.thread_context_compacted":
                console.print("\n[dim]💾 (上下文已压缩)[/dim]")
                current_text_open = False

            # 错误
            elif t == "session.error":
                console.print(
                    f"\n[red]Session 错误: {getattr(event, 'error', event)}[/red]"
                )
                current_text_open = False

            # 状态: 终止
            elif t == "session.status_terminated":
                console.print("\n[red]Session 已终止[/red]")
                return False

            # 状态: idle —— 看 stop_reason 决定是否真正结束这一轮
            elif t == "session.status_idle":
                stop = getattr(event, "stop_reason", None)
                stop_type = getattr(stop, "type", None) if stop else None
                if stop_type == "requires_action":
                    # 等子 agent thread 回到主流程，继续读
                    continue
                console.print()  # 换行收尾
                return True

    return True


# ────────────────────────────────────────────────────────────────────────────
# CLI 命令
# ────────────────────────────────────────────────────────────────────────────


def cmd_list_clients() -> None:
    if not CLIENTS:
        console.print("[yellow]还没有客户。/new <客户名> 开始第一个项目。[/yellow]")
        return
    table = Table(title="客户列表", box=box.ROUNDED)
    table.add_column("客户", style="cyan")
    table.add_column("Memory Store", style="dim")
    table.add_column("当前 Session", style="dim")
    for name, info in CLIENTS.items():
        table.add_row(
            name,
            info.get("memory_store_id", "-"),
            info.get("current_session_id", "-"),
        )
    console.print(table)


def cmd_show_team() -> None:
    table = Table(title="AI 团队 (Managed Agents)", box=box.ROUNDED)
    table.add_column("角色", style="bold")
    table.add_column("Agent ID", style="cyan")
    role_labels = {
        "tangseng": "🙏 唐僧（协调者 / 领队）",
        "bajie": "💡 八戒（产品经理）",
        "wukong": "🐒 猴哥（软件工程师）",
        "shawujing": "🧪 沙僧（QA 工程师）",
        "bailongma": "🐴 白龙马（客户成功）",
    }
    for role, label in role_labels.items():
        table.add_row(label, IDS["agent_ids"].get(role, "(未创建)"))
    console.print(table)
    console.print(f"[dim]Environment: {IDS['environment_id']}[/dim]")


def cmd_list_files(session_id: str | None) -> None:
    if not session_id:
        console.print("[yellow]当前没有活跃 session[/yellow]")
        return
    try:
        files = client.beta.files.list(
            extra_query={"scope_id": session_id},
            extra_headers={"anthropic-beta": "managed-agents-2026-04-01,files-api-2025-04-14"},
        )
    except Exception as e:
        console.print(f"[red]获取文件列表失败: {e}[/red]")
        return

    items = list(files)
    if not items:
        console.print("[yellow]session 还没有输出文件 (确保 agent 写入 /mnt/session/outputs/)[/yellow]")
        return
    table = Table(title=f"Session 输出文件", box=box.ROUNDED)
    table.add_column("文件名", style="cyan")
    table.add_column("大小", style="dim")
    table.add_column("File ID", style="dim")
    for f in items:
        table.add_row(f.filename or "(无名)", f"{f.size_bytes} B", f.id)
    console.print(table)


def cmd_download(session_id: str | None, client_name: str | None) -> None:
    if not session_id:
        console.print("[yellow]当前没有活跃 session[/yellow]")
        return
    target_dir = DOWNLOADS_DIR / (client_name or "default")
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        files = list(client.beta.files.list(
            extra_query={"scope_id": session_id},
            extra_headers={"anthropic-beta": "managed-agents-2026-04-01,files-api-2025-04-14"},
        ))
    except Exception as e:
        console.print(f"[red]获取文件列表失败: {e}[/red]")
        return

    if not files:
        console.print("[yellow]没有可下载的文件[/yellow]")
        return

    for f in files:
        try:
            content = client.beta.files.download(f.id)
            safe_name = os.path.basename(f.filename or f.id)
            content.write_to_file(str(target_dir / safe_name))
            console.print(f"[green]✓[/green] {safe_name} → {target_dir / safe_name}")
        except Exception as e:
            console.print(f"[red]下载 {f.id} 失败: {e}[/red]")


def read_multiline() -> str:
    console.print("[dim]粘贴文字稿，结束后单独一行输入 END 回车:[/dim]")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# 主循环
# ────────────────────────────────────────────────────────────────────────────


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║   TeamUp — AI 交付团队 (Managed Agents)                       ║
║                                                              ║
║   🙏 唐僧  ·  💡 八戒  ·  🐒 猴哥  ·  🧪 沙僧  ·  🐴 白龙马   ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP = """
## 可用命令

- `/new <客户名>`  新客户 / 切换客户
- `/list`         列出客户
- `/team`         查看团队配置
- `/files`        列出当前 session 输出
- `/download`     下载输出到 downloads/<客户>/
- `/transcript`   多行模式（粘贴录音文字稿）
- `/console`      打开当前 session 在 Console 的链接
- `/help`         显示帮助
- `/quit`         退出
"""


def main() -> None:
    console.print(Panel(BANNER, border_style="bold blue"))
    console.print("[dim]输入 /help 查看命令；/new <客户名> 开始第一个项目[/dim]\n")

    current_client: str | None = None
    current_session: str | None = None

    while True:
        try:
            prompt_label = f"[bold blue]{current_client or '未选客户'}[/bold blue]"
            user_input = Prompt.ask(prompt_label).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再见![/dim]")
            break

        if not user_input:
            continue

        if user_input in ("/quit", "/exit"):
            break

        if user_input == "/help":
            console.print(Markdown(HELP))
            continue

        if user_input == "/list":
            cmd_list_clients()
            continue

        if user_input == "/team":
            cmd_show_team()
            continue

        if user_input == "/files":
            cmd_list_files(current_session)
            continue

        if user_input == "/download":
            cmd_download(current_session, current_client)
            continue

        if user_input == "/console":
            if current_session:
                print_console_url(current_session)
            else:
                console.print("[yellow]当前没有 session[/yellow]")
            continue

        if user_input.startswith("/new "):
            current_client = user_input[5:].strip()
            if not current_client:
                console.print("[red]请提供客户名, 例如: /new 客户A[/red]")
                continue
            current_session = get_or_create_session(current_client)
            continue

        # 多行
        if user_input == "/transcript":
            if not current_client:
                console.print("[red]请先 /new <客户名>[/red]")
                continue
            transcript = read_multiline()
            if not transcript.strip():
                continue
            message = f"以下是与客户 {current_client} 的对话录音文字稿，请分析并提炼核心需求：\n\n---\n{transcript}\n---"
            ok = chat_turn(current_session, message)
            if not ok:
                current_session = None
            continue

        # 普通对话
        if not current_client:
            console.print("[red]请先 /new <客户名> 创建/切换客户[/red]")
            continue

        ok = chat_turn(current_session, user_input)
        if not ok:
            current_session = None


if __name__ == "__main__":
    main()
