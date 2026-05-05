"""SAFE_DRAFT: 초안 생성만. 외부 발송·제출 없음. 발송은 APPROVAL_REQUIRED tool에서."""
import json
import os
from typing import Any
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent_runtime.schemas.tool import ToolResult, ToolContractLevel, ToolStatus
from app.config import get_settings

_SEED_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data-pipeline", "seed")
)

_SUPPORTED_LANGUAGES = {
    "ko": "한국어",
    "vi": "베트남어",
    "km": "크메르어 (캄보디아)",
    "uz": "우즈베크어",
    "ne": "네팔어",
    "id": "인도네시아어",
}


def _load_templates() -> list[dict]:
    path = os.path.join(_SEED_DIR, "message_templates.jsonl")
    if not os.path.exists(path):
        return []
    templates = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    templates.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return templates


@tool
def generate_multilingual_message_draft(
    purpose: str,
    language: str,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """다국어 메시지 초안을 생성합니다. 발송은 담당자 승인 후 별도 tool로 수행합니다.

    Args:
        purpose: 메시지 목적 (document_request, visa_extension_notice, contract_termination)
        language: 언어 코드 (ko, vi, km, uz, ne, id)
        variables: 템플릿 변수 {'deadline': '2026-06-01', 'date': '2026-06-01'} 등
    """
    templates = _load_templates()
    matched = next(
        (t for t in templates if t.get("language") == language and t.get("purpose") == purpose),
        None,
    )

    if not matched:
        return ToolResult(
            tool_name="generate_multilingual_message_draft",
            tool_grade=ToolContractLevel.SAFE_DRAFT,
            status=ToolStatus.FAILED,
            input_snapshot={"purpose": purpose, "language": language},
            error=f"'{purpose}' + '{language}' 조합의 템플릿을 찾을 수 없습니다.",
        ).model_dump()

    content = matched["content"]
    if variables:
        for key, value in variables.items():
            content = content.replace(f"[{key}]", value)
            content = content.replace(f"[{key.upper()}]", value)

    lang_name = _SUPPORTED_LANGUAGES.get(language, language)

    return ToolResult(
        tool_name="generate_multilingual_message_draft",
        tool_grade=ToolContractLevel.SAFE_DRAFT,
        status=ToolStatus.SUCCESS,
        input_snapshot={"purpose": purpose, "language": language, "variables": variables},
        output={
            "draft": content,
            "language": language,
            "language_name": lang_name,
            "purpose": purpose,
            "approval_required": True,
            "note": "이 초안은 담당자 검토 후 발송 승인이 필요합니다.",
        },
    ).model_dump()


@tool
def generate_expert_handoff_package_draft(
    worker_id: str,
    case_type: str,
    notes: str = "",
) -> dict[str, Any]:
    """행정사/노무사 전달용 케이스 패키지 초안을 생성합니다. 전달은 담당자 승인 후 수행합니다.

    Args:
        worker_id: 근로자 ID
        case_type: 케이스 유형 (stay_extension, workplace_change, renewal)
        notes: 추가 메모
    """
    import csv as csv_mod

    def read_csv(fname):
        p = os.path.join(_SEED_DIR, fname)
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as f:
            return list(csv_mod.DictReader(f))

    workers = read_csv("workers.csv")
    worker = next((r for r in workers if r.get("id") == worker_id), None)
    if not worker:
        return ToolResult(
            tool_name="generate_expert_handoff_package_draft",
            tool_grade=ToolContractLevel.SAFE_DRAFT,
            status=ToolStatus.FAILED,
            input_snapshot={"worker_id": worker_id, "case_type": case_type},
            error="근로자를 찾을 수 없습니다.",
        ).model_dump()

    submitted_docs = [
        d for d in read_csv("worker_documents.csv")
        if d.get("worker_id") == worker_id
    ]

    requirements = [
        r for r in read_csv("document_requirements.csv")
        if r.get("visa_type", "").upper() == worker.get("visa_type", "").upper()
        and r.get("case_type", "").lower() == case_type.lower()
    ]

    submitted_types = {
        d["doc_type"]
        for d in submitted_docs
        if d.get("status", "").upper() in ("SUBMITTED", "APPROVED")
    }
    missing = [r["required_doc"] for r in requirements if r.get("required_doc") not in submitted_types]

    package = {
        "case_type": case_type,
        "worker_summary": {
            "name": worker.get("name"),
            "nationality": worker.get("nationality"),
            "visa_type": worker.get("visa_type"),
            "visa_expires_at": worker.get("visa_expires_at"),
            "contract_ends_at": worker.get("contract_ends_at"),
        },
        "submitted_documents": [d["doc_type"] for d in submitted_docs],
        "missing_documents": missing,
        "notes": notes,
        "approval_required": True,
        "note": "이 패키지는 담당자 검토 후 행정사/노무사에게 전달 승인이 필요합니다.",
    }

    risk_flags = []
    if missing:
        risk_flags.append(f"누락 서류 {len(missing)}건 있음: {missing}")

    return ToolResult(
        tool_name="generate_expert_handoff_package_draft",
        tool_grade=ToolContractLevel.SAFE_DRAFT,
        status=ToolStatus.SUCCESS,
        input_snapshot={"worker_id": worker_id, "case_type": case_type},
        output=package,
        risk_flags=risk_flags,
    ).model_dump()
