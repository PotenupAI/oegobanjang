from __future__ import annotations

from typing import Any


def success_response(data: Any = None, *, request_id: str | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {"ok": True, "data": data}
    if request_id:
        response["request_id"] = request_id
    return response


def error_response(
    code: str,
    message: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if request_id:
        response["request_id"] = request_id
    return response
