from __future__ import annotations

from typing import Any


ALLOWED_RISK_TYPES = {
    "missing_documents",
    "visa_expiry_near",
    "insufficient_official_evidence",
    "approval_required_action",
    "unsupported_legal_judgment",
    "unsupported_value_judgment",
    "external_submission_requested",
}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


def normalize_risk_flags(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for flag in flags:
        risk_type = str(flag.get("type", ""))
        level = str(flag.get("level", ""))
        if risk_type not in ALLOWED_RISK_TYPES:
            raise ValueError(f"Unsupported risk flag type: {risk_type}")
        if level not in ALLOWED_RISK_LEVELS:
            raise ValueError(f"Unsupported risk level: {level}")
        normalized.append(
            {
                "type": risk_type,
                "level": level,
                "reason": str(flag.get("reason", "")),
                "source_ids": [str(source_id) for source_id in flag.get("source_ids", [])],
            }
        )
    return normalized
