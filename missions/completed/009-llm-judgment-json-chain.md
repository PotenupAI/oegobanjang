# Mission 009: LLM Judgment JSON Chain

## Goal

RAG Evidence Package를 입력으로 받아 LLM 판단 JSON을 생성, 파싱, 검증하는 체인을 만든다.

실제 LLM API 호출보다 출력 계약이 먼저다. 이 mission은 prompt template, judgment JSON schema, parser, fake LLM client, post-LLM guardrail을 구현해 실제 provider 연결 전에도 deterministic하게 테스트할 수 있는 판단 체인을 만드는 것이 목적이다.

---

## Required Reading

```txt
AGENTS.md
docs/PROJECT_BRIEF.md
docs/ARCHITECTURE.md
docs/AI_OS_DESIGN.md
docs/RAG_STRATEGY.md
docs/TOOL_CONTRACT.md
docs/SECURITY_GUARDRAILS.md
docs/EVIDENCE_LOG_SCHEMA.md
missions/active/008-rag-evidence-package.md
missions/completed/001-agent-runtime-skeleton.md
```

---

## Target Files

```txt
backend/app/agent_runtime/llm/prompts.py
backend/app/agent_runtime/llm/client.py
backend/app/agent_runtime/llm/judgment_chain.py
backend/app/agent_runtime/llm/parser.py

backend/app/agent_runtime/schemas/response.py
backend/app/agent_runtime/guardrails.py

backend/tests/test_llm_judgment_chain.py
backend/tests/test_guardrails.py
backend/tests/test_agent_workflow.py
```

---

## Scope

이번 mission에서 구현할 범위는 다음과 같다.

- LLM prompt template 정의
- system/developer/user/evidence 구간 분리
- judgment JSON schema 정의
- `status`, `request_id`, `case_type`, `detected_intents`, `evidence_summary`, `risk_flags`, `approval_required`, `prohibited_actions`, `next_actions` 필드 고정
- fake LLM client 구현
- JSON-only parser 구현
- JSON 외 텍스트, 필드 누락, 잘못된 enum 거절
- LLM 결과에 대한 guardrail 재검사
- candidate ranking, 법적 확정, 자동 제출, 국적 선호, 이탈 예측이 LLM 출력에 나타나면 block

---

## Out of Scope

이번 mission에서 구현하지 않는다.

- 실제 OpenAI 또는 외부 LLM API 호출
- provider별 credential 관리
- streaming response
- 사용자용 리포트 렌더링
- frontend 연동
- RAG 검색 품질 고도화

---

## Judgment JSON Contract

```json
{
  "status": "draft",
  "request_id": "req_001",
  "case_type": "new_hiring",
  "detected_intents": ["HIRING", "VISA_CHECK"],
  "evidence_summary": [
    {
      "claim": "E-9 신규 채용은 고용허가 절차 확인이 필요합니다.",
      "source_id": "seed_eps_procedure_demo_001",
      "evidence_grade": "B"
    }
  ],
  "risk_flags": [
    {
      "type": "missing_documents",
      "level": "medium",
      "reason": "여권 사본 제출 여부가 확인되지 않았습니다.",
      "source_ids": ["document_requirement_001"]
    }
  ],
  "approval_required": true,
  "prohibited_actions": [],
  "next_actions": [
    "담당자가 누락 서류를 확인합니다.",
    "근로자에게 보낼 메시지 초안을 승인합니다."
  ]
}
```

Allowed `status`:

```txt
draft
blocked
insufficient_evidence
```

Allowed `risk_flags.type`:

```txt
missing_documents
visa_expiry_near
insufficient_official_evidence
approval_required_action
unsupported_legal_judgment
unsupported_value_judgment
external_submission_requested
```

Allowed `risk_flags.level`:

```txt
low
medium
high
```

---

## Acceptance Criteria

- Prompt builder가 system/developer/user/evidence 메시지를 분리한다.
- Judgment JSON parser가 필수 필드 누락을 거절한다.
- Parser가 JSON 외 텍스트를 거절한다.
- Parser가 허용되지 않은 enum 값을 거절한다.
- Fake LLM client로 judgment chain 테스트가 가능하다.
- LLM 출력도 post-guardrail 검사를 통과해야 최종 draft가 된다.
- 금지 작업이 LLM 출력에 들어가면 `blocked`로 변환된다.

---

## Verification Commands

```bash
uv run pytest backend/tests/test_llm_judgment_chain.py backend/tests/test_guardrails.py backend/tests/test_agent_workflow.py
python scripts/run_evals.py --dataset safety_guardrail_cases --strict
python scripts/run_evals.py --dataset workflow_e2e_cases --strict
```

---

## Human Review Checklist

- [ ] Prompt가 공식 근거와 사용자 요청을 구분하는가?
- [ ] LLM 자유문 출력이 허용되지 않는가?
- [ ] JSON schema가 리포트/승인/Evidence Log에 충분한가?
- [ ] post-LLM guardrail이 작동하는가?
- [ ] 실제 LLM API 없이 테스트가 가능한가?
