from __future__ import annotations

from fastapi import APIRouter

from app.services.document_service import list_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def read_documents() -> list[dict[str, object]]:
    return list_documents()
