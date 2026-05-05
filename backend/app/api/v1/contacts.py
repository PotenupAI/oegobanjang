from __future__ import annotations

from fastapi import APIRouter

from app.services.contact_service import list_messages

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("")
def read_contact_messages() -> list[dict[str, object]]:
    return list_messages()
