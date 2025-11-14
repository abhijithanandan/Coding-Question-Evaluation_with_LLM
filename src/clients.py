"""Thin compatibility facade that exposes LLMClient and ProviderConfig.

This file provides a stable import point for the rest of the project
(`from clients import LLMClient, ProviderConfig`). The implementation is
delegated to modules under `core` and `providers`.
"""

from __future__ import annotations

from core.manager import LLMClient as _LLMClient
from core.config import ProviderConfig

# Re-export the facade names expected by older code
LLMClient = _LLMClient

__all__ = ["LLMClient", "ProviderConfig"]
