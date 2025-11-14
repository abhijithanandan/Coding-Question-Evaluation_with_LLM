from __future__ import annotations
import os
import time
import random
from collections import deque
from typing import Any, Dict, Optional
import threading
import logging

from .base import BaseProvider
from core.config import ProviderConfig
from utils.parse import normalize_json_response

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


class OpenAIProvider(BaseProvider):
    def __init__(self, cfg: ProviderConfig):
        self.cfg = cfg
        self._client = None
        self._last_call_time = 0.0
        self._lock = threading.Lock()
        self._req_times = deque()
        model_name = (getattr(cfg, "model", None) or "").lower()
        env_rpm = os.getenv("LLM_RPM") or os.getenv("LLM_REQUESTS_PER_MINUTE")
        if env_rpm:
            try:
                self._rpm = int(env_rpm)
            except Exception:
                self._rpm = 0
        elif model_name and "gpt-5" in model_name:
            self._rpm = 500
        else:
            self._rpm = 0

    @classmethod
    def from_env(cls, cfg: ProviderConfig) -> "OpenAIProvider":
        if OpenAI is None:
            raise RuntimeError("openai package not installed")
        client = cls(cfg)
        api_key = (
            os.getenv("OPENAI_API_KEY")
            if cfg.provider == "openai"
            else os.getenv("LOCAL_LLM_API_KEY", "none")
        )
        base_url = (
            os.getenv("OPENAI_BASE_URL")
            if cfg.provider == "openai"
            else os.getenv("LOCAL_LLM_BASE_URL")
        )
        client._client = OpenAI(api_key=api_key, base_url=base_url)  # type: ignore
        return client

    def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_format: Optional[Dict] = None,
    ) -> Any:
        params = {
            "model": self.cfg.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        # if self.cfg.temperature is not None:
        #     params["temperature"] = self.cfg.temperature

        params["text_format"] = response_format

        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        initial_backoff = float(os.getenv("LLM_INITIAL_BACKOFF", "1.0"))
        backoff_multiplier = float(os.getenv("LLM_BACKOFF_MULTIPLIER", "2.0"))
        min_delay_between_calls = float(os.getenv("LLM_MIN_DELAY_BETWEEN_CALLS", "0.5"))

        attempt = 0
        last_exc = None
        while attempt <= max_retries:
            wait_for_rpm = 0.0
            with getattr(self, "_lock"):
                now = time.time()
                while self._req_times and (now - self._req_times[0]) >= 60.0:
                    self._req_times.popleft()

                if self._rpm and len(self._req_times) >= self._rpm:
                    next_allowed = self._req_times[0] + 60.0
                    wait_for_rpm = max(0.0, next_allowed - now)
                    self._req_times.append(now + wait_for_rpm)
                else:
                    self._req_times.append(now)

                elapsed = now - getattr(self, "_last_call_time", 0.0)
                wait_for_spacing = max(0.0, min_delay_between_calls - elapsed)
                self._last_call_time = now + max(wait_for_rpm, wait_for_spacing)

            total_wait = max(wait_for_rpm, wait_for_spacing)
            if total_wait > 0:
                time.sleep(total_wait)

            try:
                resp = self._client.responses.parse(**params)  # type: ignore
                with getattr(self, "_lock"):
                    self._last_call_time = time.time()
                    while (
                        self._req_times and (time.time() - self._req_times[0]) >= 60.0
                    ):
                        self._req_times.popleft()

                result = resp.output_parsed
                try:
                    if hasattr(result, "score"):
                        score = getattr(result, "score")
                    if hasattr(result, "breakdown") and getattr(result, "breakdown"):
                        breakdown = getattr(result, "breakdown")
                except Exception:
                    score = None
                    breakdown = None

                return score, breakdown
            except Exception as e:
                last_exc = e
                retryable = False
                name = type(e).__name__
                msg = str(e).lower()
                if (
                    "rate" in name.lower()
                    or "rate" in msg
                    or "429" in msg
                    or "too many requests" in msg
                ):
                    retryable = True

                if not retryable:
                    raise

                if attempt == max_retries:
                    break

                backoff = initial_backoff * (backoff_multiplier**attempt)
                jitter = random.uniform(0, 0.1 * backoff)
                wait_time = backoff + jitter
                logger.warning(
                    "Transient error calling provider '%s'. Retrying in %.2fs (attempt %d/%d).",
                    self.cfg.provider,
                    wait_time,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(wait_time)
                attempt += 1

        if last_exc:
            raise last_exc

    def generate_json(
        self, system_prompt: str, user_content: str, schema: Optional[Any] = None
    ) -> Dict:
        rf = (
            schema
            if schema is not None
            else (
                self.cfg.json_schema
                if self.cfg.json_schema is not None
                else {"type": "json_object"}
            )
        )
        raw = self.generate(system_prompt, user_content, response_format=rf)
        return normalize_json_response(
            raw, provider=self.cfg.provider, model=self.cfg.model
        )
