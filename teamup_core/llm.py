"""LLM 客户端 — DeepSeek (OpenAI 兼容协议)"""

from __future__ import annotations

import re
from typing import AsyncIterator

from openai import AsyncOpenAI

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

# DeepSeek 流式输出会在文本中夹带 <invoke>/＜invoke＞ XML 标签，需过滤
# 用简单规则：跳过含 "invoke" 或 "tool_calls" 的行/块
import re as _re
# 旧正则已废弃，现在用 _strip_invoke 做彻底清理

def _strip_invoke(text: str) -> str:
    """彻底移除 DeepSeek 输出的所有 invoke/tool_calls/XML 标签残留"""
    # 统一各种「像 < >」的 Unicode 字符
    text = text.replace('\uff1c', '<').replace('\uff1e', '>')
    text = text.replace('\u3008', '<').replace('\u3009', '>')
    # ｜invoke → <invoke (处理顺序很重要：先闭合标签后开放标签)
    text = text.replace('</｜invoke', '</invoke').replace('</｜tool_calls', '</tool_calls')
    text = text.replace('｜invoke', '<invoke').replace('｜/invoke', '</invoke')
    text = text.replace('｜tool_calls', '<tool_calls').replace('｜/tool_calls', '</tool_calls')
    # 移除 invoke/tool_calls 块
    text = _re.sub(r'<invoke[^>]*>.*?</invoke>', '', text, flags=_re.DOTALL)
    text = _re.sub(r'<tool_calls>.*?</tool_calls>', '', text, flags=_re.DOTALL)
    # 移除任何残留的 XML/HTML 标签
    text = _re.sub(r'</?[^>]*>', '', text)
    # 移除乱码标记
    text = _re.sub(r'[｜]{2,}', '', text)
    text = text.replace('DSML', '')
    # 合并多余空行
    text = _re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


# ── 流式聊天 ─────────────────────────────────────────────────


async def chat_stream(
    *,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> AsyncIterator[dict]:
    """
    流式调用 LLM，yield 每个 chunk dict:
      {"type": "text", "text": "..."}
      {"type": "tool_call_start", "id": "...", "name": "..."}
      {"type": "tool_call_arg", "id": "...", "text": "..."}
      {"type": "tool_call_end", "id": "..."}
      {"type": "finish", "finish_reason": "..."}
      {"type": "error", "message": "..."}
    """
    client = get_client()
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    try:
        stream = await client.chat.completions.create(**kwargs)
    except Exception as e:
        yield {"type": "error", "message": str(e)}
        return

    current_tool_id: str | None = None
    current_tool_name: str | None = None
    tool_args_buf: dict[str, str] = {}

    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            finish = chunk.choices[0].finish_reason

            # ── 文本 ──
            if delta.content:
                yield {"type": "text", "text": delta.content}

            # ── tool calls ──
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.id:
                        # 新的 tool call 开始
                        if current_tool_id and current_tool_id != tc.id:
                            yield {"type": "tool_call_end", "id": current_tool_id}
                        current_tool_id = tc.id
                        tool_args_buf[current_tool_id] = tool_args_buf.get(current_tool_id, "")
                        # 只发一次 start
                        if tc.function and tc.function.name:
                            current_tool_name = tc.function.name
                            yield {
                                "type": "tool_call_start",
                                "id": current_tool_id,
                                "name": current_tool_name,
                            }
                    if tc.function and tc.function.arguments:
                        tool_args_buf[tc.id] = tool_args_buf.get(tc.id, "") + tc.function.arguments
                        yield {
                            "type": "tool_call_arg",
                            "id": tc.id,
                            "text": tc.function.arguments,
                        }

            # ── finish ──
            if finish:
                if current_tool_id:
                    yield {"type": "tool_call_end", "id": current_tool_id}
                yield {"type": "finish", "finish_reason": finish}
                return

    except Exception as e:
        yield {"type": "error", "message": str(e)}


# ── 非流式聊天 (用于子 agent，不需要流式给前端) ──────────────


async def chat_complete(
    *,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> dict:
    """
    非流式调用，返回:
      {"text": "...", "tool_calls": [{"id": "...", "name": "...", "arguments": {...}}]}
    """
    client = get_client()
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    try:
        resp = await client.chat.completions.create(**kwargs)
    except Exception as e:
        return {"text": "", "tool_calls": [], "error": str(e)}

    msg = resp.choices[0].message
    result: dict = {"text": _strip_invoke(msg.content or ""), "tool_calls": []}

    if msg.tool_calls:
        for tc in msg.tool_calls:
            import json
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            result["tool_calls"].append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": args,
            })

    return result
