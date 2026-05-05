from __future__ import annotations

from fastapi import APIRouter

from app.services.visa_service import list_visas

router = APIRouter(prefix="/visas", tags=["visas"])


@router.get("")
def read_visas() -> list[dict[str, object]]:
    return list_visas()
