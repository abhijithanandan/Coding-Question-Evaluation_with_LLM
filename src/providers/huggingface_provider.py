from __future__ import annotations
import os
import json
from typing import Any, Optional

from .base import BaseProvider
from core.config import ProviderConfig
from utils.parse import normalize_json_response

try:
    import requests
except Exception:
    requests = None


class HuggingFaceProvider(BaseProvider):
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg

    @classmethod
    def from_env(cls, cfg: ProviderConfig) -> "HuggingFaceProvider":
        if requests is None:
            raise RuntimeError("requests not installed")
        if not os.getenv("HF_API_KEY"):
            raise RuntimeError("HF_API_KEY not set")
        return cls(cfg)

    def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_format: Optional[dict] = None,
    ) -> Any:
        endpoint = f"https://api-inference.huggingface.co/models/{self.cfg.model}"
        headers = {
            "Authorization": f"Bearer {os.getenv('HF_API_KEY')}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": f"SYSTEM:\n{system_prompt}\nUSER:\n{user_content}",
            "parameters": {"temperature": self.cfg.temperature},
        }
        r = requests.post(
            endpoint, headers=headers, data=json.dumps(payload), timeout=60
        )
        r.raise_for_status()
        data = r.json()
        if (
            isinstance(data, list)
            and data
            and isinstance(data[0], dict)
            and "generated_text" in data[0]
        ):
            return data[0]["generated_text"]
        return json.dumps(data)

    def generate_json(
        self, system_prompt: str, user_content: str, schema: Optional[Any] = None
    ) -> Any:
        raw = self.generate(system_prompt, user_content)
        return normalize_json_response(
            raw, provider=self.cfg.provider, model=self.cfg.model
        )
