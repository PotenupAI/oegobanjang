from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any


def calculate_visa_timeline(payload: Mapping[str, Any]) -> dict[str, Any]:
    today = _parse_date(payload.get("today")) or date.today()
    visa_expires_at = _parse_date(payload.get("visa_expires_at") or payload.get("stay_expires_at"))
    contract_ends_at = _parse_date(payload.get("contract_ends_at") or payload.get("contract_end_date"))

    if visa_expires_at is None:
        return {
            "status": "needs_more_information",
            "d_day": None,
            "risk_flags": ["missing_visa_expiry_date"],
            "follow_up_questions": ["체류만료일을 입력해 주세요."],
        }

    d_day = (visa_expires_at - today).days
    risk_flags: list[str] = []
    follow_up_questions: list[str] = []

    if d_day < 0:
        risk_flags.append("visa_expired")
        follow_up_questions.append("체류만료일이 지났습니다. 행정사 검토가 필요합니다.")
    elif d_day <= 14:
        risk_flags.append("visa_expiry_urgent")
    elif d_day <= 60:
        risk_flags.append("visa_expiry_near")
    elif d_day <= 90:
        risk_flags.append("visa_expiry_watch")

    contract_conflict = False
    if contract_ends_at is not None and contract_ends_at > visa_expires_at:
        contract_conflict = True
        risk_flags.append("contract_after_visa_expiry")
        follow_up_questions.append("계약종료일이 체류만료일보다 늦습니다. 담당자 확인이 필요합니다.")

    return {
        "status": "calculated",
        "today": today.isoformat(),
        "visa_expires_at": visa_expires_at.isoformat(),
        "contract_ends_at": contract_ends_at.isoformat() if contract_ends_at else None,
        "d_day": d_day,
        "contract_conflict": contract_conflict,
        "risk_flags": risk_flags,
        "follow_up_questions": follow_up_questions,
    }


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None
