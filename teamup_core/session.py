"""会话管理 — 客户端 / session / memory / 文件"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from .config import CLIENTS_FILE, WORKSPACES_DIR

CLIENTS_LOCK = __import__("threading").Lock()


def load_clients() -> dict:
    if CLIENTS_FILE.exists():
        return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
    return {}


def save_clients(clients: dict) -> None:
    with CLIENTS_LOCK:
        CLIENTS_FILE.write_text(
            json.dumps(clients, ensure_ascii=False, indent=2), encoding="utf-8"
        )


class Session:
    """一个客户的一次取经 session。"""

    def __init__(self, client_name: str, session_id: str | None = None):
        self.client_name = client_name
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # 工作区目录
        self.workspace = WORKSPACES_DIR / client_name / self.session_id
        self.outputs_dir = self.workspace / "outputs"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        # 记忆文件
        self.memory_file = WORKSPACES_DIR / client_name / "memory.md"

        # 保存会话元数据
        self._save_meta()

    @property
    def meta_file(self) -> Path:
        return self.workspace / ".session.json"

    @property
    def state_file(self) -> Path:
        return self.workspace / ".state.json"

    def _save_meta(self) -> None:
        self.meta_file.write_text(
            json.dumps(
                {
                    "session_id": self.session_id,
                    "client_name": self.client_name,
                    "created_at": self.created_at,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # ── 会话状态机 ─────────────────────────────────────────

    STAGES = ["init", "prd", "tech_spec", "code", "test", "customer_success", "done"]

    def get_state(self) -> dict:
        """读取当前会话的阶段状态。"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                pass
        return {"stage": "init", "completed": [], "delegated": {}}

    def save_state(self, state: dict) -> None:
        """保存会话状态。"""
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def read_memory(self) -> str:
        """读取客户长期记忆。"""
        if self.memory_file.exists():
            content = self.memory_file.read_text(encoding="utf-8")
            return content[:8000]  # 限制长度
        return ""

    def write_memory(self, notes: str) -> None:
        """追加客户记忆。"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## {ts} (session {self.session_id})\n{notes}"
        with self.memory_file.open("a", encoding="utf-8") as f:
            f.write(entry)

    # ── 对话历史持久化 ─────────────────────────────────────

    @property
    def history_file(self) -> Path:
        return self.workspace / ".chat_history.json"

    def save_history(self, messages: list[dict]) -> None:
        """保存对话历史。"""
        self.history_file.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_history(self) -> list[dict]:
        """加载对话历史。返回 messaage 列表。"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                pass
        return []

    def get_files(self) -> list[dict]:
        """列出 outputs 目录中的文件。"""
        files = []
        if self.outputs_dir.exists():
            for p in self.outputs_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(self.outputs_dir)
                    files.append({
                        "id": str(rel),
                        "name": str(rel),
                        "size": p.stat().st_size,
                    })
        return sorted(files, key=lambda f: f["name"])

    def read_output_file(self, file_id: str) -> bytes:
        """读取 outputs 中的文件内容。"""
        p = (self.outputs_dir / file_id).resolve()
        if not str(p).startswith(str(self.outputs_dir.resolve())):
            raise ValueError("路径越界")
        if not p.exists():
            raise FileNotFoundError(f"文件不存在: {file_id}")
        return p.read_bytes()

    def close(self) -> None:
        """清理 (当前不删数据，保留历史)。"""
        pass


class SessionManager:
    """管理所有客户和 session。"""

    def __init__(self):
        self.clients: dict = load_clients()
        self._current_client: str | None = None
        self._current_session: Session | None = None

    @property
    def current_client(self) -> str | None:
        return self._current_client

    @property
    def current_session(self) -> Session | None:
        return self._current_session

    def list_clients(self) -> list[str]:
        return sorted(self.clients.keys())

    def get_or_create_session(self, client_name: str) -> Session:
        """获取已有 session 或创建新的。"""
        self._current_client = client_name

        info = self.clients.setdefault(client_name, {})
        sid = info.get("current_session_id")

        if sid:
            ws = WORKSPACES_DIR / client_name / sid
            if (ws / ".session.json").exists():
                session = Session(client_name, sid)
                self._current_session = session
                return session

        # 创建新 session
        session = Session(client_name)
        info["current_session_id"] = session.session_id
        save_clients(self.clients)
        self._current_session = session
        return session

    def create_new_session(self, client_name: str) -> Session:
        """强制创建全新 session。"""
        self._current_client = client_name
        session = Session(client_name)
        info = self.clients.setdefault(client_name, {})
        info["current_session_id"] = session.session_id
        save_clients(self.clients)
        self._current_session = session
        return session
