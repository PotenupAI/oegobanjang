from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_id: str | None = None
    user_id: str | None = None
    company_id: str | None = None
    user_message: str | None = None
    case_type: str | None = None
    current_state: str | None = None
    runtime_mode: Literal["deterministic", "langchain_judgment"] = "deterministic"
    input_state: dict[str, Any] = Field(default_factory=dict)
    human_approved: bool = False
    retrieved_evidence: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    case_type: str | None = None
    current_state: str | None = None
    next_state: str | None = None
    approval_required: bool | None = None
