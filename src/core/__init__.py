"""Core package exports.

This module makes `src/core` a proper Python package and re-exports
the commonly-used symbols so callers can do::

    from core import LLMClient, ProviderConfig

Keep this file intentionally small to avoid import-time side-effects.
"""

from __future__ import annotations

from .manager import LLMClient  # noqa: F401
from .config import ProviderConfig  # noqa: F401

__all__ = ["LLMClient", "ProviderConfig"]
