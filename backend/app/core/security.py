from __future__ import annotations

from app.agent_runtime.middleware.pii_filter import mask_payload


def sanitize_for_log(payload: object) -> object:
    return mask_payload(payload)
