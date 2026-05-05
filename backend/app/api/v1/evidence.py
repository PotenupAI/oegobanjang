from __future__ import annotations

from fastapi import APIRouter

from app.schemas.evidence import EvidenceCreate, EvidenceList, EvidenceRead
from app.services.evidence_service import append_evidence, list_evidence

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceRead)
def create_evidence_event(payload: EvidenceCreate) -> EvidenceRead:
    return EvidenceRead.model_validate(append_evidence(payload), from_attributes=True)


@router.get("/{request_id}", response_model=EvidenceList)
def read_evidence_events(request_id: str) -> EvidenceList:
    return EvidenceList(
        events=[
            EvidenceRead.model_validate(record, from_attributes=True)
            for record in list_evidence(request_id)
        ]
    )
