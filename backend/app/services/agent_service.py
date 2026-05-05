from __future__ import annotations

from typing import Any

from app.agent_runtime.graph.workflow import run_workflow


def run_agent_request(payload: dict[str, Any] | None) -> dict[str, Any]:
    return run_workflow(payload)
