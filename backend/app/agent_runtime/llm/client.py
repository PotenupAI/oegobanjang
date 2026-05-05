from __future__ import annotations

from typing import Protocol


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
