"""Agent — 单一 AI 角色，带工具执行的对话循环"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Callable

from .config import load_agent_prompt, load_agent_model, get_agent_name
from .llm import chat_stream, chat_complete, _strip_invoke
from .tools import ToolExecutor, tools_for

log = logging.getLogger("teamup.agent")


def _final_clean(text: str) -> str:
    """最终清理：移除 DeepSeek 的 invoke/tool_calls 标签残留"""
    return _strip_invoke(text)


class Agent:
    """一个 AI Agent：system prompt + 工具 + 工作区。"""

    def __init__(self, role: str, workspace: str, memory_context: str = ""):
        self.role = role
        self.name = get_agent_name(role)
        self.model = load_agent_model(role)
        self.workspace = workspace
        self.system_prompt = self._build_system_prompt(memory_context)
        self.tools = tools_for(role)
        self.executor = ToolExecutor(workspace)

    def _build_system_prompt(self, memory_context: str) -> str:
        base = load_agent_prompt(self.role)
        ws_info = f"""
## 当前工作环境

- 工作区路径: {self.workspace}
- 所有文件操作（read_file, write_file, edit_file, glob, grep, bash）都基于此目录
- 最终交付客户的文件请保存到 {self.workspace}/outputs/ 目录
"""
        parts = [base.strip(), ws_info.strip()]
        if memory_context:
            parts.append(f"\n## 客户历史记忆\n\n{memory_context}")
        return "\n\n".join(parts)

    # ── 非流式对话 (可靠，无乱码) ──────────────────────────────

    async def chat_stream_loop(
        self,
        user_message: str,
        history: list[dict],
        on_event: Callable | None = None,
        on_delegate: Callable | None = None,
    ) -> str:
        """
        工具循环对话。使用非流式调用避免 DeepSeek 流式乱码。
        每轮通过 on_event 推送状态和文本。
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        all_text: list[str] = []
        max_rounds = 15
        tool_rounds_this_turn = 0
        total_tool_rounds = 0

        for _round in range(max_rounds):
            # 工具过热保护
            force_text = (tool_rounds_this_turn >= 3) or (total_tool_rounds >= 5)
            active_tools = None if (_round >= max_rounds - 3 or force_text) else self.tools

            # 非流式调用
            if on_event and _round == 0:
                await on_event("agent_status", agent=self.name, status="thinking", activity="思考中")

            resp = await chat_complete(
                model=self.model,
                messages=messages,
                tools=active_tools,
            )

            if resp.get("error"):
                err = f"[错误: {resp['error']}]"
                all_text.append(err)
                if on_event:
                    await on_event("agent_text", agent=self.name, text=err)
                break

            text = resp.get("text", "")
            tool_calls = resp.get("tool_calls", [])

            # 推送文本
            if text:
                all_text.append(text)
                if on_event:
                    await on_event("agent_status", agent=self.name, status="speaking", activity="回复中")
                    await on_event("agent_text", agent=self.name, text=text)

            # 无工具调用 → 结束
            if not tool_calls:
                break

            # ── 推送工具使用进度（仅更新状态卡片，不污染聊天）
            if on_event:
                tool_names = [tc["name"] for tc in tool_calls]
                await on_event("agent_status", agent=self.name, status="working", activity=f"使用: {', '.join(tool_names[:3])}")

            # 跟踪工具使用
            total_tool_rounds += 1
            if text.strip():
                tool_rounds_this_turn = 0
            else:
                tool_rounds_this_turn += 1

            # 构建 assistant 消息
            assistant_msg: dict = {"role": "assistant", "content": text if text else None}
            assistant_msg["tool_calls"] = [
                {
                    "type": "function",
                    "id": tc["id"],
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            # 执行工具
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})

                if on_event:
                    await on_event("tool_use", agent=self.name, tool=tool_name)

                if tool_name == "delegate_task" and on_delegate:
                    result = await on_delegate(tool_args)
                elif tool_name == "delegate_task":
                    result = f"[委派任务给 {tool_args.get('agent', '?')}，等待结果...]"
                else:
                    result = await self.executor.execute(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        return _final_clean("".join(all_text))

    # ── 子 agent 执行 ─────────────────────────────────────────

    async def run_task(self, task: str) -> str:
        """执行独立任务（八戒/猴哥/沙僧/白龙马），返回完整文本。"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]

        full_text: list[str] = []

        for _round in range(15):
            active_tools = self.tools if _round < 12 else None
            resp = await chat_complete(
                model=self.model,
                messages=messages,
                tools=active_tools,
            )

            if resp.get("error"):
                return f"调用失败: {resp['error']}"

            text = resp.get("text", "")
            full_text.append(text)
            tool_calls = resp.get("tool_calls", [])

            if not tool_calls:
                break

            assistant_msg: dict = {"role": "assistant", "content": text if text else None}
            assistant_msg["tool_calls"] = [
                {
                    "type": "function",
                    "id": tc["id"],
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_msg)

            for tc in tool_calls:
                result = await self.executor.execute(tc["name"], tc["arguments"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

        return _final_clean("".join(full_text))
