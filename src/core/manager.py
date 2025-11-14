from __future__ import annotations
from typing import Any
from .config import ProviderConfig
from providers import (
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    HuggingFaceProvider,
)


class ProviderFactory:
    """Factory for provider implementations.

    This centralizes mapping from provider name to concrete class. New
    providers can be added here.
    """

    _MAP = {
        "openai": OpenAIProvider,
        "local": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "huggingface": HuggingFaceProvider,
    }

    @classmethod
    def create(cls, cfg: ProviderConfig) -> Any:
        key = cfg.provider.lower()
        impl = cls._MAP.get(key)
        if impl is None:
            raise ValueError(f"Unsupported provider: {cfg.provider}")
        return impl.from_env(cfg)


class LLMClient:
    """Facade client that mirrors the old `LLMClient` behaviour but is
    implemented on top of provider modules.
    """

    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self._provider = None

    @classmethod
    def from_env(cls, cfg: ProviderConfig) -> "LLMClient":
        inst = cls(cfg)
        inst._provider = ProviderFactory.create(cfg)
        return inst

    def generate(
        self, system_prompt: str, user_content: str, response_format: Any = None
    ):
        return self._provider.generate(system_prompt, user_content, response_format)

    def generate_json(self, system_prompt: str, user_content: str, schema: Any = None):
        return self._provider.generate_json(system_prompt, user_content, schema)
