from __future__ import annotations

from fastapi import APIRouter

from app.services.company_service import list_companies

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("")
def read_companies() -> list[dict[str, object]]:
    return list_companies()
