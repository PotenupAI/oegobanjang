from __future__ import annotations

from fastapi import APIRouter

from app.services.worker_service import list_workers

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("")
def read_workers() -> list[dict[str, object]]:
    return list_workers()
