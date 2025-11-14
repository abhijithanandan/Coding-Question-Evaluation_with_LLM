from __future__ import annotations
from typing import Any, Optional

from .base import BaseProvider
from core.config import ProviderConfig
from utils.parse import normalize_json_response

try:
    from google import genai as google_genai
except Exception:  # pragma: no cover
    google_genai = None


class GoogleProvider(BaseProvider):
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self._client = None

    @classmethod
    def from_env(cls, cfg: ProviderConfig) -> "GoogleProvider":
        if google_genai is None:
            raise RuntimeError("google-genai package not installed")
        if not __import__("os").environ.get("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY not set")
        client = cls(cfg)
        client._client = google_genai.Client()
        return client

    def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_format: Optional[dict] = None,
    ) -> str:
        config = {}
        if response_format and response_format.get("type") == "json_object":
            if self.cfg.json_schema:
                config["response_json_schema"] = self.cfg.json_schema
            config["response_mime_type"] = "application/json"
        if self.cfg.max_output_tokens:
            config["max_output_tokens"] = self.cfg.max_output_tokens
        resp = self._client.models.generate_content(  # type: ignore
            model=self.cfg.model,
            contents=f"{system_prompt}\n\n{user_content}",
            config=config,
        )
        return getattr(resp, "text", "")

    def generate_json(
        self, system_prompt: str, user_content: str, schema: Optional[Any] = None
    ) -> Any:
        raw = self.generate(
            system_prompt,
            user_content,
            response_format=(schema if schema is not None else {"type": "json_object"}),
        )
        return normalize_json_response(
            raw, provider=self.cfg.provider, model=self.cfg.model
        )
