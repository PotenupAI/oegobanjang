# WorkBridge Taxonomy (워크브릿지 택소노미)

이 문서는 WorkBridge/oegobanjang 프로젝트 전체에 흩어진 분류값을 한 곳에 모은 택소노미 색인이다. 기준 소스는 루트 지침, `docs/`, `missions/active/`, `backend/`, `data-pipeline/seed/`, `evals/datasets/`, `frontend/`이다.

이 파일은 운영자가 빠르게 분류값을 찾기 위한 통합 색인이다. 실제 계약의 최종 권위는 각 mission 문서, schema 문서, 코드 타입 정의, DB migration에 있다. 새 분류값을 추가하면 관련 계약 문서와 이 파일을 함께 갱신한다.

## 1. Runtime Intent Taxonomy (런타임 의도 분류)

| Intent (의도) | 의미 | 현재 처리 기준 |
| --- | --- | --- |
| `HIRING` (신규 채용) | 신규 채용, 사업장 상태 확인, 후보자 intake, 계약 준비 초안 | `workforce_agent` (인력 운영 에이전트) / hiring flow (채용 흐름) |
| `VISA_CHECK` (비자/체류 점검) | 체류자격, 만료일, 갱신 리스크 점검 | `visa_document_agent` (비자/서류 에이전트) 또는 문서/비자 flow (흐름) |
| `DOCUMENT_CHECK` (서류 점검) | 필요 서류, 누락 서류, 제출 상태 점검 | `visa_document_agent` (비자/서류 에이전트) |
| `CONTACT` (소통/연락) | 근로자/담당자/전문가에게 보낼 메시지 초안 또는 전달 요청 | 메시지 초안은 가능, 실제 발송은 승인 필요 |
| `BRIEFING` (상태 브리핑) | 현재 케이스 상태 요약, 담당자 briefing (브리핑) | final response (최종 응답) / briefing placeholder (브리핑 자리표시자) |
| `UNSUPPORTED_VALUE_JUDGMENT` (지원하지 않는 가치판단) | 성실도, 이탈 가능성, 국적 선호, 감시 등 가치판단 요청 | blocked (차단) |
| `UNSUPPORTED_LEGAL_JUDGMENT` (지원하지 않는 법률/노무 판단) | 비자 가능 확정, 법률/노무 자문, 책임 있는 판단 요청 | blocked (차단) |
| `UNSUPPORTED_AUTO_SUBMISSION` (지원하지 않는 자동 제출) | 정부 포털 제출, 외부 제출 자동화, 무승인 대외 발송 요청 | blocked (차단) |

복합 intent (의도)는 허용된다. 예를 들어 신규 채용 절차와 비자 점검을 함께 묻는 요청은 `HIRING` (신규 채용) + `VISA_CHECK` (비자/체류 점검)로 분류될 수 있다.

## 2. Case Type Taxonomy (케이스 유형 분류)

| Case Type (케이스 유형) | 상태 | 의미/출처 |
| --- | --- | --- |
| `new_hiring` (신규 고용) | current runtime (현재 런타임) | 신규 고용 흐름. Mission 001 runtime과 hiring agent의 주력 케이스 |
| `workplace_change_intake` (사업장 변경 접수) | current runtime (현재 런타임) | 사업장 변경 intake. 현재는 최소 지원 또는 제한적 초안 생성 |
| `stay_extension` (체류 연장) | seed/DB (시드/DB) | 체류 연장 또는 갱신 서류 요구 케이스 |
| `employment_change` (고용 변경) | seed/DB (시드/DB) | 고용 변경/사업장 변경 관련 서류 요구 케이스 |
| `rehire_loyalty` (재고용 충성도 과거 분류) | legacy/synthetic (레거시/합성 데이터) | 재고용 관련 과거 synthetic case 분류 |
| `same_worker_rehire` (동일 근로자 재고용) | legacy/synthetic (레거시/합성 데이터) | 동일 근로자 재고용 관련 과거 synthetic case 분류 |

정규화 권장: runtime (런타임)의 canonical case type (표준 케이스 유형)은 `new_hiring` (신규 고용), `workplace_change_intake` (사업장 변경 접수)로 두고, seed/DB (시드/DB)의 `stay_extension` (체류 연장), `employment_change` (고용 변경)는 document requirement domain case (서류 요구 도메인 케이스)로 분리한다.

## 3. Workflow State Taxonomy (워크플로 상태 분류)

| State (상태) | 의미 |
| --- | --- |
| `draft` (초안) | 케이스 초안 또는 초기 입력 상태 |
| `site_check` (사업장 확인) | 사업장 요건/상태 확인 |
| `candidate_intake` (후보자 정보 접수) | 후보자 또는 근로자 입력값 수집 |
| `site_check_and_intake` (사업장 확인 및 접수) | 사업장 변경 등에서 사업장 확인과 intake를 함께 수행 |
| `contract_prep` (계약 준비) | 계약/서류 패키지 초안 준비 |
| `risk_review` (리스크 검토) | 리스크 플래그가 있어 사람 검토가 필요한 상태 |
| `blocked` (차단됨) | guardrail 또는 지원 범위 밖 요청으로 차단 |
| `human_approved` (사람 승인 완료) | 담당자 승인 완료 |
| `handoff_package` (전달 패키지) | 전문가/담당자에게 전달 가능한 패키지 초안 |
| `approval_pending` (승인 대기) | seed/schema fixture에서 쓰이는 승인 대기 상태 |
| `completed` (완료) | seed/schema fixture에서 쓰이는 완료 상태 |

주요 전이:

| Flow (흐름) | Allowed Path (허용 경로) |
| --- | --- |
| `new_hiring` (신규 고용) | `draft` (초안) -> `site_check` (사업장 확인) -> `candidate_intake` (후보자 정보 접수) -> `contract_prep` (계약 준비) -> `human_approved` (사람 승인 완료) |
| `workplace_change_intake` (사업장 변경 접수) | `draft` (초안) -> `site_check_and_intake` (사업장 확인 및 접수) -> `contract_prep` (계약 준비) -> `human_approved` (사람 승인 완료) |
| common risk (공통 리스크) | `any_state` (임의 상태) -> `risk_review` (리스크 검토) |
| common block (공통 차단) | `any_state` (임의 상태) -> `blocked` (차단됨) |
| handoff (전달) | `human_approved` (사람 승인 완료) -> `handoff_package` (전달 패키지) |

## 4. Agent And Tool Taxonomy (에이전트와 도구 분류)

### Agents (에이전트)

| Agent (에이전트) | 역할 |
| --- | --- |
| `workforce_agent` (인력 운영 에이전트) | 신규 고용, 사업장 확인, 후보자 intake, 계약 준비 초안 |
| `visa_document_agent` (비자/서류 에이전트) | 체류/비자/서류 누락 점검 |
| `multilingual_contact_agent` (다국어 소통 에이전트) | 다국어 메시지 초안, 안전 안내, 응답 요약 |
| `communication_agent` (소통 에이전트) | Mission 001/eval에서 쓰이는 contact placeholder 명칭 |
| `hiring_agent` (채용 에이전트 구현체) | runtime 구현 파일 기준의 workforce agent 본체 |

정규화 이슈: RAG seed는 `multilingual_contact_agent` (다국어 소통 에이전트)를 쓰고, Mission 001/eval/planner 쪽은 `communication_agent` (소통 에이전트)를 쓴다. contact (소통) 계열 agent (에이전트) 이름은 하나로 정리할 필요가 있다.

### Tool Grades (도구 등급)

| Grade (등급) | 의미 |
| --- | --- |
| `SAFE_READ` (안전 조회) | DB/RAG에서 읽기만 수행 |
| `SAFE_CALCULATE` (안전 계산) | 날짜, 누락 서류, readiness 등 deterministic 계산 |
| `SAFE_DRAFT` (안전 초안 생성) | 메시지/패키지/요청 초안 생성 |
| `APPROVAL_REQUIRED` (승인 필요) | 외부 발송, 완료 처리, export 등 승인 후 실행 가능 |
| `FORBIDDEN` (금지) | 프로젝트 원칙상 구현/실행 금지 |

### Tool Response Status (도구 응답 상태)

| Status (상태) | 의미 |
| --- | --- |
| `SUCCESS` (성공) | 실행 성공 |
| `FAILED` (실패) | 실행 실패 |
| `NEEDS_APPROVAL` (승인 필요) | 승인 없이는 실행 불가 |
| `FORBIDDEN` (금지) | 금지 작업으로 차단 |

### Safe Read Tools (안전 조회 도구)

- `get_company_profile` (사업장 프로필 조회)
- `get_worker_profile` (근로자 프로필 조회)
- `get_candidate_profile` (후보자 프로필 조회)
- `get_document_status` (서류 상태 조회)
- `search_policy_documents` (정책/절차 문서 검색)
- `search_message_templates` (메시지 템플릿 검색)
- `search_safety_guides` (안전 안내 검색)

### Safe Calculate Tools (안전 계산 도구)

- `calculate_visa_d_day` (비자 만료 D-day 계산)
- `calculate_contract_gap` (계약 공백 계산)
- `calculate_missing_documents` (누락 서류 계산)
- `calculate_candidate_readiness` (후보자 준비 상태 계산)
- `classify_case_type` (케이스 유형 분류)
- `quota_tool` (쿼터 준비 상태 도구) readiness calculation (준비 상태 계산)

### Safe Draft Tools (안전 초안 생성 도구)

- `generate_hiring_request_draft` (채용 요청 초안 생성)
- `generate_multilingual_message_draft` (다국어 메시지 초안 생성)
- `generate_expert_handoff_package_draft` (전문가 전달 패키지 초안 생성)
- `generate_safety_notice_draft` (안전 안내문 초안 생성)

### Approval Required Tools (승인 필요 도구)

- `send_worker_message` (근로자 메시지 발송)
- `send_manager_notification` (관리자 알림 발송)
- `send_expert_package` (전문가 패키지 전달)
- `update_case_status_completed` (케이스 완료 상태 처리)
- `export_handoff_package` (전달 패키지 export)

### Forbidden Tools / Behaviors (금지 도구/행동)

- `submit_government_portal` (정부 포털 제출)
- `confirm_visa_eligibility` (비자 가능 여부 확정)
- `provide_legal_advice` (법률 자문 제공)
- `predict_worker_absconding` (근로자 이탈 가능성 예측)
- `monitor_worker_sns` (근로자 SNS 감시)
- `score_worker_reliability` (근로자 신뢰도 점수화)
- `recommend_worker_by_nationality` (국적 기준 근로자 추천)

## 5. Approval And Status Taxonomy (승인과 상태 분류)

### Runtime Approval Status (런타임 승인 상태)

| Status (상태) | 의미 |
| --- | --- |
| `NOT_REQUIRED` (승인 불필요) | 승인 없이 초안/조회/계산 가능 |
| `PENDING` (승인 대기) | 승인 필요, 아직 실행 불가 |
| `APPROVED` (승인 완료) | 승인 완료 |
| `REJECTED` (승인 거절) | 승인 거절 |

### DB Approval Status (DB 승인 상태)

| Status (상태) | 의미 |
| --- | --- |
| `PENDING` (승인 대기) | 승인 대기 |
| `APPROVED` (승인 완료) | 승인 완료 |
| `REJECTED` (승인 거절) | 승인 거절 |
| `CANCELLED` (취소됨) | 승인 요청 취소 |

### Approval Required Actions (승인 필요 작업)

- 외국인 근로자 메시지 발송
- 행정사/노무사 패키지 전달
- 케이스 상태 완료 처리
- 대외 제출용 문서 export
- 카톡/문자 푸시 발송

정규화 이슈: runtime (런타임)에서는 `approval.required` (승인 필요 여부), `approval_required` (승인 필요 여부), `requires_human` (사람 검토 필요 여부)이 함께 등장한다. 외부 API는 `approval_required` (승인 필요 여부), agent output (에이전트 출력)은 `requires_human` (사람 검토 필요 여부), 내부 approval object (승인 객체)는 `required` (필요 여부)처럼 레이어별로 명확히 구분하는 것이 좋다.

## 6. Evidence Log Taxonomy (증거 로그 분류)

### Canonical Event Types (표준 이벤트 유형)

| Event Type (이벤트 유형) | 의미 |
| --- | --- |
| `intent_classified` (의도 분류됨) | 사용자 요청의 intent 분류 |
| `plan_created` (계획 생성됨) | agent/tool 실행 계획 생성 |
| `tool_executed` (도구 실행됨) | 도구 또는 agent 호출 결과 기록 |
| `rag_retrieved` (RAG 근거 검색됨) | RAG 근거 검색 결과 기록 |
| `risk_flagged` (리스크 표시됨) | 리스크 또는 주의사항 감지 |
| `approval_requested` (승인 요청됨) | 승인 필요 작업 감지 및 대기 |
| `approval_completed` (승인 처리 완료됨) | 승인/거절 처리 완료 |
| `final_response_generated` (최종 응답 생성됨) | 사용자에게 반환할 최종 응답 생성 |
| `block` (차단) | guardrail 또는 scope 밖 요청 차단 |

### Compatibility Action Types (호환용 실행 동작 유형)

| Action Type (동작 유형) | 의미 |
| --- | --- |
| `retrieve` (검색) | 근거 검색 |
| `judge` (판단) | 판단/분류 |
| `approve` (승인) | 승인 처리 |
| `handoff` (전달) | 전달 패키지 생성 또는 handoff |
| `route` (라우팅) | intent routing |
| `plan` (계획) | plan 생성 |
| `execute_tool` (도구 실행) | agent/tool 실행 |
| `block` (차단) | 차단 |

정규화 권장: `event_type` (이벤트 유형)은 문서 계약 기준의 canonical event (표준 이벤트)로 두고, `action_type` (동작 유형)은 실행 동작 호환 필드로 유지한다.

## 7. Safety And Guardrail Taxonomy (안전장치와 가드레일 분류)

### Sensitive Information Categories (민감정보 범주)

- 이름
- 생년월일
- 국적
- 여권번호
- 외국인등록번호
- 체류자격
- 체류만료일
- 계약 정보
- 숙소 정보
- 연락처
- 제출 서류

### Forbidden Behavior IDs (금지 행동 ID)

| Behavior ID (행동 ID) | 의미 |
| --- | --- |
| `candidate_recommendation` (후보자 추천) | 특정 후보자를 AI가 추천/선정 |
| `nationality_preference` (국적 선호) | 국적 선호 또는 차별적 추천 |
| `auto_visa_decision` (비자 자동 판정) | 비자 가능 여부 확정 |
| `legal_advice` (법률 자문) | 법률 자문 |
| `labor_advice` (노무 자문) | 노무 자문 |
| `government_portal_submission` (정부 포털 제출) | 정부 포털 자동 제출 |
| `external_submission_without_approval` (무승인 외부 제출) | 승인 없는 외부 제출/전달 |
| `worker_surveillance` (근로자 감시) | 근로자 SNS/단톡방/외부 커뮤니티 감시 |
| `absconding_prediction` (이탈 예측) | 이탈 가능성 예측 |
| `worker_reliability_scoring` (근로자 신뢰도 점수화) | 성실도/신뢰도 점수화 |
| `public_workplace_reputation_scoring` (사업장 공개 평판 점수화) | 사업장 공개 평판 점수 |
| `broker_detection` (브로커 색출) | 브로커 색출 |

### Safety Outcome (안전 처리 결과)

| Outcome (결과) | 의미 |
| --- | --- |
| `blocked` (차단됨) | 금지 요청으로 차단 |
| `approval_pending` (승인 대기) | 실행은 가능성이 있으나 사람 승인 전에는 멈춤 |
| `draft_only` (초안만 허용) | 초안 생성까지만 허용 |
| `safe_read_or_calculate` (안전 조회 또는 계산) | 조회/계산만 수행 |

## 8. Risk And Readiness Taxonomy (리스크와 준비 상태 분류)

### Risk Level (리스크 수준)

| Value (값) | 사용 위치 |
| --- | --- |
| `low` (낮음) / `medium` (중간) / `high` (높음) | RAG metadata, seed chunks |
| `LOW` (낮음) / `MEDIUM` (중간) / `HIGH` (높음) | DB/Evidence schema examples |

정규화 이슈: RAG는 lowercase, DB/Evidence는 uppercase를 쓴다. 저장 계층별 요구가 없다면 API/문서에서는 lowercase를 권장하고, DB enum은 migration 기준을 따른다.

### Evidence Grade (근거 등급)

| Grade (등급) | 의미 | 답변 근거 사용 |
| --- | --- | --- |
| `A` (공식 법령/정부 문서) | 법령/정부 공식 문서 | 가능 |
| `B` (공식 절차 안내) | 공공기관/공식 절차 안내 | 가능 |
| `C` (공공데이터/통계) | 공공데이터/통계 | 시장/상황 분석용 |
| `D` (상담사례/참고자료) | 센터 상담사례/참고자료 | 참고용 |
| `E` (내부 템플릿) | 내부 템플릿 | 승인 전 초안/메시지 템플릿용 |
| `F` (합성/평가 데이터) | synthetic/demo/eval 데이터 | 공식 근거로 사용 금지 |

Mission 002 기준으로 A/B/E만 answer evidence로 사용할 수 있고, F는 demo/eval 전용이다.

### Quota / Readiness Status (쿼터/준비 상태)

| Status (상태) | 의미 |
| --- | --- |
| `needs_more_information` (추가 정보 필요) | 필수 입력이 부족함 |
| `needs_human_review` (사람 검토 필요) | 계산 가능하지만 사람 검토가 필요함 |
| `ready_for_review` (검토 준비 완료) | 초안/검토 단계로 넘길 준비가 됨 |

### Runtime Risk Flags (런타임 리스크 플래그)

- `headcount_not_numeric` (고용 인원 값이 숫자가 아님)
- `quota_insufficient` (쿼터 부족)
- `workplace_change_history_unverified` (사업장 변경 이력 미확인)
- `unsupported_case_type` (지원하지 않는 케이스 유형)
- `missing_company_id` (사업장 ID 누락)
- `missing_headcount` (고용 인원 누락)
- `missing_evidence_source` (근거 출처 누락)

## 9. RAG And Source Metadata Taxonomy (RAG와 출처 메타데이터 분류)

### RAG Metadata Fields (RAG 메타데이터 필드)

- `source_id` (출처 ID)
- `title` (제목)
- `publisher` (발행 기관)
- `source_type` (출처 유형)
- `url` (원문 URL)
- `retrieved_at` (수집 일시)
- `effective_date` (시행일)
- `doc_type` (문서 유형)
- `mission_agent` (담당 미션 에이전트)
- `visa_type` (체류자격 유형)
- `country` (국가)
- `industry` (업종)
- `risk_level` (리스크 수준)
- `evidence_grade` (근거 등급)

### Source Type (출처 유형)

| Value (값) | 의미 |
| --- | --- |
| `official_law` (공식 법령) | 법령/고시/공식 법적 근거 |
| `official_procedure` (공식 절차) | 공식 절차 안내 |
| `official_form` (공식 서식) | 공식 서식 |
| `safety_guide` (안전 안내) | 안전/생활/사업장 안내 |
| `message_template` (메시지 템플릿) | 메시지 템플릿 |
| `synthetic_case` (합성 케이스) | 평가/데모용 synthetic case |
| `internal_checklist` (내부 체크리스트) | 내부 체크리스트 또는 seed-derived chunk |

### Document Type (문서 유형)

| Value (값) | 의미 |
| --- | --- |
| `law` (법령) | 법령 |
| `procedure` (절차) | 절차 |
| `form` (서식) | 서식 |
| `safety` (안전 안내) | 안전/생활 안내 |
| `template` (템플릿) | 템플릿 |
| `case` (케이스) | 케이스 |

### Legacy Chunk Type (레거시 청크 유형)

| Value (값) | 의미 |
| --- | --- |
| `law_clause` (법령 조항) | 법령 조항 단위 |
| `procedure_step` (절차 단계) | 절차 단계 |
| `industry_entry` (업종 항목) | 업종/허용 범위 항목 |
| `form_field` (서식 필드) | 서식 필드 |
| `template` (템플릿) | 템플릿 chunk |
| `scoring_criterion` (점수 기준) | 점수/기준 항목 |

정규화 이슈: 현재 Mission 002의 active contract (현재 계약)는 `doc_type` (문서 유형) 중심이고, `chunk_type` (청크 유형)은 legacy phase/RAG 설계에서 나온 분류다. 검색/평가에서 계속 필요하면 `chunk_type` (청크 유형)을 별도 metadata (메타데이터)로 복원할지 결정해야 한다.

### Search Filter Values (검색 필터 값)

- `visa_type` (체류자격 유형)
- `doc_type` (문서 유형)
- `mission_agent` (담당 미션 에이전트)
- `country` (국가)
- `industry` (업종)

### Downloaded Format (다운로드 형식)

- `html` (HTML 문서)
- `pdf` (PDF 문서)

## 10. Domain Data Taxonomy (도메인 데이터 분류)

### Visa Type (체류자격 유형)

- `D-10` (구직)
- `E-7` (특정활동)
- `E-9` (비전문취업)
- `F-2` (거주)
- `H-2` (방문취업)

현재 seed (시드)의 worker/visa/document requirement (근로자/비자/서류 요구 데이터)는 주로 `E-9` (비전문취업), `H-2` (방문취업)를 사용하고, lookup (조회표)에는 `D-10` (구직), `E-7` (특정활동), `F-2` (거주)도 있다.

### Nationality (국적)

- `Cambodia` (캄보디아)
- `Indonesia` (인도네시아)
- `Nepal` (네팔)
- `Philippines` (필리핀)
- `Thailand` (태국)
- `Uzbekistan` (우즈베키스탄)
- `Vietnam` (베트남)

주의: 국적은 언어/서류 안내와 입력 상태 확인을 위한 데이터일 뿐, 선호/추천/차별 기준으로 쓰면 안 된다.

### Preferred Language (선호 언어)

- `id` (인도네시아어)
- `km` (크메르어)
- `ko` (한국어)
- `ne` (네팔어)
- `th` (태국어)
- `tl` (타갈로그어)
- `uz` (우즈베크어)
- `vi` (베트남어)

### Industry (업종)

- `manufacturing` (제조업)
- `반도체`
- `자동차제조`
- `전자제품제조`
- `조선`
- `태양광제조`

### Region (지역)

- `거제`
- `부산`
- `아산`
- `이천`
- `인천`

### Required Document Type (필수 서류 유형)

- `alien_registration` (외국인등록증/외국인등록 관련 서류)
- `company_approval` (사업장 승인 서류)
- `criminal_record` (범죄경력증명)
- `education_cert` (학력 증명)
- `employment_contract` (고용계약서)
- `health_certificate` (건강진단서)
- `labor_contract` (근로계약서)
- `passport` (여권)
- `passport_copy` (여권 사본)
- `technical_cert` (기술 자격 증명)
- `work_permit` (취업 허가 서류)

## 11. DB Status Taxonomy (DB 상태 분류)

| Domain (도메인) | Status Values (상태값) |
| --- | --- |
| `user.role` (사용자 역할) | `ADMIN` (관리자), `MANAGER` (담당자) |
| `worker.status` (근로자 상태) | `ACTIVE` (활성), `INACTIVE` (비활성), `LEFT` (퇴사/이탈), `PENDING` (대기) |
| `candidate.status` (후보자 상태) | `PENDING` (대기), `READY` (준비됨), `NEEDS_INFO` (정보 필요), `REJECTED` (거절됨) |
| `hiring_request.status` (채용 요청 상태) | `DRAFT` (초안), `PENDING_REVIEW` (검토 대기), `APPROVED` (승인됨), `CANCELLED` (취소됨) |
| `visa.status` (비자 상태) | `ACTIVE` (유효), `EXPIRING` (만료 임박), `EXPIRED` (만료됨), `REVIEW_REQUIRED` (검토 필요) |
| `worker_document.status` (근로자 서류 상태) | `MISSING` (누락), `SUBMITTED` (제출됨), `REVIEWED` (검토됨), `EXPIRED` (만료됨) |
| `contact_message.status` (연락 메시지 상태) | `DRAFT` (초안), `PENDING_APPROVAL` (승인 대기), `APPROVED` (승인됨), `SENT` (발송됨), `CANCELLED` (취소됨) |
| `approval.status` (승인 상태) | `PENDING` (대기), `APPROVED` (승인됨), `REJECTED` (거절됨), `CANCELLED` (취소됨) |

## 12. Message Template Taxonomy (메시지 템플릿 분류)

### Purpose (목적)

- `contract_termination` (계약 종료 안내)
- `document_request` (서류 요청)
- `visa_extension_notice` (비자 연장 안내)

### Template Language (템플릿 언어)

- `id` (인도네시아어)
- `km` (크메르어)
- `ko` (한국어)
- `ne` (네팔어)
- `uz` (우즈베크어)
- `vi` (베트남어)

## 13. Frontend Taxonomy (프론트엔드 분류)

### Dashboard Item Status (대시보드 항목 상태)

- `normal` (정상)
- `attention` (주의 필요)
- `approval` (승인 필요)
- `risk` (리스크)

### Worker Document Status (근로자 서류 상태)

- `complete` (완료)
- `missing` (누락)
- `review` (검토)

### Approval Summary Status (승인 요약 상태)

- `PENDING` (대기)
- `APPROVED` (승인됨)
- `REJECTED` (거절됨)
- `CANCELLED` (취소됨)

### Mock Dashboard Action Types (목업 대시보드 동작 유형)

- `send_worker_message` (근로자 메시지 발송)
- `export_handoff_package` (전달 패키지 export)
- `intent_classified` (의도 분류됨)
- `approval_requested` (승인 요청됨)

## 14. Eval Dataset Taxonomy (평가 데이터셋 분류)

### Datasets (데이터셋)

| Dataset (데이터셋) | 검증 대상 |
| --- | --- |
| `intent_router_cases` (의도 라우터 케이스) | intent 분류, required agent, approval 필요 여부 |
| `safety_guardrail_cases` (안전 가드레일 케이스) | 금지 요청 차단, 무승인 발송 방지, approval required |
| `workflow_e2e_cases` (워크플로 E2E 케이스) | workflow intent/agent/approval/evidence event 흐름 |

### Eval Expected Intents (평가 기대 의도)

- `CONTACT` (소통/연락)
- `DOCUMENT_CHECK` (서류 점검)
- `HIRING` (신규 채용)
- `VISA_CHECK` (비자/체류 점검)
- `UNSUPPORTED_AUTO_SUBMISSION` (지원하지 않는 자동 제출)
- `UNSUPPORTED_LEGAL_JUDGMENT` (지원하지 않는 법률/노무 판단)
- `UNSUPPORTED_VALUE_JUDGMENT` (지원하지 않는 가치판단)

### Eval Evidence Events (평가 증거 이벤트)

- `intent_classified` (의도 분류됨)
- `plan_created` (계획 생성됨)
- `tool_executed` (도구 실행됨)
- `approval_requested` (승인 요청됨)
- `final_response_generated` (최종 응답 생성됨)

### Eval / Seed Source IDs (평가/시드 출처 ID)

- `message_template_passport_request_ko` (여권 요청 한국어 메시지 템플릿)
- `message_template_safety_notice_ko` (안전 안내 한국어 메시지 템플릿)
- `message_template_visa_extension_notice_ko` (비자 연장 안내 한국어 메시지 템플릿)
- `seed_eps_procedure_demo_001` (EPS 절차 데모 시드)
- `seed_visa_extension_demo_001` (비자 연장 데모 시드)
- `eps_employer_process_001` (EPS 사업주 절차 출처)
- `eps_allowed_industries_001` (EPS 허용 업종 출처)
- `eps_application_guide_001` (EPS 신청 안내 출처)
- `law_foreign_worker_act_001` (외국인근로자 법령 출처)
- `law_form_employment_change_001` (고용변경 법정 서식 출처)
- `eps_employer_scoring_001` (EPS 사업주 점수 기준 출처)

## 15. Naming Conflicts And Normalization Notes (명명 충돌과 정규화 메모)

| Area (영역) | 현재 혼재 | 권장 정리 |
| --- | --- | --- |
| case type (케이스 유형) | runtime (런타임) `workplace_change_intake` (사업장 변경 접수), seed/DB (시드/DB) `employment_change` (고용 변경), `stay_extension` (체류 연장) | runtime case (런타임 케이스)와 document requirement case (서류 요구 케이스)를 분리 |
| risk level (리스크 수준) | RAG `low/medium/high` (낮음/중간/높음), DB/Evidence `LOW/MEDIUM/HIGH` (낮음/중간/높음) | API/RAG는 lowercase (소문자), DB enum (DB 열거값)은 migration 기준 |
| contact agent (소통 에이전트) | `multilingual_contact_agent` (다국어 소통 에이전트), `communication_agent` (소통 에이전트) | 하나를 canonical (표준)로 정하고 alias map (별칭 맵) 유지 |
| approval flag (승인 플래그) | `approval_required` (승인 필요), `requires_human` (사람 검토 필요), `approval.required` (승인 필요 여부) | 레이어별 필드 책임을 문서화 |
| evidence naming (증거 로그 명명) | `event_type` (이벤트 유형), `action_type` (동작 유형) | `event_type`은 canonical event (표준 이벤트), `action_type`은 실행 동작 |
| legacy phase (레거시 단계) | `phase` (단계) | `current_state` (현재 상태) / mission acceptance (미션 수용조건) 기준으로 전환 |
| chunk metadata (청크 메타데이터) | `chunk_type` (청크 유형), `doc_type` (문서 유형) | active RAG contract (현재 RAG 계약)는 `doc_type`; chunk granularity (청크 세분성)가 필요하면 `chunk_type` 재도입 |
| downloaded format (다운로드 형식) | raw source (원천 소스) `html` (HTML 문서), `pdf` (PDF 문서) | source manifest (출처 매니페스트)의 실제 format (형식)을 그대로 기록 |

## 16. Update Rule (갱신 규칙)

새로운 분류값을 추가할 때는 아래를 함께 확인한다.

1. Mission acceptance에 필요한 값인지 확인한다.
2. Schema/type 정의와 DB enum에 반영한다.
3. Eval dataset에 최소 1개 케이스를 추가한다.
4. Evidence Log에 남아야 하는 값이면 PII masking 영향도 확인한다.
5. 이 `taxonomy.md`와 `FOLDER_STRUCTURE.md`를 함께 갱신한다.
