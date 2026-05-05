from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.approval import ApprovalCreate, ApprovalDecision, ApprovalList, ApprovalRead
from app.services.approval_service import create_approval, decide_approval, get_approval, list_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalRead)
def create_approval_request(payload: ApprovalCreate) -> ApprovalRead:
    return ApprovalRead.model_validate(create_approval(payload), from_attributes=True)


@router.get("", response_model=ApprovalList)
def list_approval_requests(request_id: str | None = None) -> ApprovalList:
    return ApprovalList(
        approvals=[
            ApprovalRead.model_validate(record, from_attributes=True)
            for record in list_approvals(request_id)
        ]
    )


@router.get("/{approval_id}", response_model=ApprovalRead)
def read_approval_request(approval_id: str) -> ApprovalRead:
    record = get_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="approval not found")
    return ApprovalRead.model_validate(record, from_attributes=True)


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
def decide_approval_request(approval_id: str, payload: ApprovalDecision) -> ApprovalRead:
    record = decide_approval(approval_id, payload)
    if record is None:
        raise HTTPException(status_code=404, detail="approval not found")
    return ApprovalRead.model_validate(record, from_attributes=True)
