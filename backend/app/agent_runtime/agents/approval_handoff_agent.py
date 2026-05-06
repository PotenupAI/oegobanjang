from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.agent_runtime.schemas.agent_output import AgentOutput, ApprovalRequiredAction


ACTION_LABELS = {
    "send_worker_message": "외국인 근로자에게 메시지 발송",
    "send_expert_package": "행정사/노무사에게 패키지 전달",
    "complete_case": "케이스 상태 완료 처리",
    "export_external_document": "대외 제출용 문서 export",
    "government_portal_submission": "정부 포털 제출",
}


def prepare_approval_handoff(request: Mapping[str, Any]) -> AgentOutput:
    requested_actions = _requested_actions(request)
    actions = [
        ApprovalRequiredAction(
            action_type=action_type,
            label=ACTION_LABELS.get(action_type, action_type),
            reason="외부 발송, 전달, 제출, 완료 처리는 담당자 승인 이후에만 가능합니다.",
            source_agent="approval_handoff_agent",
        )
        for action_type in requested_actions
    ]

    return AgentOutput(
        agent_id="approval_handoff_agent",
        status="draft",
        summary="사람 승인 또는 전문가 전달이 필요한 작업을 승인 대기 상태로 정리했습니다.",
        checklist=[
            "승인 필요한 외부 작업 식별",
            "실제 발송, 전달, 제출, 완료 처리는 실행하지 않음",
            "담당자 승인 후 별도 실행 대기",
        ],
        approval_required_actions=actions,
        next_actions=["담당자가 승인 대기 작업을 검토하고 승인 또는 반려해 주세요."],
        raw={
            "requested_actions": requested_actions,
            "sent": False,
            "exported": False,
            "case_completed": False,
        },
    )


def _requested_actions(request: Mapping[str, Any]) -> list[str]:
    explicit = request.get("requested_actions")
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]

    detected_intents = set(request.get("detected_intents", []))
    user_message = str(request.get("user_message") or "").lower()
    actions: list[str] = []
    if "CONTACT" in detected_intents or any(word in user_message for word in ("메시지", "문자", "카톡", "보내", "발송")):
        actions.append("send_worker_message")
    if any(word in user_message for word in ("행정사", "노무사", "패키지", "전달", "전송")):
        actions.append("send_expert_package")
    if "완료" in user_message:
        actions.append("complete_case")
    if "export" in user_message or "내보내" in user_message:
        actions.append("export_external_document")
    return list(dict.fromkeys(actions or ["send_expert_package"]))
