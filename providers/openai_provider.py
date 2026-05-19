from typing import Iterator
from openai import OpenAI

import config
from providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI 官方 API。"""

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        api_key_env = cfg.get("api_key_env", "OPENAI_API_KEY")
        self.client = OpenAI(api_key=config.get_api_key(api_key_env))

    def stream(self, system: str, user_message: str) -> Iterator[str]:
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        for chunk in completion:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI 协议兼容的第三方端点（DeepSeek / Qwen / Moonshot / 智谱 / vLLM 等）。

    通过 base_url 指定具体厂商的网关，复用 openai 官方 SDK 客户端。
    """

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        base_url = cfg.get("base_url")
        if not base_url:
            raise ValueError(
                f"openai_compatible provider 必须在 agents_config.yaml 中设置 base_url（model={self.model}）"
            )
        api_key_env = cfg.get("api_key_env")
        if not api_key_env:
            raise ValueError(
                f"openai_compatible provider 必须设置 api_key_env，指向对应厂商的 API key 环境变量（model={self.model}）"
            )
        self.client = OpenAI(
            api_key=config.get_api_key(api_key_env),
            base_url=base_url,
        )

    def stream(self, system: str, user_message: str) -> Iterator[str]:
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
