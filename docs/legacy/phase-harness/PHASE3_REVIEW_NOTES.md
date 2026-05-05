# 3단계 (워크플로우 상태 머신) 사전 검토

> 대상: `C:\WorkBridge\phases\mvp\phase3-state-machine.md`
> 작성 시점: Phase 1C·Phase 2 완료 직후, 진입 직전 검토 권장

---

## 현재 spec 평가

### 통과
- Goal에 핵심 4요소가 명시되어 있다. `request prep / evidence retrieval / risk flags / human approval`
- Forbidden 4종이 명확하다. 외부 발송 / EPS API / auto-approve / EPS 점수 자동 계산
- Stop Conditions에 `human approval bypass`가 명시되어 있다

### 개선 권장 5가지

#### 1. Goal이 너무 광범위하다
현재: "request preparation, evidence retrieval, risk flags, and human approval"

→ 이 네 가지가 한 모듈에 들어가면 `workflow_state.py`가 비대해진다.
책임을 더 명시적으로 분리해야 테스트와 review가 깔끔해진다.

#### 2. Allowed Writes를 분리할 필요가 있다
현재: `src/workflow_state.py` 한 파일.

권장:
- `src/workflow_state.py` - 상태 + 전이
- `src/risk_flags.py` - risk flag 산정 규칙
- `src/evidence_assembler.py` - retrieve 결과를 evidence 패키지로 조립

#### 3. Steps가 추상적이다
현재 Step 2: "Implement transitions for draft, evidence_ready, risk_review, human_approved, and blocked"

→ 좋은 출발점이다. 다만 case_type별 분기와 risk_flag 종류가 명시되지 않았다.
LLM 없이 deterministic하게 구현하려면 enum이 spec에 있어야 한다.

#### 4. Verification이 너무 가볍다
현재: pytest 통과만.

→ synthetic case `case_001/002/003`이 이미 `expected_workforce_agent_output`을 갖고 있으므로,
end-to-end fixture 검증을 verification에 포함해야 의미가 있다.

#### 5. Forbidden에 LLM을 명시하는 것을 권장한다
현재 Forbidden에 LLM 항목이 없다.

→ Phase 2가 deterministic이고 Phase 3도 deterministic이어야 risk_flag 결과가 일관된다.
`Do not call an LLM in workflow_state, risk_flags, or evidence_assembler`를 추가하는 것이 좋다.

LLM은 별도 phase(예: 사용자 query 슬롯 추출)로 분리하는 것이 안전하다.

---

## 제안 버전 2 사양

아래 내용을 그대로 `phase3-state-machine.md`로 갱신할 수 있다.

```markdown
# 3단계: 워크플로우 상태 머신 + Risk Flags + Evidence Assembly (v2)

## 목표
워크포스 에이전트를 위한 deterministic workflow state machine을 구현한다.
router output + case context + retrieved evidence가 주어지면 synthetic case의
`expected_workforce_agent_output` 스키마와 맞는 state-tracked `workforce_agent_output`을 만든다.

## 입력
- 01_workforce_agent_schema.md (case_type, output schema)
- docs/DATA_GUIDE.md
- src/workforce_router.py
- src/retrieve.py (after Phase 1C refactor)
- data/structured/companies.csv
- data/structured/candidates.csv
- data/synthetic_cases/case_001.json (verification fixture)
- data/synthetic_cases/case_002.json (verification fixture)
- data/synthetic_cases/case_003.json (verification fixture)

## 허용 쓰기
- src/workflow_state.py
- src/risk_flags.py
- src/evidence_assembler.py
- tests/test_workflow_state.py
- tests/test_risk_flags.py
- tests/test_evidence_assembler.py

## 금지
- Do not call an LLM in workflow_state, risk_flags, or evidence_assembler.
- Do not send external messages.
- Do not auto-approve requests.
- Do not calculate EPS scores from real data.
- Do not invent risk_flag types beyond the Allowed Risk Flag Types list.

## 허용 상태
- draft
- evidence_ready
- risk_review
- human_approved
- blocked

## 허용 Risk Flag 유형
- score_below_threshold
- quarter_timing_unknown
- missing_documents
- contract_period_misalignment
- naekuk_recruitment_evidence_missing
- workplace_change_history_unverified

## 단계

### 1. State Machine
- case_type별로 상태와 전이를 정의한다.
- 기본 흐름: draft -> evidence_ready -> risk_review -> human_approved.
- level=high인 risk_flag가 있으면 다른 규칙이 통과해도 state를 risk_review로 보낸다.

### 2. Risk Flags
- 각 case_type마다 input_state 규칙으로 risk_flag 목록을 계산한다.
- 참조 필드: eps_employer_score, last_application_quarter, 보유 서류, 계약 날짜, workplace_change history.

### 3. Evidence Assembler
- `retrieve.py`에서 가져온 retrieved chunks를 바탕으로 다음을 조립한다:
  - request_form fields
  - evidence chunk_id가 붙은 site_condition_check items
  - admin / sending agency / candidate용 질문
  - risk_flags
  - evidence_sources 목록
- 출력에는 항상 `human_approval_required = true`를 설정한다.

### 4. End-to-end fixture tests
- synthetic case 3개(case_001, case_002, case_003)를 불러온다.
- router -> state machine -> risk_flags -> evidence_assembler 순으로 실행한다.
- 결과를 `expected_workforce_agent_output`과 구조적으로 비교한다.

## 검증

```bash
uv run pytest tests/test_workflow_state.py tests/test_risk_flags.py tests/test_evidence_assembler.py
```

Required:
- 3개 synthetic case 테스트가 모두 통과하고 다음 항목이 구조적으로 일치해야 한다:
  `case_type`, `phase`, `site_condition_check` items, `risk_flags`, `evidence_sources`, `human_approval_required`
- 명시적 approval token 없이는 어떤 state transition도 `human_approved`에 도달할 수 없어야 한다.

## 중단 조건
- transition이 human approval을 우회하면 중단한다.
- Allowed Risk Flag Types에 없는 risk_flag 값이 나오면 중단한다.
- 필요한 모듈(router, retrieve)이 없거나 변경되면 중단한다.
- synthetic case fixture를 맞출 수 없으면 중단한다. fixture를 억지로 고치지 않는다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```

### 버전 2가 가져오는 변화 요약

| 항목 | v1 | v2 |
|---|---|---|
| Allowed Writes | 1개 파일 | 3개 파일 (책임 분리) |
| Risk Flag 종류 | 추상 | 6종 enum 명시 |
| 검증 | pytest only | + synthetic case 3건 fixture 매칭 |
| LLM 사용 | 미명시 | Forbidden 명시 |
| Inputs | 4개 | + synthetic case 3건 |
| Stop Conditions | 3개 | + risk_flag enum 위반, fixture 매칭 실패 |
