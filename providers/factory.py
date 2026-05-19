import config
from providers.base import LLMProvider
from providers.anthropic_provider import AnthropicProvider
from providers.openai_provider import OpenAIProvider, OpenAICompatibleProvider


_REGISTRY = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "openai_compatible": OpenAICompatibleProvider,
}


def get_provider(role: str) -> LLMProvider:
    cfg = config.get_agent_config(role)
    provider_name = cfg.get("provider", "anthropic")
    if provider_name not in _REGISTRY:
        raise ValueError(
            f"未知 provider: {provider_name}（agent={role}）。"
            f"可选值: {', '.join(_REGISTRY.keys())}"
        )
    return _REGISTRY[provider_name](cfg)
