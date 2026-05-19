"""
TeamUp Control Plane — 西天取经团队实时可视化

启动一个 FastAPI 服务，浏览器访问 http://localhost:8000 即可看到：
  - 唐僧居中、四徒弟环列的"取经地图"
  - 任务分派、并行执行、交付物的实时流转
  - 顾问对话面板（粘贴录音文字稿、下指令）
  - 交付物列表（自动从 session outputs 拉取）

后端把 Anthropic Managed Agents 的 session event stream 实时翻译成简化事件，
通过 WebSocket 广播给所有连接的浏览器。

前置: 先运行 `python setup_managed.py` 生成 .teamup_ids.json。

运行:
    pip install -r requirements.txt
    python teamup_server.py
    # 然后浏览器打开 http://localhost:8000
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import anthropic
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("teamup")

client = anthropic.Anthropic()

IDS_FILE = Path(".teamup_ids.json")
CLIENTS_FILE = Path(".teamup_clients.json")
STATIC_DIR = Path("static")
DOWNLOADS_DIR = Path("downloads")

if not IDS_FILE.exists():
    raise SystemExit("未找到 .teamup_ids.json — 请先运行 `python setup_managed.py`")

IDS = json.loads(IDS_FILE.read_text(encoding="utf-8"))


def load_clients() -> dict:
    if CLIENTS_FILE.exists():
        return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
    return {}


def save_clients(clients: dict) -> None:
    CLIENTS_FILE.write_text(
        json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8"
    )


CLIENTS: dict = load_clients()


# ────────────────────────────────────────────────────────────────────────────
# 异步事件广播
# ────────────────────────────────────────────────────────────────────────────

EVENT_LOOP: asyncio.AbstractEventLoop | None = None
EVENT_QUEUE: asyncio.Queue | None = None
WEBSOCKETS: set[WebSocket] = set()
# 简单的服务端状态镜像，新连进来的浏览器能立刻看到上次的状态
LAST_STATE = {
    "current_client": None,
    "current_session": None,
    "agent_status": {  # agent name -> {status, activity}
        "唐僧": {"status": "idle", "activity": ""},
        "八戒": {"status": "idle", "activity": ""},
        "猴哥": {"status": "idle", "activity": ""},
        "沙僧": {"status": "idle", "activity": ""},
        "白龙马": {"status": "idle", "activity": ""},
    },
}


def push_event(event_type: str, **payload) -> None:
    """线程安全：从任意线程把事件推入 asyncio 队列以便广播。"""
    if EVENT_LOOP is None or EVENT_QUEUE is None:
        return
    msg = {"type": event_type, "ts": time.time(), **payload}
    # 本地状态同步
    _apply_local_state(msg)
    try:
        asyncio.run_coroutine_threadsafe(EVENT_QUEUE.put(msg), EVENT_LOOP)
    except RuntimeError:
        pass


def _apply_local_state(msg: dict) -> None:
    t = msg["type"]
    if t == "agent_status":
        name = msg.get("agent")
        if name in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][name] = {
                "status": msg.get("status", "idle"),
                "activity": msg.get("activity", ""),
            }
    elif t == "turn_started":
        # 一轮开始：所有非唐僧重置为待命，唐僧 thinking
        for k in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][k] = {"status": "idle", "activity": ""}
        LAST_STATE["agent_status"]["唐僧"] = {"status": "thinking", "activity": "理解需求"}
    elif t in ("session_idle", "turn_ended"):
        for k in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][k] = {"status": "idle", "activity": ""}


# ────────────────────────────────────────────────────────────────────────────
# Anthropic 资源管理
# ────────────────────────────────────────────────────────────────────────────


def ensure_memory_store(client_name: str) -> str:
    info = CLIENTS.setdefault(client_name, {})
    if "memory_store_id" in info:
        try:
            client.beta.memory_stores.retrieve(info["memory_store_id"])
            return info["memory_store_id"]
        except anthropic.NotFoundError:
            log.info("memory store 失效，重建: %s", client_name)

    store = client.beta.memory_stores.create(
        name=f"客户-{client_name}",
        description=(
            f"客户 {client_name} 的跨 session 持久记忆库。包含：业务背景、"
            "已确认需求、历史决策、未解决问题、交付物索引。"
        ),
    )
    info["memory_store_id"] = store.id
    save_clients(CLIENTS)
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
                    "结束前更新关键信息（业务背景、已确认需求、未解决问题、下一步计划）。"
                ),
            }
        ],
    )
    CLIENTS[client_name]["current_session_id"] = session.id
    save_clients(CLIENTS)
    return session.id


def get_or_create_session(client_name: str) -> str:
    info = CLIENTS.get(client_name, {})
    sid = info.get("current_session_id")
    if sid:
        try:
            sess = client.beta.sessions.retrieve(sid)
            if sess.status != "terminated":
                return sid
        except anthropic.NotFoundError:
            pass
    return create_session(client_name)


# ────────────────────────────────────────────────────────────────────────────
# 事件翻译：Anthropic stream → 浏览器友好事件
# ────────────────────────────────────────────────────────────────────────────


def render_text_blocks(blocks) -> str:
    parts = []
    for b in blocks or []:
        if hasattr(b, "type") and b.type == "text":
            parts.append(getattr(b, "text", ""))
    return "".join(parts)


def handle_stream_event(event: Any) -> None:
    t = getattr(event, "type", None)

    if t == "agent.message":
        text = render_text_blocks(getattr(event, "content", []))
        if text:
            push_event("agent_text", agent="唐僧", text=text)
            push_event("agent_status", agent="唐僧", status="speaking", activity="正在回复顾问")

    elif t == "session.thread_created":
        name = getattr(event, "agent_name", "?")
        push_event("thread_created", agent=name)
        push_event("agent_status", agent=name, status="working", activity="thread 已开启")

    elif t == "agent.thread_message_sent":
        to_name = getattr(event, "to_agent_name", "?")
        text = render_text_blocks(getattr(event, "content", []))
        push_event(
            "delegation",
            from_agent="唐僧",
            to_agent=to_name,
            text=text,
        )
        push_event("agent_status", agent="唐僧", status="delegating", activity=f"派任务给 {to_name}")
        push_event("agent_status", agent=to_name, status="working", activity=(text[:40] or "执行中"))

    elif t == "agent.thread_message_received":
        from_name = getattr(event, "from_agent_name", "?")
        text = render_text_blocks(getattr(event, "content", []))
        push_event(
            "delegation_reply",
            from_agent=from_name,
            to_agent="唐僧",
            text=text,
        )
        push_event("agent_status", agent=from_name, status="delivered", activity="已交付")
        push_event("agent_status", agent="唐僧", status="thinking", activity=f"接收 {from_name} 的成果")

    elif t in ("agent.tool_use", "agent.mcp_tool_use"):
        agent_name = getattr(event, "agent_name", "唐僧") or "唐僧"
        tool_name = getattr(event, "name", "?")
        push_event("tool_use", agent=agent_name, tool=tool_name)
        push_event("agent_status", agent=agent_name, status="working", activity=f"使用 {tool_name}")

    elif t == "agent.thread_context_compacted":
        push_event("compacted")

    elif t == "session.error":
        push_event("error", message=str(getattr(event, "error", event)))

    elif t == "session.status_terminated":
        push_event("session_terminated")

    elif t == "session.status_idle":
        stop = getattr(event, "stop_reason", None)
        stop_type = getattr(stop, "type", None) if stop else None
        if stop_type != "requires_action":
            push_event("session_idle")


def chat_turn_worker(session_id: str, user_text: str) -> None:
    """后台线程：开 stream + 发消息 + 翻译事件。"""
    push_event("turn_started", user_text=user_text)
    try:
        with client.beta.sessions.events.stream(session_id=session_id) as stream:
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
                handle_stream_event(event)
                etype = getattr(event, "type", None)
                if etype == "session.status_terminated":
                    break
                if etype == "session.status_idle":
                    stop = getattr(event, "stop_reason", None)
                    if getattr(stop, "type", None) != "requires_action":
                        break
    except Exception as e:
        log.exception("chat_turn_worker 失败")
        push_event("error", message=str(e))
    finally:
        push_event("turn_ended")
        # 推一遍最新文件列表
        try:
            files = list_session_files(session_id)
            push_event("files_updated", files=files)
        except Exception as e:
            log.warning("拉取 file list 失败: %s", e)


# ────────────────────────────────────────────────────────────────────────────
# 文件
# ────────────────────────────────────────────────────────────────────────────


def list_session_files(session_id: str) -> list[dict]:
    files = client.beta.files.list(
        extra_query={"scope_id": session_id},
        extra_headers={
            "anthropic-beta": "managed-agents-2026-04-01,files-api-2025-04-14"
        },
    )
    return [
        {"id": f.id, "name": f.filename or f.id, "size": getattr(f, "size_bytes", 0)}
        for f in files
    ]


# ────────────────────────────────────────────────────────────────────────────
# FastAPI
# ────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="TeamUp Control Plane")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
async def _startup() -> None:
    global EVENT_LOOP, EVENT_QUEUE
    EVENT_LOOP = asyncio.get_running_loop()
    EVENT_QUEUE = asyncio.Queue()
    asyncio.create_task(_broadcast_worker())
    log.info("TeamUp 控制台已启动 → http://localhost:8000")


async def _broadcast_worker() -> None:
    assert EVENT_QUEUE is not None
    while True:
        msg = await EVENT_QUEUE.get()
        dead = []
        for ws in list(WEBSOCKETS):
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            WEBSOCKETS.discard(ws)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/state")
async def api_state() -> dict:
    return {
        "clients": list(CLIENTS.keys()),
        "current_client": LAST_STATE["current_client"],
        "current_session": LAST_STATE["current_session"],
        "agent_status": LAST_STATE["agent_status"],
        "team": [
            {"role": "tangseng", "name": "唐僧", "title": "协调者", "icon": "🙏", "model": "claude-opus-4-5"},
            {"role": "bajie", "name": "八戒", "title": "产品经理", "icon": "💡", "model": "claude-sonnet-4-6"},
            {"role": "wukong", "name": "猴哥", "title": "软件工程师", "icon": "🐒", "model": "claude-opus-4-7"},
            {"role": "shawujing", "name": "沙僧", "title": "QA 工程师", "icon": "🧪", "model": "claude-sonnet-4-6"},
            {"role": "bailongma", "name": "白龙马", "title": "客户成功", "icon": "🐴", "model": "claude-sonnet-4-6"},
        ],
    }


@app.post("/api/client/select")
async def api_client_select(payload: dict) -> dict:
    name = (payload or {}).get("name", "").strip()
    if not name:
        raise HTTPException(400, "name required")
    sid = get_or_create_session(name)
    LAST_STATE["current_client"] = name
    LAST_STATE["current_session"] = sid
    push_event("client_selected", client=name, session_id=sid)
    try:
        files = list_session_files(sid)
        push_event("files_updated", files=files)
    except Exception as e:
        log.warning("拉取 file list 失败: %s", e)
    return {"client": name, "session_id": sid}


@app.post("/api/message")
async def api_message(payload: dict) -> dict:
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(400, "text required")
    sid = LAST_STATE["current_session"]
    if not sid:
        raise HTTPException(400, "请先选择客户")
    push_event("user_message", text=text)
    threading.Thread(target=chat_turn_worker, args=(sid, text), daemon=True).start()
    return {"ok": True, "session_id": sid}


@app.get("/api/files")
async def api_files() -> list[dict]:
    sid = LAST_STATE["current_session"]
    if not sid:
        return []
    try:
        return list_session_files(sid)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/file/{file_id}")
async def api_file_download(file_id: str):
    try:
        content = client.beta.files.download(file_id)
    except Exception as e:
        raise HTTPException(404, str(e))
    # content has read() / iter_bytes() depending on SDK version; try read
    data = content.read() if hasattr(content, "read") else bytes(content)
    return StreamingResponse(iter([data]), media_type="application/octet-stream",
                             headers={"Content-Disposition": f'attachment; filename="{file_id}"'})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    WEBSOCKETS.add(ws)
    # 把当前状态先推一份给新连接
    try:
        await ws.send_json({"type": "hello", "ts": time.time(), "state": LAST_STATE})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("ws error")
    finally:
        WEBSOCKETS.discard(ws)


if __name__ == "__main__":
    STATIC_DIR.mkdir(exist_ok=True)
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
