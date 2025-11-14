from __future__ import annotations
from typing import Any, Optional

from .base import BaseProvider
from core.config import ProviderConfig
from utils.parse import normalize_json_response

try:
    import anthropic
except Exception:  # pragma: no cover
    anthropic = None


class AnthropicProvider(BaseProvider):
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self._client = None

    @classmethod
    def from_env(cls, cfg: ProviderConfig) -> "AnthropicProvider":
        if anthropic is None:
            raise RuntimeError("anthropic package not installed")
        client = cls(cfg)
        client._client = anthropic.Anthropic(api_key=__import__("os").environ.get("ANTHROPIC_API_KEY"))  # type: ignore
        return client

    def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_format: Optional[dict] = None,
    ) -> str:
        messages = [{"role": "user", "content": f"{system_prompt}\n\n{user_content}"}]
        resp = self._client.messages.create(  # type: ignore
            model=self.cfg.model,
            max_tokens=self.cfg.max_output_tokens or 1024,
            temperature=self.cfg.temperature,
            messages=messages,
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")  # type: ignore

    def generate_json(
        self, system_prompt: str, user_content: str, schema: Optional[Any] = None
    ) -> Any:
        raw = self.generate(system_prompt, user_content)
        return normalize_json_response(
            raw, provider=self.cfg.provider, model=self.cfg.model
        )
