from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.auth import router as auth_router
from app.api.v1.companies import router as companies_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.health import router as health_router
from app.api.v1.hiring import router as hiring_router
from app.api.v1.visas import router as visas_router
from app.api.v1.workers import router as workers_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(companies_router)
router.include_router(workers_router)
router.include_router(hiring_router)
router.include_router(visas_router)
router.include_router(documents_router)
router.include_router(contacts_router)
router.include_router(approvals_router)
router.include_router(evidence_router)
router.include_router(agent_router)
