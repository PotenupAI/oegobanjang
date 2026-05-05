from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceCreate(BaseModel):
    request_id: str
    event_type: str
    agent_id: str
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceRead(BaseModel):
    event_id: str
    request_id: str
    event_type: str
    agent_id: str
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class EvidenceList(BaseModel):
    events: list[EvidenceRead] = Field(default_factory=list)
