"""SAFE_CALCULATE: DB/입력값 기반 계산 전용. 외부 발송·제출 없음."""
import csv
import os
from datetime import date, datetime
from typing import Any
from langchain_core.tools import tool

from app.agent_runtime.schemas.tool import ToolResult, ToolContractLevel, ToolStatus

_SEED_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data-pipeline", "seed")
)


def _read_csv(filename: str) -> list[dict[str, str]]:
    path = os.path.join(_SEED_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_date(s: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


@tool
def calculate_visa_d_day(worker_id: str) -> dict[str, Any]:
    """근로자의 비자 체류 만료까지 남은 일수(D-day)를 계산합니다.

    Args:
        worker_id: 근로자 ID
    """
    workers = _read_csv("workers.csv")
    worker = next((r for r in workers if r.get("id") == worker_id), None)

    if not worker:
        return ToolResult(
            tool_name="calculate_visa_d_day",
            tool_grade=ToolContractLevel.SAFE_CALCULATE,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id},
            error="근로자를 찾을 수 없습니다.",
        ).model_dump()

    expires_at = _parse_date(worker.get("visa_expires_at", ""))
    if not expires_at:
        return ToolResult(
            tool_name="calculate_visa_d_day",
            tool_grade=ToolContractLevel.SAFE_CALCULATE,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id},
            error="체류 만료일 파싱 실패.",
        ).model_dump()

    today = date.today()
    d_day = (expires_at - today).days

    risk_level = "LOW"
    if d_day < 0:
        risk_level = "HIGH"
    elif d_day <= 30:
        risk_level = "HIGH"
    elif d_day <= 90:
        risk_level = "MEDIUM"

    risk_flags = []
    if d_day < 0:
        risk_flags.append(f"체류기간 초과 ({abs(d_day)}일 경과)")
    elif d_day <= 30:
        risk_flags.append(f"체류만료 D-{d_day} 긴급 구간")
    elif d_day <= 90:
        risk_flags.append(f"체류만료 D-{d_day} 주의 구간")

    return ToolResult(
        tool_name="calculate_visa_d_day",
        tool_grade=ToolContractLevel.SAFE_CALCULATE,
        status=ToolStatus.SUCCESS,
        input_snapshot={"worker_id": worker_id},
        output={
            "worker_id": worker_id,
            "visa_type": worker.get("visa_type"),
            "visa_expires_at": worker.get("visa_expires_at"),
            "d_day": d_day,
            "risk_level": risk_level,
            "today": today.isoformat(),
        },
        risk_flags=risk_flags,
    ).model_dump()


@tool
def calculate_missing_documents(worker_id: str, case_type: str) -> dict[str, Any]:
    """근로자의 케이스 유형에 따른 누락 서류를 계산합니다.

    Args:
        worker_id: 근로자 ID
        case_type: 케이스 유형 (stay_extension, workplace_change, renewal 등)
    """
    workers = _read_csv("workers.csv")
    worker = next((r for r in workers if r.get("id") == worker_id), None)
    if not worker:
        return ToolResult(
            tool_name="calculate_missing_documents",
            tool_grade=ToolContractLevel.SAFE_CALCULATE,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id, "case_type": case_type},
            error="근로자를 찾을 수 없습니다.",
        ).model_dump()

    visa_type = worker.get("visa_type", "")

    requirements = _read_csv("document_requirements.csv")
    required = [
        r for r in requirements
        if r.get("visa_type", "").upper() == visa_type.upper()
        and r.get("case_type", "").lower() == case_type.lower()
        and r.get("required", "").lower() == "true"
    ]

    submitted_docs = _read_csv("worker_documents.csv")
    submitted_types = {
        d["doc_type"]
        for d in submitted_docs
        if d.get("worker_id") == worker_id
        and d.get("status", "").upper() in ("SUBMITTED", "APPROVED")
    }

    missing = [r for r in required if r.get("required_doc") not in submitted_types]
    present = [r for r in required if r.get("required_doc") in submitted_types]

    risk_flags = []
    if missing:
        risk_flags.append(f"누락 서류 {len(missing)}건: {[m['required_doc'] for m in missing]}")

    return ToolResult(
        tool_name="calculate_missing_documents",
        tool_grade=ToolContractLevel.SAFE_CALCULATE,
        status=ToolStatus.SUCCESS,
        input_snapshot={"worker_id": worker_id, "case_type": case_type},
        output={
            "worker_id": worker_id,
            "visa_type": visa_type,
            "case_type": case_type,
            "required_count": len(required),
            "present_count": len(present),
            "missing_count": len(missing),
            "missing": [
                {"doc_type": m["required_doc"], "notes": m.get("notes", "")}
                for m in missing
            ],
            "present": [p["required_doc"] for p in present],
        },
        risk_flags=risk_flags,
    ).model_dump()


@tool
def calculate_contract_gap(worker_id: str) -> dict[str, Any]:
    """근로계약 기간과 비자 체류기간의 갭을 계산합니다.

    Args:
        worker_id: 근로자 ID
    """
    workers = _read_csv("workers.csv")
    worker = next((r for r in workers if r.get("id") == worker_id), None)
    if not worker:
        return ToolResult(
            tool_name="calculate_contract_gap",
            tool_grade=ToolContractLevel.SAFE_CALCULATE,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id},
            error="근로자를 찾을 수 없습니다.",
        ).model_dump()

    visa_expires = _parse_date(worker.get("visa_expires_at", ""))
    contract_ends = _parse_date(worker.get("contract_ends_at", ""))

    if not visa_expires or not contract_ends:
        return ToolResult(
            tool_name="calculate_contract_gap",
            tool_grade=ToolContractLevel.SAFE_CALCULATE,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id},
            error="날짜 파싱 실패.",
        ).model_dump()

    gap_days = (contract_ends - visa_expires).days

    risk_flags = []
    if gap_days > 30:
        risk_flags.append(f"계약기간이 체류기간보다 {gap_days}일 초과 — 체류연장 필요")
    elif gap_days < -30:
        risk_flags.append(f"체류기간이 계약기간보다 {abs(gap_days)}일 초과 — 계약 갱신 확인 필요")

    return ToolResult(
        tool_name="calculate_contract_gap",
        tool_grade=ToolContractLevel.SAFE_CALCULATE,
        status=ToolStatus.SUCCESS,
        input_snapshot={"worker_id": worker_id},
        output={
            "worker_id": worker_id,
            "visa_expires_at": worker.get("visa_expires_at"),
            "contract_ends_at": worker.get("contract_ends_at"),
            "gap_days": gap_days,
            "note": "양수=계약이 비자보다 길다, 음수=비자가 계약보다 길다",
        },
        risk_flags=risk_flags,
    ).model_dump()
