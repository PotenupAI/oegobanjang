from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED", "CANCELLED"]


class ApprovalCreate(BaseModel):
    request_id: str
    action_type: str
    reason: str | None = None


class ApprovalDecision(BaseModel):
    status: Literal["APPROVED", "REJECTED", "CANCELLED"]


class ApprovalRead(BaseModel):
    approval_id: str
    request_id: str
    action_type: str
    status: ApprovalStatus = "PENDING"
    reason: str | None = None


class ApprovalList(BaseModel):
    approvals: list[ApprovalRead] = Field(default_factory=list)
