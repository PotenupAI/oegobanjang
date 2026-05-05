from __future__ import annotations

from fastapi import APIRouter

from app.schemas.agent import AgentRunRequest
from app.services.agent_service import run_agent_request

router = APIRouter()


@router.post("/agent/run")
def run_agent(request: AgentRunRequest) -> dict[str, object]:
    return run_agent_request(request.model_dump())
