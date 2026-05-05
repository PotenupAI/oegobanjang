from __future__ import annotations

import json
from typing import Protocol

from app.agent_runtime.middleware.pii_filter import mask_payload
from app.config import get_settings


class JudgmentClient(Protocol):
    def generate_json(self, messages: list[dict[str, str]]) -> str:
        """Return a JSON-only judgment response."""


class FakeJudgmentClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls = 0
        self.last_messages: list[dict[str, str]] | None = None

    def generate_json(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        self.last_messages = messages
        return self.response_text


class ProviderError(RuntimeError):
    pass


class ProviderTimeout(ProviderError):
    pass


class RealProviderJudgmentClient:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str | None,
        timeout_seconds: float,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.last_messages: list[dict[str, str]] | None = None

    def generate_json(self, messages: list[dict[str, str]]) -> str:
        sanitized_messages = mask_payload(messages)
        self.last_messages = sanitized_messages if isinstance(sanitized_messages, list) else []
        if not self.api_key:
            raise ProviderError(f"{self.provider} provider is enabled but API key is missing")
        # The real network call is intentionally deferred until the provider SDK is installed
        # and REAL_LLM_ENABLED=true is explicitly set in the runtime environment.
        raise ProviderError(f"{self.provider} provider adapter is configured but not activated in tests")


def build_judgment_client(*, fallback_response_text: str) -> JudgmentClient:
    settings = get_settings()
    if not settings.real_llm_enabled:
        return FakeJudgmentClient(fallback_response_text)

    if settings.llm_provider.lower() != "openai":
        raise ProviderError(f"Unsupported LLM provider: {settings.llm_provider}")

    return RealProviderJudgmentClient(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        timeout_seconds=settings.llm_timeout_seconds,
    )


def ensure_json_only(raw: str) -> str:
    stripped = raw.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        raise ProviderError("provider returned non-JSON output")
    try:
        json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"provider returned invalid JSON: {exc}") from exc
    return stripped
