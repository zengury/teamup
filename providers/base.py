from abc import ABC, abstractmethod
from typing import Iterator


class LLMProvider(ABC):
    """所有 LLM provider 的统一接口。

    每个 provider 负责将通用的 (system, user_message) 调用翻译成具体厂商 SDK 的请求格式，
    并以流式方式返回文本片段。返回值是 generator，调用方可边接收边打印。
    """

    def __init__(self, config: dict):
        self.config = config
        self.model: str = config["model"]
        self.max_tokens: int = config.get("max_tokens", 8192)

    @abstractmethod
    def stream(self, system: str, user_message: str) -> Iterator[str]:
        """流式生成回复，逐 token 返回文本片段。"""
        raise NotImplementedError

    def describe(self) -> str:
        provider_name = self.__class__.__name__.replace("Provider", "")
        return f"{provider_name}:{self.model}"
