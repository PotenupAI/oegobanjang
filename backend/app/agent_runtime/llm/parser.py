from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


JudgmentStatus = Literal["draft", "blocked", "insufficient_evidence"]
RiskFlagType = Literal[
    "missing_documents",
    "visa_expiry_near",
    "insufficient_official_evidence",
    "approval_required_action",
    "unsupported_legal_judgment",
    "unsupported_value_judgment",
    "external_submission_requested",
]
RiskLevel = Literal["low", "medium", "high"]
ReadinessStatus = Literal["ready", "needs_review", "blocked", "insufficient_evidence"]


class EvidenceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str
    source_id: str
    evidence_grade: Literal["A", "B", "E"]


class RiskFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: RiskFlagType
    level: RiskLevel
    reason: str
    source_ids: list[str] = Field(default_factory=list)


class WorkBridgeJudgmentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: JudgmentStatus
    request_id: str
    case_type: str
    detected_intents: list[str]
    summary: str
    evidence_summary: list[EvidenceSummary]
    risk_flags: list[RiskFlag]
    readiness_status: ReadinessStatus
    missing_inputs: list[str]
    follow_up_questions: list[str]
    approval_required: bool
    blocked: bool
    guardrail_notes: list[str]
    prohibited_actions: list[dict[str, object]]
    next_actions: list[str]


def parse_judgment_json(raw: str) -> WorkBridgeJudgmentReport:
    stripped = raw.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        raise ValueError("Judgment output must be JSON-only.")

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid judgment JSON: {exc}") from exc

    try:
        return WorkBridgeJudgmentReport.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid judgment JSON: {exc}") from exc
