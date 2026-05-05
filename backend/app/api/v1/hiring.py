from __future__ import annotations

from fastapi import APIRouter

from app.services.hiring_service import list_hiring_requests

router = APIRouter(prefix="/hiring", tags=["hiring"])


@router.get("")
def read_hiring_requests() -> list[dict[str, object]]:
    return list_hiring_requests()
