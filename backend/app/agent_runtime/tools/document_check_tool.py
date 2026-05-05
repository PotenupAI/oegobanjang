from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


DEFAULT_REQUIREMENTS_PATH = Path("data-pipeline/seed/document_requirements.csv")


def calculate_missing_documents(
    payload: Mapping[str, Any],
    *,
    requirements_path: str | Path = DEFAULT_REQUIREMENTS_PATH,
) -> dict[str, Any]:
    case_type = str(payload.get("case_type") or "").strip()
    visa_type = str(payload.get("visa_type") or payload.get("visa") or "E-9").strip()
    held_documents = _normalize_documents(
        payload.get("held_documents")
        or payload.get("documents")
        or payload.get("db_document_state")
        or payload.get("document_state")
        or []
    )

    if not case_type:
        return _failed("case_type is required", {"case_type": case_type, "visa_type": visa_type})
    if not visa_type:
        return _failed("visa_type is required", {"case_type": case_type, "visa_type": visa_type})

    requirements = _load_required_documents(Path(requirements_path), case_type=case_type, visa_type=visa_type)
    missing = sorted(doc for doc in requirements if doc not in held_documents)
    risk_flags = ["missing_required_documents"] if missing else []

    return {
        "tool_name": "calculate_missing_documents",
        "tool_grade": "SAFE_CALCULATE",
        "status": "SUCCESS",
        "input_snapshot": {
            "case_type": case_type,
            "visa_type": visa_type,
            "held_documents": sorted(held_documents),
            "document_state_source": _document_state_source(payload),
        },
        "output": {
            "case_type": case_type,
            "visa_type": visa_type,
            "required_documents": sorted(requirements),
            "held_documents": sorted(held_documents),
            "missing_documents": missing,
        },
        "citations": sorted(set(requirements.values())),
        "risk_flags": risk_flags,
        "approval_required": False,
        "error": None,
    }


def _load_required_documents(path: Path, *, case_type: str, visa_type: str) -> dict[str, str]:
    requirements: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("case_type") != case_type:
                continue
            if row.get("visa_type") != visa_type:
                continue
            if str(row.get("required", "")).lower() != "true":
                continue
            doc = str(row.get("required_doc") or "").strip()
            source_id = str(row.get("source_id") or "").strip()
            if doc:
                requirements[doc] = source_id
    return requirements


def _normalize_documents(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        normalized: set[str] = set()
        for key, present in value.items():
            if isinstance(present, Mapping):
                status = str(present.get("status") or present.get("state") or "").lower()
                if status in {"held", "submitted", "available", "complete", "verified"}:
                    normalized.add(str(key))
                continue
            if bool(present):
                normalized.add(str(key))
        return normalized
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value if str(item)}
    return set()


def _document_state_source(payload: Mapping[str, Any]) -> str:
    if payload.get("db_document_state") is not None:
        return "db_document_state"
    if payload.get("document_state") is not None:
        return "document_state"
    if payload.get("held_documents") is not None:
        return "held_documents"
    if payload.get("documents") is not None:
        return "documents"
    return "none"


def _failed(error: str, input_snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool_name": "calculate_missing_documents",
        "tool_grade": "SAFE_CALCULATE",
        "status": "FAILED",
        "input_snapshot": input_snapshot,
        "output": {},
        "citations": [],
        "risk_flags": [],
        "approval_required": False,
        "error": error,
    }
