from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


AgentStatus = Literal["draft", "executed", "blocked", "mocked", "error"]
RiskLevel = Literal["low", "medium", "high"]


class EvidenceSourceRef(BaseModel):
    source_id: str
    chunk_id: str | None = None
    evidence_grade: str | None = None
    title: str | None = None


class AgentRiskFlag(BaseModel):
    type: str
    level: RiskLevel = "medium"
    reason: str
    source_agent: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class ApprovalRequiredAction(BaseModel):
    action_type: str
    label: str
    reason: str
    source_agent: str


class AgentOutput(BaseModel):
    agent_id: str
    status: AgentStatus = "draft"
    summary: str = ""
    checklist: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    risk_flags: list[AgentRiskFlag] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceRef] = Field(default_factory=list)
    approval_required_actions: list[ApprovalRequiredAction] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AggregatedCaseOutput(BaseModel):
    case_summary: str = ""
    agent_outputs: dict[str, AgentOutput] = Field(default_factory=dict)
    combined_checklist: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    risk_flags: list[AgentRiskFlag] = Field(default_factory=list)
    evidence_sources: list[EvidenceSourceRef] = Field(default_factory=list)
    approval_required: bool = False
    approval_required_actions: list[ApprovalRequiredAction] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def infer_approval_required(self) -> AggregatedCaseOutput:
        if self.approval_required_actions:
            self.approval_required = True
        return self
