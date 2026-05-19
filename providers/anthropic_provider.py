from typing import Iterator
import anthropic

import config
from providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, cfg: dict):
        super().__init__(cfg)
        api_key_env = cfg.get("api_key_env", "ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=config.get_api_key(api_key_env))
        self.thinking_mode = cfg.get("thinking")

    def stream(self, system: str, user_message: str) -> Iterator[str]:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_message}],
        }

        if self.thinking_mode == "adaptive":
            kwargs["thinking"] = {"type": "adaptive"}
        elif isinstance(self.thinking_mode, dict):
            kwargs["thinking"] = self.thinking_mode

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
