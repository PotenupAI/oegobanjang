from __future__ import annotations

from fastapi import APIRouter

from app.services.auth_service import issue_local_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/local-token")
def create_local_token(user_id: str = "local_user") -> dict[str, str]:
    return issue_local_token(user_id)
