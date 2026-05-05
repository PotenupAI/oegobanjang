from fastapi import APIRouter
from app.api.v1 import agent

router = APIRouter()
router.include_router(agent.router)
