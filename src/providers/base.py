from __future__ import annotations
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract provider interface. Concrete providers must implement
    `from_env`, `generate`, and may override `generate_json` when needed.
    """

    cfg: Any

    @classmethod
    @abstractmethod
    def from_env(cls, cfg: Any) -> "BaseProvider":
        raise NotImplementedError()

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_format: Optional[Dict] = None,
    ) -> Any:
        raise NotImplementedError()

    def generate_json(
        self, system_prompt: str, user_content: str, schema: Optional[Any] = None
    ) -> Any:
        """Default JSON generation pipeline: call generate and attempt to coerce to JSON/dict.

        Providers may override for SDK-specific parsing.
        """
        return self.generate(
            system_prompt,
            user_content,
            response_format=(schema or {"type": "json_object"}),
        )
