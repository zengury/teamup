"""Agent 工具 — 文件系统 / bash / web / 委派"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

# ── 工具定义 (给 LLM 的 function definitions) ──────────────────

BASE_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取工作区中的文件内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径，相对于工作区"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入工作区中的文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径，相对于工作区"},
                    "content": {"type": "string", "description": "要写入的内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "精确替换文件中的一段文本。old_str 必须在文件中唯一匹配。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径，相对于工作区"},
                    "old_str": {"type": "string", "description": "要被替换的原文"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "按通配符模式查找文件。例如: glob('*.md') 或 glob('**/*.py')。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "文件通配符模式 (glob pattern)"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "在文件中搜索匹配正则表达式的行。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "正则表达式"},
                    "path": {"type": "string", "description": "搜索路径，相对于工作区"},
                },
                "required": ["pattern", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "在工作区目录中执行 bash 命令。可执行 python 脚本、安装包、运行测试等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "bash 命令。长时间运行的命令请加超时处理。",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索互联网获取最新信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "获取指定 URL 的网页内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL"},
                },
                "required": ["url"],
            },
        },
    },
]

# 唐僧专用的委派工具
DELEGATE_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "delegate_task",
        "description": (
            "委派任务给团队成员。八戒(bajie)负责产品和需求，猴哥(wukong)负责代码实现，"
            "沙僧(shawujing)负责测试，白龙马(bailongma)负责客户成功。"
            "指令需包含：背景、目标、约束条件、验收标准。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["bajie", "wukong", "shawujing", "bailongma"],
                    "description": "要委派的团队成员",
                },
                "task": {
                    "type": "string",
                    "description": "详细的任务描述",
                },
            },
            "required": ["agent", "task"],
        },
    },
}


def tools_for(role: str) -> list[dict]:
    """根据角色返回可用工具列表。"""
    tools = list(BASE_TOOLS)
    if role == "tangseng":
        tools.append(DELEGATE_TOOL)
    return tools


# ── 工具执行 ─────────────────────────────────────────────────


class ToolExecutor:
    """在工作区中执行工具调用。"""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        """解析路径，防止目录穿越。"""
        p = (self.workspace / path).resolve()
        if not str(p).startswith(str(self.workspace)):
            raise ValueError(f"路径越界: {path}")
        return p

    async def execute(self, name: str, arguments: dict) -> str:
        """执行一个工具调用，返回结果字符串。"""
        try:
            if name == "read_file":
                return self._read_file(arguments)
            elif name == "write_file":
                return self._write_file(arguments)
            elif name == "edit_file":
                return self._edit_file(arguments)
            elif name == "glob":
                return self._glob(arguments)
            elif name == "grep":
                return self._grep(arguments)
            elif name == "bash":
                return await self._bash(arguments)
            elif name == "web_search":
                return await self._web_search(arguments)
            elif name == "web_fetch":
                return await self._web_fetch(arguments)
            else:
                return f"未知工具: {name}"
        except Exception as e:
            return f"工具执行错误: {e}"

    def _read_file(self, args: dict) -> str:
        p = self._resolve(args["path"])
        if not p.exists():
            return f"文件不存在: {args['path']}"
        content = p.read_text(encoding="utf-8", errors="replace")
        # 限制返回长度
        max_len = 20000
        if len(content) > max_len:
            content = content[:max_len] + f"\n... (截断，共 {len(content)} 字符)"
        return content

    def _write_file(self, args: dict) -> str:
        p = self._resolve(args["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args["content"], encoding="utf-8")
        return f"已写入: {args['path']} ({len(args['content'])} 字符)"

    def _edit_file(self, args: dict) -> str:
        p = self._resolve(args["path"])
        if not p.exists():
            return f"文件不存在: {args['path']}"
        content = p.read_text(encoding="utf-8")
        old = args["old_str"]
        new = args["new_str"]
        count = content.count(old)
        if count == 0:
            return f"未找到匹配文本: {args['path']}"
        if count > 1:
            return f"匹配到 {count} 处，请提供更精确的原文: {args['path']}"
        content = content.replace(old, new, 1)
        p.write_text(content, encoding="utf-8")
        return f"已编辑: {args['path']}"

    def _glob(self, args: dict) -> str:
        pattern = args["pattern"]
        matches = []
        for p in self.workspace.rglob(pattern):
            rel = p.relative_to(self.workspace)
            matches.append(str(rel))
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return "\n".join(sorted(matches)[:50])

    def _grep(self, args: dict) -> str:
        pattern = args["pattern"]
        search_path = args["path"]
        p = self._resolve(search_path)
        results = []
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"正则错误: {e}"

        def _search_file(fp: Path):
            try:
                for i, line in enumerate(fp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{fp.relative_to(self.workspace)}:{i}: {line[:200]}")
            except Exception:
                pass

        if p.is_file():
            _search_file(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix not in (".pyc", ".pyo", ".so", ".dylib"):
                    _search_file(f)
        else:
            return f"路径不存在: {search_path}"

        if not results:
            return f"未找到匹配 '{pattern}' 的内容"
        return "\n".join(results[:40])

    async def _bash(self, args: dict) -> str:
        command = args["command"]
        timeout = args.get("timeout", 60)

        # 构建完整命令，cd 到工作区
        full_cmd = f"cd {self.workspace} && {command}"

        try:
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "HOME": str(self.workspace)},
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            return f"命令超时 ({timeout}s): {command[:100]}"

        out = stdout.decode("utf-8", errors="replace")
        err = stderr.decode("utf-8", errors="replace")

        parts = []
        if out.strip():
            parts.append(out.strip())
        if err.strip():
            parts.append(f"[stderr]\n{err.strip()}")
        result = "\n".join(parts)

        # 限制长度
        if len(result) > 4000:
            result = result[:4000] + f"\n... (截断，共 {len(result)} 字符)"
        return result or f"命令执行完毕 (rc={proc.returncode})"

    async def _web_search(self, args: dict) -> str:
        query = args["query"]
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "TeamUp/1.0"},
                )
                # 简单提取文本
                text = resp.text
                # 去掉 HTML 标签，取前 3000 字符
                import re as _re
                text = _re.sub(r"<[^>]+>", " ", text)
                text = _re.sub(r"\s+", " ", text).strip()
                return text[:3000] if text else "未找到搜索结果"
        except Exception as e:
            return f"搜索失败: {e}"

    async def _web_fetch(self, args: dict) -> str:
        url = args["url"]
        try:
            import httpx
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "TeamUp/1.0"},
                )
                text = resp.text
                import re as _re
                text = _re.sub(r"<[^>]+>", " ", text)
                text = _re.sub(r"\s+", " ", text).strip()
                return text[:5000] if text else "空页面"
        except Exception as e:
            return f"抓取失败: {e}"
