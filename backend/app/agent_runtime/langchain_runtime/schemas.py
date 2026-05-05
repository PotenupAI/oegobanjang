from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent_runtime.llm.parser import WorkBridgeJudgmentReport


class PolicyDocument(BaseModel):
    page_content: str
    metadata: dict[str, object] = Field(default_factory=dict)


class RetrievedPolicyContext(BaseModel):
    source_id: str
    title: str
    snippet: str
    evidence_grade: str
    score: float | None = None


class LangChainJudgmentResult(BaseModel):
    report: WorkBridgeJudgmentReport
    used_tools: list[str] = Field(default_factory=list)
    retrieved_context: list[RetrievedPolicyContext] = Field(default_factory=list)
