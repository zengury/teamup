"""
TeamUp Server — 开放架构版 (DeepSeek)

启动一个 FastAPI 服务，浏览器访问 http://localhost:8000 即可看到西天取经控制台。

用法:
    pip install -r requirements.txt
    cp .env.example .env   # 填入 DEEPSEEK_API_KEY
    python server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from teamup_core.orchestrator import Orchestrator
from teamup_core.session import SessionManager
from teamup_core.config import TEAM, STATIC_DIR

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("teamup")

STATIC_DIR.mkdir(exist_ok=True)

# ── 全局状态 ─────────────────────────────────────────────────

session_mgr = SessionManager()
ACTIVE_TURN = False
LAST_STATE = {
    "current_client": None,
    "current_session": None,
    "agent_status": {
        "唐僧": {"status": "idle", "activity": ""},
        "八戒": {"status": "idle", "activity": ""},
        "猴哥": {"status": "idle", "activity": ""},
        "沙僧": {"status": "idle", "activity": ""},
        "白龙马": {"status": "idle", "activity": ""},
    },
}
WEBSOCKETS: set[WebSocket] = set()
EVENT_LOOP: asyncio.AbstractEventLoop | None = None
EVENT_QUEUE: asyncio.Queue | None = None


# ── 事件推送 ─────────────────────────────────────────────────


def push_event(event_type: str, **payload) -> None:
    if EVENT_LOOP is None or EVENT_QUEUE is None:
        return
    msg = {"type": event_type, "ts": time.time(), **payload}
    _apply_local_state(msg)
    EVENT_LOOP.call_soon_threadsafe(EVENT_QUEUE.put_nowait, msg)


def _apply_local_state(msg: dict) -> None:
    global ACTIVE_TURN
    t = msg["type"]
    if t == "agent_status":
        name = msg.get("agent")
        if name in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][name] = {
                "status": msg.get("status", "idle"),
                "activity": msg.get("activity", ""),
            }
    elif t == "turn_started":
        ACTIVE_TURN = True
        for k in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][k] = {"status": "idle", "activity": ""}
        LAST_STATE["agent_status"]["唐僧"] = {"status": "thinking", "activity": "理解需求"}
    elif t in ("session_idle", "turn_ended", "session_terminated"):
        ACTIVE_TURN = False
        for k in LAST_STATE["agent_status"]:
            LAST_STATE["agent_status"][k] = {"status": "idle", "activity": ""}


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


# ── 后台工作线程 ─────────────────────────────────────────────


def chat_turn_worker(client_name: str, user_text: str) -> None:
    """后台线程：运行一轮 orchestration，推送事件。"""
    global ACTIVE_TURN
    try:
        session = session_mgr.get_or_create_session(client_name)
        LAST_STATE["current_client"] = client_name
        LAST_STATE["current_session"] = session.session_id

        push_event("turn_started", user_text=user_text)
        push_event("user_message", text=user_text)

        # 在后台线程中运行 async 编排
        async def _run():
            orch = Orchestrator(session)
            return await orch.run_turn(
                user_message=user_text,
                on_event=_async_event_callback,
            )

        result = asyncio.run(_run())
        log.info(f"turn complete: {len(result)} chars, preview: {(result or '')[:80]}")

        # 输出文件更新
        files = session.get_files()
        push_event("files_updated", files=files)

    except Exception as e:
        log.exception("chat_turn_worker 失败")
        push_event("error", message=str(e))
    finally:
        push_event("turn_ended")
        push_event("session_idle")
        ACTIVE_TURN = False


async def _async_event_callback(event_type: str, **payload) -> None:
    """从 async 上下文推送事件。"""
    push_event(event_type, **payload)


# ── FastAPI ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global EVENT_LOOP, EVENT_QUEUE
    EVENT_LOOP = asyncio.get_running_loop()
    EVENT_QUEUE = asyncio.Queue()
    asyncio.create_task(_broadcast_worker())
    log.info("TeamUp 控制台已启动 → http://localhost:8000")
    yield


app = FastAPI(title="TeamUp Control Plane", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/state")
async def api_state() -> dict:
    return {
        "clients": session_mgr.list_clients(),
        "current_client": LAST_STATE["current_client"],
        "current_session": LAST_STATE["current_session"],
        "active_turn": ACTIVE_TURN,
        "agent_status": LAST_STATE["agent_status"],
        "team": TEAM,
    }


@app.post("/api/client/select")
async def api_client_select(payload: dict) -> dict:
    name = (payload or {}).get("name", "").strip()
    if not name:
        raise HTTPException(400, "name required")
    session = session_mgr.get_or_create_session(name)
    LAST_STATE["current_client"] = name
    LAST_STATE["current_session"] = session.session_id
    push_event("client_selected", client=name, session_id=session.session_id)
    # 推送历史消息
    history = session.load_history()
    if history:
        push_event("history_loaded", messages=history)
    files = session.get_files()
    if files:
        push_event("files_updated", files=files)
    return {"client": name, "session_id": session.session_id}


@app.post("/api/client/new")
async def api_client_new(payload: dict) -> dict:
    name = (payload or {}).get("name", "").strip()
    if not name:
        raise HTTPException(400, "name required")
    session = session_mgr.create_new_session(name)
    LAST_STATE["current_client"] = name
    LAST_STATE["current_session"] = session.session_id
    push_event("client_selected", client=name, session_id=session.session_id)
    return {"client": name, "session_id": session.session_id}


@app.post("/api/message")
async def api_message(payload: dict) -> dict:
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(400, "text required")
    if ACTIVE_TURN:
        raise HTTPException(409, "团队还在取经，请稍候")
    client_name = LAST_STATE["current_client"]
    if not client_name:
        raise HTTPException(400, "请先选择客户")
    threading.Thread(
        target=chat_turn_worker, args=(client_name, text), daemon=True
    ).start()
    return {"ok": True, "session_id": LAST_STATE["current_session"]}


@app.get("/api/files")
async def api_files() -> list[dict]:
    session = session_mgr.current_session
    if not session:
        return []
    return session.get_files()


@app.get("/api/file/{file_id:path}")
async def api_file_download(file_id: str):
    session = session_mgr.current_session
    if not session:
        raise HTTPException(404, "没有活跃 session")
    try:
        data = session.read_output_file(file_id)
    except Exception as e:
        raise HTTPException(404, str(e))
    return StreamingResponse(
        iter([data]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{Path(file_id).name}"'
        },
    )


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    WEBSOCKETS.add(ws)
    try:
        await ws.send_json({
            "type": "hello",
            "ts": time.time(),
            "state": LAST_STATE,
            "active_turn": ACTIVE_TURN,
            "clients": session_mgr.list_clients(),
        })
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("ws error")
    finally:
        WEBSOCKETS.discard(ws)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
