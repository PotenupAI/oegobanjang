# 워크브리지 남은 실행 계획

## 실행 순서
다음 순서로 진행한다:

1. `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ADR.md`, `docs/UI_GUIDE.md`를 읽는다.
2. `01_workforce_agent_schema.md`를 읽는다.
3. `02_week1_checklist_eval.md`를 읽는다.
4. `Phase 1: Data Schema + RAG Thin Slice`를 실행한다.
5. `Phase 2: Router`를 실행한다.
6. `Phase 3: Workflow State Machine`을 실행한다.
7. `Phase 4: Demo UI`를 실행한다.

## 1단계: 데이터 계약 + RAG Thin Slice
이 Phase는 `01_workforce_agent_schema.md`와 `02_week1_checklist_eval.md`를 하나의 실행 단위로 묶는다.

### 0. 범위 읽기와 고정
- 에이전트가 공식 절차, 조건, 허용 업종, 점수, 쿼터 정보만 정리한다는 점을 확인한다.
- 범위 밖 동작을 확인한다: candidate ranking, nationality preference, legal interpretation, 미승인 외부 발송, 자동 EPS 점수 계산.
- Phase 목표를 확인한다: 공식 raw source snapshot 6개, metadata가 완전한 chunks, retrieval eval 12문항, `Hit@3 >= 80%`.

### 1. 데이터 계약 고정
- `docs/DATA_GUIDE.md`를 만든다.
- company, candidate, synthetic case, chunk, source metadata, retrieval eval 스키마를 문서화한다.
- `case_type`, optional `phase`, `scoring_criterion`, source metadata, evidence grades, synthetic data 경계를 포함한다.
- 구현 전에 CSV와 JSON 계약 테스트를 추가한다.

### 2. 공식 raw source 수집
- `data/raw/` 아래에 공식 raw source snapshot 6개를 모은다.
- 필요한 파일은 `eps_employer_process_001.html`, `eps_allowed_industries_001.html`, `eps_application_guide_001.html`, `law_foreign_worker_act_001.html`, `law_form_employment_change_001.pdf`, `eps_employer_scoring_001.html`이다.
- manifest에 있는 공식 raw source가 하나라도 없으면 올바른 결과는 `status: blocked`이며, 가짜 chunk를 만들면 안 된다.

### 3. 텍스트 추출과 chunk 분할
- `src/ingest.py`를 구현한다.
- HTML/PDF 텍스트를 추출하고 table/heading 깨짐을 확인한다.
- 스키마 규칙에 따라 chunk를 나눈다: 법령 조문, 절차 단계, 업종 항목, 서식 필드 그룹, 점수제 항목.
- `data/processed/regulation_chunks.jsonl`를 쓴다.
- `data/processed/sources.json`를 쓴다.

### 4. retriever와 index 구축
- `src/retrieve.py`를 구현한다.
- `search(query, k=5, filters={})`를 만든다.
- `visa_type=E-9`와 `case_type=new_hiring`에 대한 metadata filter를 지원한다.
- index는 `data/index/` 아래에 저장한다.
- synthetic case는 공식 evidence index에 넣지 않는다.

### 5. retrieval eval 실행
- 12개의 retrieval eval row를 `eval/retrieval_eval.jsonl`에 쓴다.
- `src/evaluate.py`를 구현한다.
- top-3 source hit을 측정하고 실패 사례를 기록한다.
- `eval/results/phase1_retrieval_report.md`를 저장한다.
- `Hit@3 >= 80%`일 때만 완료로 본다. 아니면 실패 원인을 적어 blocked로 표시한다.

## 이후 Phase
`Phase 2: Router`는 deterministic하게 유지하고 LLM 호출을 피해야 한다.

`Phase 3: Workflow State Machine`은 외부 동작 전에 risk flag와 human approval을 강제해야 한다.

`Phase 4: Demo UI`는 candidate ranking이나 legal interpretation처럼 보이지 않게 evidence ID, risk flag, approval state를 보여줘야 한다.

## 현재 경계
WorkBridge에는 harness, docs, mock data, synthetic cases, 공식 raw source snapshot, Phase wrapper가 준비돼 있다. 다음 구현 실행은 Phase 1부터 시작해야 하며, manifest에 있는 공식 raw source가 `data/raw/` 아래에 없으면 즉시 중단해야 한다.
