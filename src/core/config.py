from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ProviderConfig:
    """Lightweight provider configuration used across provider implementations.

    Attributes:
        provider: provider key (openai, anthropic, google, huggingface, local)
        model: model identifier for the provider
        temperature: sampling temperature
        max_output_tokens: optional maximum tokens to request
        json_schema: optional schema or parse hint for structured outputs
    """

    provider: str
    model: str
    temperature: float = 0.0
    max_output_tokens: Optional[int] = None
    json_schema: Optional[Dict[str, Any]] = None
