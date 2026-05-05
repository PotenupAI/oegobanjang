# 평가 지표

## 1. 목적

WorkBridge/Oegobanjang의 평가는 세 가지 지표군으로 분리한다.

1. CI와 harness에서 확인하는 자동화 지표.
2. 파일럿에서 신뢰도와 승인 가능성을 확인하는 휴먼 리뷰 지표.
3. 운영 시작 후 실제 업무 효과를 확인하는 비즈니스 지표.

이 세 지표군을 하나의 점수로 합치지 않는다. 각 지표군은 서로 다른 질문에 답한다.

---

## 2. 지표군

| 지표군 | WorkBridge 적용 예 | 측정 방법 | 주 담당 | Notion 매핑 |
|---|---|---|---|---|
| 자동화 | Hit@3 retrieval, chunk 누락률, 서류 누락 탐지 정확도, safety violation count, evidence log missing count | `scripts/run_evals.py`, 향후 `evals/runner.py`, backend tests, CI report | Engineering | Eval Axis: 자동화 / Status: CI |
| 휴먼 | 사장/담당자의 무수정 승인, 수정 승인, 거절 사유, citation usefulness, risk clarity | AI 출력별 파일럿 리뷰 form. 생성 초안과 최종 승인본 비교 | Product / Ops | Eval Axis: 휴먼 리뷰 / Status: Pilot |
| 비즈니스 | 행정사/노무사 보완 요청 감소, 사업장당 처리 시간 단축, 누락 서류 follow-up 감소, 비자 확인 지연 감소 | 파일럿 이후 운영 tracking. 주간 before/after 비교 | Ops / Business | Eval Axis: 비즈니스 효과 / Status: Operations |

---

## 3. 자동화 지표

| 지표 | 정의 | 목표 | 출처 |
|---|---|---:|---|
| RAG Hit@3 | 기대 source가 검색 결과 top 3 chunk 안에 포함되는 비율. | MVP seed eval은 >= 90%, 확장 eval set은 >= 85% | `evals/datasets/rag_retrieval_cases.jsonl` |
| RAG Hit@5 | 기대 source가 검색 결과 top 5 chunk 안에 포함되는 비율. | >= 85% | `docs/EVAL_HARNESS.md` |
| Chunk 누락률 | 필요한 source 문서는 있으나 valid chunk가 생성되지 않은 비율. | 필수 seed docs 기준 0% | ingest report |
| Metadata 누락률 | `source_id`, `publisher`, `doc_type`, `evidence_grade` 등 필수 metadata가 누락된 chunk 비율. | 0% | ingest validation |
| 서류 누락 탐지 정확도 | required/missing document 분류가 기대 fixture와 일치하는 정도. | recall >= 95% | `document_gap_cases.jsonl` |
| Safety Violation Count | 금지 action, 법적 확정, 차별적 추천, 자동 제출이 output에 포함된 건수. | 0 | `safety_guardrail_cases.jsonl` |
| Evidence Log Missing Count | workflow trace에서 필수 event가 빠진 건수. | 0 | workflow/evidence eval |

---

## 4. 휴먼 리뷰 지표

| 지표 | 정의 | 측정 방식 |
|---|---|---|
| 무수정 승인율 | 사장/담당자가 AI 출력을 그대로 승인한 비율. | `approved_without_edit / total_reviewed_outputs` |
| 수정 승인율 | 사장/담당자가 AI 출력을 수정한 뒤 승인한 비율. | `approved_with_edit / total_reviewed_outputs` |
| 거절률 | reviewer가 AI 출력을 거절한 비율. | `rejected / total_reviewed_outputs` |
| Citation 유용성 점수 | 근거 citation이 의사결정에 도움이 됐는지에 대한 reviewer 평가. | 1-5 파일럿 설문 |
| Risk 명확성 점수 | risk flag가 이해하기 쉬웠는지에 대한 reviewer 평가. | 1-5 파일럿 설문 |
| Human Override Reason | reviewer가 output을 수정하거나 거절한 이유. | 구조화 tag + 자유 텍스트 note |

휴먼 리뷰 지표는 CI gate가 아니다. 파일럿 사용 후 prompt, UX, workflow 개선 방향을 정하는 데 사용한다.

---

## 5. 비즈니스 지표

| 지표 | 정의 | 측정 기간 |
|---|---|---|
| 행정사/노무사 보완 요청 횟수 | case package당 행정사/노무사의 보완 요청 수. | 파일럿 전후 주간 비교 |
| 사업장당 케이스 처리 시간 | case 접수부터 handoff-ready package까지 담당자가 쓴 시간. | case당 median minutes |
| 누락 서류 follow-up 수 | 누락 또는 outdated document 때문에 추가 요청한 횟수. | 사업장별 월간 |
| 비자/체류기한 확인 지연 건수 | 비자/체류 deadline을 놓치거나 늦게 확인한 건수. | 월간 |
| Package 재작업률 | 승인된 handoff package가 이후 재작업된 비율. | `reworked_packages / approved_packages` |

비즈니스 지표는 실제 운영 사용이 시작된 뒤 추적한다. mission에서 명시하지 않는 한 로컬 개발을 막는 blocker로 쓰지 않는다.

---

## 6. Notion 페이지 매핑

Notion database에는 metric 하나당 row 하나를 만든다.

| Notion 속성 | 값 |
|---|---|
| 지표명 | 3-5장 중 하나의 지표명 |
| 평가 축 | `자동화`, `휴먼 리뷰`, `비즈니스 효과` |
| 지표 유형 | `quality`, `safety`, `trust`, `efficiency`, `operations` |
| 출처 | Dataset, survey, CI report, operations tracker |
| 목표 | 숫자 target 또는 정성 threshold |
| 현재 값 | 최신 측정값 |
| 담당자 | Engineering, Product, Ops, Business |
| 검토 주기 | PR, daily, weekly, monthly, pilot checkpoint |
| 의사결정 용도 | 이 지표가 어떤 의사결정에 쓰이는지 |

---

## 7. 의사결정 규칙

- 자동화 safety failure는 blocker다.
- 자동화 quality regression은 mission target 아래로 내려갈 때만 blocker다.
- 휴먼 리뷰 지표는 prompt, UX, workflow 개선에 사용한다.
- 비즈니스 지표는 우선순위와 가격/사업 의사결정에 사용한다.
- `confidence`는 비즈니스 성공 지표로 사용하지 않는다. routing/classification signal일 뿐이다.
