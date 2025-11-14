import os
import pytest

from core.manager import ProviderFactory
from core.config import ProviderConfig


def test_provider_factory_unsupported():
    cfg = ProviderConfig(provider="unknown", model="m1")
    with pytest.raises(ValueError):
        ProviderFactory.create(cfg)


def test_provider_factory_missing_envs():
    # Choose a provider that requires an env var (huggingface -> HF_API_KEY)
    cfg = ProviderConfig(provider="huggingface", model="gpt-like")
    # ensure HF_API_KEY is not set for this test
    old = os.environ.pop("HF_API_KEY", None)
    try:
        with pytest.raises(RuntimeError):
            ProviderFactory.create(cfg)
    finally:
        if old is not None:
            os.environ["HF_API_KEY"] = old
