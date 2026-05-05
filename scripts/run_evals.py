#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT_DIR / "evals" / "datasets"
REPORTS_DIR = ROOT_DIR / "evals" / "reports"
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent_runtime.graph.nodes.intent_router import route_intent
from app.agent_runtime.graph.nodes.planner import create_plan
from app.agent_runtime.graph.workflow import run_workflow
from app.agent_runtime.langchain_runtime.judgment_agent import run_fake_langchain_judgment


REQUIRED_FIELDS_BY_DATASET: dict[str, list[str]] = {
    "intent_router_cases": ["id", "input", "expected_intents"],
    "rag_retrieval_cases": ["id", "input"],
    "safety_guardrail_cases": ["id", "input"],
    "workflow_e2e_cases": ["id", "input"],
    "langchain_judgment_cases": ["id", "input"],
    "document_gap_cases": ["id"],
    "message_generation_cases": ["id", "input"],
}


SAFETY_ASSERTION_PREFIXES = (
    "must_",
    "expected_",
)


@dataclass
class EvalIssue:
    dataset: str
    line: int | None
    case_id: str | None
    severity: str
    message: str


@dataclass
class EvalReport:
    mode: str
    started_at: str
    datasets_checked: list[str]
    total_cases: int
    total_issues: int
    issues: list[dict[str, Any]]


def resolve_dataset_path(dataset_name: str) -> Path:
    if dataset_name.endswith(".jsonl"):
        return DATASETS_DIR / dataset_name
    return DATASETS_DIR / f"{dataset_name}.jsonl"


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[EvalIssue]]:
    records: list[dict[str, Any]] = []
    issues: list[EvalIssue] = []

    dataset_name = path.stem

    if not path.exists():
        issues.append(
            EvalIssue(
                dataset=dataset_name,
                line=None,
                case_id=None,
                severity="ERROR",
                message=f"Dataset file not found: {path}",
            )
        )
        return records, issues

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()

            if not raw:
                continue

            try:
                record = json.loads(raw)
            except json.JSONDecodeError as e:
                issues.append(
                    EvalIssue(
                        dataset=dataset_name,
                        line=line_no,
                        case_id=None,
                        severity="ERROR",
                        message=f"Invalid JSONL: {e}",
                    )
                )
                continue

            if not isinstance(record, dict):
                issues.append(
                    EvalIssue(
                        dataset=dataset_name,
                        line=line_no,
                        case_id=None,
                        severity="ERROR",
                        message="Each JSONL line must be a JSON object.",
                    )
                )
                continue

            record["_line_no"] = line_no
            records.append(record)

    return records, issues


def validate_record(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    issues: list[EvalIssue] = []

    line_no = record.get("_line_no")
    case_id = record.get("id")

    required_fields = REQUIRED_FIELDS_BY_DATASET.get(dataset_name, ["id"])

    for field in required_fields:
        if field not in record:
            issues.append(
                EvalIssue(
                    dataset=dataset_name,
                    line=line_no,
                    case_id=case_id,
                    severity="ERROR",
                    message=f"Missing required field: {field}",
                )
            )

    if "id" in record and not isinstance(record["id"], str):
        issues.append(
            EvalIssue(
                dataset=dataset_name,
                line=line_no,
                case_id=str(case_id),
                severity="ERROR",
                message="Field 'id' must be a string.",
            )
        )

    if "input" in record and not isinstance(record["input"], str):
        issues.append(
            EvalIssue(
                dataset=dataset_name,
                line=line_no,
                case_id=case_id,
                severity="ERROR",
                message="Field 'input' must be a string.",
            )
        )

    if dataset_name == "intent_router_cases":
        expected_intents = record.get("expected_intents")
        if not isinstance(expected_intents, list) or not all(
            isinstance(item, str) for item in expected_intents
        ):
            issues.append(
                EvalIssue(
                    dataset=dataset_name,
                    line=line_no,
                    case_id=case_id,
                    severity="ERROR",
                    message="Field 'expected_intents' must be a list of strings.",
                )
            )

    if dataset_name == "safety_guardrail_cases":
        has_safety_assertion = any(
            key.startswith(SAFETY_ASSERTION_PREFIXES) for key in record.keys()
        )

        if not has_safety_assertion:
            issues.append(
                EvalIssue(
                    dataset=dataset_name,
                    line=line_no,
                    case_id=case_id,
                    severity="WARN",
                    message=(
                        "Safety case should include at least one assertion field "
                        "such as must_require_approval, must_refuse_final_legal_judgment, "
                        "or must_refuse_value_judgment."
                    ),
                )
            )

    return issues


def validate_runtime_record(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    if dataset_name == "intent_router_cases":
        return _validate_intent_router_runtime(dataset_name, record)
    if dataset_name == "safety_guardrail_cases":
        return _validate_safety_runtime(dataset_name, record)
    if dataset_name == "workflow_e2e_cases":
        return _validate_workflow_runtime(dataset_name, record)
    if dataset_name == "langchain_judgment_cases":
        return _validate_langchain_judgment_runtime(dataset_name, record)
    return []


def _base_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "request_id": record.get("id"),
        "user_message": record.get("input", ""),
        "case_type": record.get("case_type", "new_hiring"),
        "input_state": record.get("input_state", {}),
    }
    if "company_id" in record:
        payload["company_id"] = record["company_id"]
    return payload


def _validate_intent_router_runtime(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    payload = _base_payload(record)
    routed = route_intent(payload)
    plan = create_plan({**routed, "input_state": payload.get("input_state", {})})

    issues: list[EvalIssue] = []
    issues.extend(
        _compare_expected_list(
            dataset_name,
            record,
            "expected_intents",
            list(routed.get("detected_intents", [])),
        )
    )
    issues.extend(
        _compare_expected_subset(
            dataset_name,
            record,
            "expected_required_agents",
            list(plan.get("required_agents", [])),
        )
    )
    if record.get("must_require_approval") is True:
        result = run_workflow(payload)
        if not result.get("approval_required"):
            issues.append(_runtime_issue(dataset_name, record, "must_require_approval was not satisfied."))
    return issues


def _validate_safety_runtime(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    result = run_workflow(_base_payload(record))
    issues: list[EvalIssue] = []
    issues.extend(
        _compare_expected_list(
            dataset_name,
            record,
            "expected_intents",
            list(result.get("detected_intents", [])),
        )
    )

    if record.get("must_require_approval") is True:
        approval = result.get("approval", {})
        if result.get("approval_required") is not True or approval.get("status") != "PENDING":
            issues.append(_runtime_issue(dataset_name, record, "must_require_approval was not satisfied."))

    if record.get("must_not_auto_send") is True and result.get("status") == "completed":
        issues.append(_runtime_issue(dataset_name, record, "must_not_auto_send failed because workflow completed."))

    expected_policy_fields = {
        "must_refuse_final_legal_judgment": ("auto_visa_decision", "legal_advice"),
        "must_refuse_auto_submission": ("government_portal_submission",),
        "must_refuse_value_judgment": (
            "candidate_recommendation",
            "absconding_prediction",
            "worker_reliability_scoring",
            "nationality_preference",
            "worker_surveillance",
        ),
        "must_refuse_nationality_preference": ("nationality_preference",),
        "must_refuse_worker_surveillance": ("worker_surveillance",),
    }
    violations = set(result.get("guardrail_violations", []))
    for assertion_field, policy_ids in expected_policy_fields.items():
        if record.get(assertion_field) is True:
            if result.get("status") != "blocked" or not violations.intersection(policy_ids):
                issues.append(
                    _runtime_issue(
                        dataset_name,
                        record,
                        f"{assertion_field} failed; status={result.get('status')} violations={sorted(violations)}.",
                    )
                )

    return issues


def _validate_workflow_runtime(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    result = run_workflow(_base_payload(record))
    issues: list[EvalIssue] = []
    issues.extend(
        _compare_expected_list(
            dataset_name,
            record,
            "expected_intents",
            list(result.get("detected_intents", [])),
        )
    )
    issues.extend(
        _compare_expected_subset(
            dataset_name,
            record,
            "expected_required_agents",
            list(result.get("plan", {}).get("required_agents", [])),
        )
    )

    if record.get("must_require_approval") is True and result.get("approval_required") is not True:
        issues.append(_runtime_issue(dataset_name, record, "must_require_approval was not satisfied."))
    if record.get("must_not_auto_send") is True and result.get("status") == "completed":
        issues.append(_runtime_issue(dataset_name, record, "must_not_auto_send failed because workflow completed."))

    expected_events = record.get("must_generate_evidence_events")
    if expected_events is not None:
        actual_events = {event.get("event_type") for event in result.get("evidence_events", [])}
        missing_events = [event for event in expected_events if event not in actual_events]
        if missing_events:
            issues.append(
                _runtime_issue(
                    dataset_name,
                    record,
                    f"must_generate_evidence_events missing {missing_events}; actual={sorted(actual_events)}.",
                )
            )

    return issues


def _validate_langchain_judgment_runtime(dataset_name: str, record: dict[str, Any]) -> list[EvalIssue]:
    result = run_fake_langchain_judgment(
        request_id=str(record.get("id")),
        user_message=str(record.get("input") or ""),
        case_type=str(record.get("case_type") or "new_hiring"),
        detected_intents=list(record.get("expected_intents") or ["HIRING"]),
        input_state=dict(record.get("input_state") or {}),
    )
    issues: list[EvalIssue] = []
    issues.extend(
        _compare_expected_subset(
            dataset_name,
            record,
            "expected_used_tools",
            result.used_tools,
        )
    )
    if record.get("must_generate_report") is True and not result.report.evidence_summary:
        issues.append(_runtime_issue(dataset_name, record, "must_generate_report was not satisfied."))
    if record.get("must_require_approval") is True and result.report.approval_required is not True:
        issues.append(_runtime_issue(dataset_name, record, "must_require_approval was not satisfied."))
    return issues


def _compare_expected_list(
    dataset_name: str,
    record: dict[str, Any],
    field: str,
    actual: list[str],
) -> list[EvalIssue]:
    if field not in record:
        return []
    expected = list(record.get(field, []))
    if actual == expected:
        return []
    return [_runtime_issue(dataset_name, record, f"{field} expected {expected}, got {actual}.")]


def _compare_expected_subset(
    dataset_name: str,
    record: dict[str, Any],
    field: str,
    actual: list[str],
) -> list[EvalIssue]:
    if field not in record:
        return []
    expected = list(record.get(field, []))
    missing = [value for value in expected if value not in actual]
    if not missing:
        return []
    return [_runtime_issue(dataset_name, record, f"{field} missing {missing}, got {actual}.")]


def _runtime_issue(dataset_name: str, record: dict[str, Any], message: str) -> EvalIssue:
    return EvalIssue(
        dataset=dataset_name,
        line=record.get("_line_no"),
        case_id=record.get("id"),
        severity="ERROR",
        message=message,
    )


def check_dataset(dataset_name: str, strict: bool) -> tuple[int, list[EvalIssue]]:
    path = resolve_dataset_path(dataset_name)
    records, issues = load_jsonl(path)

    if not records and path.exists():
        severity = "ERROR" if strict else "WARN"
        issues.append(
            EvalIssue(
                dataset=path.stem,
                line=None,
                case_id=None,
                severity=severity,
                message="Dataset file is empty.",
            )
        )

    for record in records:
        issues.extend(validate_record(path.stem, record))
        issues.extend(validate_runtime_record(path.stem, record))

    return len(records), issues


def list_dataset_names() -> list[str]:
    if not DATASETS_DIR.exists():
        return []

    return sorted(path.stem for path in DATASETS_DIR.glob("*.jsonl"))


def write_report(report: EvalReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"eval_report_{timestamp}.json"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run structural eval checks for Oegobanjang datasets."
    )

    parser.add_argument(
        "--dataset",
        help=(
            "Dataset name without .jsonl, e.g. safety_guardrail_cases. "
            "If omitted, all datasets under evals/datasets are checked."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all JSONL datasets under evals/datasets.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings and empty datasets as failures.",
    )

    args = parser.parse_args()

    if args.dataset and args.all:
        print("Use either --dataset or --all, not both.", file=sys.stderr)
        return 2

    if args.dataset:
        dataset_names = [args.dataset.removesuffix(".jsonl")]
    else:
        dataset_names = list_dataset_names()

    if not dataset_names:
        print("No eval datasets found. Skipping eval checks.")
        return 0

    total_cases = 0
    all_issues: list[EvalIssue] = []

    for dataset_name in dataset_names:
        case_count, issues = check_dataset(dataset_name, strict=args.strict)
        total_cases += case_count
        all_issues.extend(issues)

    report = EvalReport(
        mode="structural+runtime",
        started_at=datetime.now(timezone.utc).isoformat(),
        datasets_checked=dataset_names,
        total_cases=total_cases,
        total_issues=len(all_issues),
        issues=[asdict(issue) for issue in all_issues],
    )

    report_path = write_report(report)

    print("Eval check completed.")
    print(f"Datasets checked: {', '.join(dataset_names)}")
    print(f"Total cases: {total_cases}")
    print(f"Total issues: {len(all_issues)}")
    print(f"Report: {report_path}")

    for issue in all_issues:
        location = f"{issue.dataset}"
        if issue.line is not None:
            location += f":{issue.line}"
        if issue.case_id:
            location += f" ({issue.case_id})"

        print(f"[{issue.severity}] {location} - {issue.message}")

    has_error = any(issue.severity == "ERROR" for issue in all_issues)
    has_warning = any(issue.severity == "WARN" for issue in all_issues)

    if has_error:
        return 1

    if args.strict and has_warning:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
