# 1단계: 데이터 계약 + RAG Thin Slice

## 목표
`01_workforce_agent_schema.md`와 `02_week1_checklist_eval.md`를 하나의 실행 가능한 Phase로 묶는다. 이 Phase는 데이터 계약을 고정하고, 공식 raw source snapshot 6개를 수집하고, 첫 retrieval slice를 만들고, 12문항 eval을 측정한다.

## 입력
- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/ADR.md`
- `01_workforce_agent_schema.md`
- `02_week1_checklist_eval.md`
- `data/structured/companies.csv`
- `data/structured/candidates.csv`
- `data/synthetic_cases/case_001.json`
- `data/synthetic_cases/case_002.json`
- `data/synthetic_cases/case_003.json`
- `data/raw/source_manifest.json`
- `data/raw/eps_employer_process_001.html`
- `data/raw/eps_allowed_industries_001.html`
- `data/raw/eps_application_guide_001.html`
- `data/raw/law_foreign_worker_act_001.html`
- `data/raw/law_form_employment_change_001.pdf`
- `data/raw/eps_employer_scoring_001.html`

## 허용 쓰기
- `docs/DATA_GUIDE.md`
- `data/raw/`
- `data/processed/regulation_chunks.jsonl`
- `data/processed/sources.json`
- `data/index/`
- `eval/retrieval_eval.jsonl`
- `eval/results/phase1_retrieval_report.md`
- `src/ingest.py`
- `src/retrieve.py`
- `src/evaluate.py`
- `tests/test_data_contracts.py`
- `tests/test_retrieval_eval_contract.py`

## 금지
- 이 Phase에서 `01_workforce_agent_schema.md`나 `02_week1_checklist_eval.md`를 수정하지 않는다.
- 공식 EPS/legal source 내용을 지어내지 않는다.
- synthetic case, mock company, mock candidate를 legal evidence로 사용하지 않는다.
- routing, ranking, legal interpretation을 위해 LLM 호출을 추가하지 않는다.
- candidate를 rank하거나 nationality preference를 표현하지 않는다.
- `data/raw/source_manifest.json`에 적힌 공식 raw source가 하나라도 없으면 생성한 chunks를 진행하지 않는다.
- 이 Phase에서 이후 Phase 파일을 변경하지 않는다.

## 실행 순서

### 0. 범위 읽기와 고정
1. `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ADR.md`를 읽는다.
2. `01_workforce_agent_schema.md`를 agent 책임, 입력, 출력, `case_type`, chunk schema, source metadata, evidence grade, 범위 밖 동작의 단일 기준으로 읽는다.
3. `02_week1_checklist_eval.md`를 Week 1 RAG thin slice 실행 체크리스트로 읽는다.
4. Phase 목표를 확인한다: 공식 raw source snapshot 6개, `Hit@3 >= 80%`, 그리고 지어낸 legal evidence 없음.

### 1. 데이터 계약 고정
1. `docs/DATA_GUIDE.md`를 만든다.
2. `companies.csv` 필드를 문서화한다. 항목에는 employer score, cumulative intake count, departure rate, last application quarter가 포함된다.
3. `candidates.csv` 필드를 문서화한다. passport/photo/health check status, intake route, matching status가 포함된다.
4. 허용되는 `case_type` 4개를 문서화한다: `new_hiring`, `rehire_loyalty`, `workplace_change_intake`, `same_worker_rehire`.
5. 선택적 `phase` 값 `site_check`, `candidate_intake`, `contract_prep`를 문서화한다.
6. chunk JSONL 필드 `chunk_id`, `source_id`, `chunk_text`, `chunk_type`, `section_title`, `order_in_doc`, `char_count`를 문서화한다.
7. 허용 chunk type `law_clause`, `procedure_step`, `industry_entry`, `form_field`, `template`, `scoring_criterion`을 문서화한다.
8. source metadata 필드, evidence grade 규칙, 그리고 source metadata가 official evidence와 synthetic/demo data를 분리해야 한다는 규칙을 문서화한다.
9. mock CSV 파일, synthetic case, source metadata, chunk schema, retrieval eval row에 대한 contract test를 추가한다.

### 2. 공식 source 수집
1. `data/raw/source_manifest.json`를 확인한다.
2. 필요한 공식 raw source snapshot 6개를 확인한다.
3. manifest에 있는 공식 raw source가 하나라도 없으면 Phase를 blocked로 표시한다.
4. 없는 source에 대해 placeholder chunk를 만들지 않는다.

### 3. 텍스트 추출과 chunking
1. `src/ingest.py`를 구현한다.
2. 환경에 이미 있는 프로젝트 의존성을 사용해 각 공식 HTML/PDF raw source snapshot을 텍스트로 변환한다.
3. chunk를 만들기 전에 table과 heading 깨짐을 확인한다.
4. 법령은 조문 단위로 `law_clause`로 chunk한다.
5. EPS 사업주 고용절차는 step 단위로 `procedure_step`로 chunk한다.
6. E-9 허용업종은 industry item 단위로 `industry_entry`로 chunk한다.
7. 고용허가 신청 안내는 procedure step 단위로 `procedure_step`로 chunk한다.
8. 별지 서식은 field group 단위로 `form_field`로 chunk한다.
9. 사업장 점수제 안내는 scoring item 단위로 `scoring_criterion`으로 chunk한다.
10. chunk는 `data/processed/regulation_chunks.jsonl`에 쓴다.
11. source metadata는 `data/processed/sources.json`에 쓴다.

### 4. Retriever와 index
1. `src/retrieve.py`를 구현한다.
2. `data/processed/regulation_chunks.jsonl`와 `data/processed/sources.json`를 읽는다.
3. `search(query, k=5, filters={})`를 가진 첫 retriever를 만든다.
4. `visa_type=E-9`와 `case_type=new_hiring`에 대한 metadata filter를 지원한다.
5. index는 `data/index/` 아래에 저장한다.
6. synthetic case는 공식 evidence index에서 제외한다.

### 5. Retrieval eval과 보고서
1. `02_week1_checklist_eval.md`의 12개 retrieval eval row를 `eval/retrieval_eval.jsonl`에 쓴다.
2. `src/evaluate.py`를 구현한다.
3. 각 eval question마다 검색을 수행하고, 기대 source ID가 top 3 안에 있는지 확인한다.
4. `Hit@3`를 출력하고 기록한다.
5. 실행 요약과 실패 분석을 `eval/results/phase1_retrieval_report.md`에 저장한다.
6. `Hit@3 >= 80%`이면 Phase를 completed로 표시한다.
7. `Hit@3`가 목표보다 낮으면 실패 사례와 가능한 원인을 적어 blocked로 표시한다.

## 검증
다음을 실행한다:

```bash
uv run pytest tests/test_data_contracts.py tests/test_retrieval_eval_contract.py
uv run python src/evaluate.py
```

필수 결과:

```text
Hit@3 >= 80%
```

선택적 grep 확인:

```bash
rg -n "eps_employer_process_001|eps_allowed_industries_001|eps_application_guide_001|law_foreign_worker_act_001|law_form_employment_change_001|eps_employer_scoring_001" data/processed eval docs/DATA_GUIDE.md
```

## 중단 조건
- manifest에 있는 공식 raw source가 하나라도 없으면 Phase를 blocked로 표시한다.
- 필요한 CSV 또는 synthetic case 파일이 없다.
- 기존 mock data가 v2 schema와 맞지 않는다.
- `chunk_id`, `source_id`, `chunk_text`, `chunk_type`, `section_title`, `order_in_doc`, `char_count`가 유효하게 생성되지 않는다.
- `source_id`, `publisher`, `source_type`, `retrieved_at`, `doc_type`, `mission_agent`, `visa_type`, `case_type`, `risk_level`, `evidence_grade`가 유효하게 생성되지 않는다.
- eval row를 `question`, expected source ID, expected chunk를 가진 JSONL로 표현할 수 없다.
- `Hit@3`를 측정할 수 없거나 80%보다 낮다.
- missing metadata에 대한 silent fallback은 금지한다. 명시적 이유와 함께 blocked로 표시한다.

## 최종 출력 요구사항
응답의 마지막은 다음 중 하나여야 한다:

```text
status: completed
status: blocked
status: error
```
