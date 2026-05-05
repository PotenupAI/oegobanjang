from __future__ import annotations

import json
from typing import Any


def build_judgment_messages(
    *,
    user_message: str,
    detected_intents: list[str],
    evidence_package: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are WorkBridge judgment report generator. "
                "Do not provide final visa eligibility, legal advice, labor advice, "
                "government submission, nationality preference, reliability scoring, "
                "or absconding prediction. "
                "비자 가능 여부 확정, 법률 자문, 노무 자문, 정부 포털 제출, "
                "국적 선호, 성실도 평가, 이탈 예측은 금지됩니다."
            ),
        },
        {
            "role": "developer",
            "content": (
                "Return JSON only. Use the WorkBridgeJudgmentReport schema. "
                "Use only evidence source_ids present in the evidence package. "
                "Set approval_required=true for external messages, expert handoff, exports, "
                "or status completion."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "user_message": user_message,
                    "detected_intents": detected_intents,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
        {
            "role": "evidence",
            "content": json.dumps(evidence_package, ensure_ascii=False, sort_keys=True),
        },
    ]
