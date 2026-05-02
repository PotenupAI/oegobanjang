# TOOL CONTRACT

## 1. Tool 사용 원칙

Tool은 Agent가 실제 업무를 수행하기 위해 호출하는 기능 단위다.  
다만 Tool은 외부 발송, 정부 제출, 법적 확답을 자동 실행하지 않는다.

## 2. Tool 등급

### SAFE_READ

읽기 전용 도구. 자동 실행 가능하다.

- get_company_profile
- get_worker_profile
- get_candidate_profile
- get_document_status
- search_policy_documents
- search_message_templates
- search_safety_guides

### SAFE_CALCULATE

DB 상태나 입력값을 기반으로 계산만 수행한다.

- calculate_visa_d_day
- calculate_contract_gap
- calculate_missing_documents
- calculate_candidate_readiness
- classify_case_type

### SAFE_DRAFT

초안을 생성하지만 외부로 발송하거나 제출하지 않는다.

- generate_hiring_request_draft
- generate_multilingual_message_draft
- generate_expert_handoff_package_draft
- generate_safety_notice_draft

### APPROVAL_REQUIRED

관리자 승인 없이는 실행할 수 없다.

- send_worker_message
- send_manager_notification
- send_expert_package
- update_case_status_completed
- export_handoff_package

### FORBIDDEN

MVP에서 구현하면 안 된다.

- submit_government_portal
- confirm_visa_eligibility
- provide_legal_advice
- predict_worker_absconding
- monitor_worker_sns
- score_worker_reliability
- recommend_worker_by_nationality

## 3. 공통 Tool 응답 스키마

```json
{
  "tool_name": "string",
  "tool_grade": "SAFE_READ | SAFE_CALCULATE | SAFE_DRAFT | APPROVAL_REQUIRED | FORBIDDEN",
  "status": "SUCCESS | FAILED | NEEDS_APPROVAL | FORBIDDEN",
  "input_snapshot": {},
  "output": {},
  "citations": [],
  "risk_flags": [],
  "approval_required": false,
  "error": null
}