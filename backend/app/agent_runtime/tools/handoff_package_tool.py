from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_handoff_package(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing_documents = [str(item) for item in payload.get("missing_documents", [])]
    evidence_source_ids = [str(item) for item in payload.get("evidence_source_ids", [])]

    return {
        "tool_name": "build_handoff_package",
        "status": "draft",
        "case_type": payload.get("case_type"),
        "visa_type": payload.get("visa_type") or "E-9",
        "worker_name": payload.get("worker_name"),
        "sections": [
            {
                "title": "요청 요약",
                "items": [
                    f"case_type={payload.get('case_type')}",
                    f"visa_type={payload.get('visa_type') or 'E-9'}",
                ],
            },
            {
                "title": "누락 서류",
                "items": missing_documents,
            },
            {
                "title": "근거 source_id",
                "items": evidence_source_ids,
            },
        ],
        "missing_documents": missing_documents,
        "evidence_source_ids": evidence_source_ids,
        "approval_required": True,
        "sent": False,
        "exported": False,
        "case_completed": False,
    }
