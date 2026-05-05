# 스키마 계약

## 1. 목적

이 문서는 WorkBridge/Oegobanjang의 work item, fixture, eval case에서 공통으로 사용하는 JSON envelope를 정의한다.

목표는 각 Agent나 harness가 서로 다른 case 형식을 임의로 만들지 않도록 막는 것이다. 도메인별 payload는 달라질 수 있지만, 아래 top-level 필드는 Workforce, Visa Document, Contact, workflow, eval fixture 전체에서 안정적으로 유지한다.

---

## 2. 공통 Work Item Envelope 형식

```json
{
  "work_item_id": "case_003",
  "case_type": "workplace_change_intake",
  "current_state": "site_check",
  "next_state": "candidate_intake",
  "requires_human": true,
  "confidence": 0.85,
  "input_state": {},
  "expected_workforce_agent_output": {},
  "audit_log_ref": ["log_id_xxx"]
}
```

---

## 3. 필수 필드

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---:|---:|---|
| work_item_id | string | 예 | case, fixture, eval item의 안정적인 ID. 예: `case_003`. |
| case_type | string | 예 | 업무 case 유형. 해당 Agent가 허용한 값 중 하나여야 한다. |
| current_state | string | 예 | 이 work item 실행 전 현재 workflow state. 새 fixture에서는 `phase` 대신 이 필드를 사용한다. |
| next_state | string | 예 | 정상 처리 후 기대되는 다음 workflow state. |
| requires_human | boolean | 예 | 외부 실행 또는 최종 완료 전에 사람 승인/검토가 필요한지 여부. |
| confidence | number | 예 | Router 또는 classifier confidence. 값 범위는 `0.0`부터 `1.0`까지다. deterministic router는 문서화된 고정값을 사용한다. |
| input_state | object | 예 | Agent 또는 workflow node에 전달되는 입력 snapshot. raw PII를 포함하면 안 된다. |
| expected_workforce_agent_output | object | 조건부 | Workforce Agent의 기대 출력. Workforce fixture/eval에서는 필수다. |
| audit_log_ref | array[string] | 예 | 이 work item과 연결된 Evidence/Audit log ID 목록. 실행 전에는 빈 배열을 허용한다. |

---

## 4. 이름 규칙

- `work_item_id`가 표준 case/eval 식별자다. 외부 도구가 강제하지 않는 한 별도 top-level `id`를 만들지 않는다.
- `current_state`와 `next_state`가 표준 workflow 필드다. 새 fixture에서는 `phase`를 사용하지 않는다.
- `requires_human`이 표준 승인 필요 여부 필드다. 기존 `human_approval_required`는 하위 호환을 위해 읽을 수 있지만, 새 fixture에서 두 필드를 동시에 쓰지 않는다.
- `audit_log_ref`에는 log reference만 저장한다. raw snapshot, PII, 전체 evidence text를 넣지 않는다.

---

## 5. State 값

State 이름은 `docs/GRAPH_STATE.md` 및 mission별 workflow spec과 맞춘다. MVP fixture에서 사용할 수 있는 state 예시는 다음과 같다.

```txt
site_check
candidate_intake
contract_prep
site_check_and_intake
approval_pending
completed
blocked
```

새 state가 필요하면 fixture에 추가하기 전에 mission spec에 먼저 문서화한다.

---

## 6. 안전 및 PII 규칙

- `input_state`에는 외국인등록번호, 여권번호, 전체 전화번호, 전체 주소, 서류 파일 원문을 저장하지 않는다.
- 테스트에 PII 형태의 값이 필요하면 마스킹된 예시 또는 synthetic placeholder를 사용한다.
- routing, retrieval, audit에 필요한 metadata가 없으면 silent fallback을 사용하지 않는다. work item을 `blocked`로 표시하고 명시적인 reason을 남긴다.
- `confidence`는 법적 확실성 점수나 비자 가능성 점수가 아니다. routing/classification confidence만 의미한다.

---

## 7. Workforce Fixture 예시

```json
{
  "work_item_id": "case_003",
  "case_type": "workplace_change_intake",
  "current_state": "site_check",
  "next_state": "candidate_intake",
  "requires_human": true,
  "confidence": 0.85,
  "input_state": {
    "company_id": "company_demo_001",
    "worker_id": "worker_demo_003",
    "request_summary": "사업장 변경 접수 전 확인이 필요한 데모 케이스"
  },
  "expected_workforce_agent_output": {
    "status": "needs_human_review",
    "case_type": "workplace_change_intake",
    "risk_flags": ["workplace_change_requires_review"],
    "approval_required": true
  },
  "audit_log_ref": ["log_id_xxx"]
}
```

---

## 8. 하위 호환

기존 fixture에는 아래 필드가 남아 있을 수 있다.

- `case_id`
- `phase`
- `human_approval_required`

Reader는 아래처럼 표준 필드로 정규화할 수 있다.

| 기존 필드 | 표준 필드 |
|---|---|
| case_id | work_item_id |
| phase | current_state |
| human_approval_required | requires_human |

새 fixture와 eval case는 표준 필드를 사용해야 한다.
