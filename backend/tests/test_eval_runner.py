import json
import importlib.util
import sys
from pathlib import Path


RUN_EVALS_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_evals.py"
SPEC = importlib.util.spec_from_file_location("run_evals", RUN_EVALS_PATH)
assert SPEC is not None
assert SPEC.loader is not None
run_evals = importlib.util.module_from_spec(SPEC)
sys.modules["run_evals"] = run_evals
SPEC.loader.exec_module(run_evals)


def test_intent_router_eval_reports_runtime_mismatch(tmp_path, monkeypatch) -> None:
    dataset = tmp_path / "intent_router_cases.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "intent-mismatch",
                "input": "Nguyen 체류만료 언제야?",
                "expected_intents": ["HIRING"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(run_evals, "DATASETS_DIR", tmp_path)

    _, issues = run_evals.check_dataset("intent_router_cases", strict=True)

    assert any(issue.severity == "ERROR" and "expected_intents" in issue.message for issue in issues)


def test_workflow_eval_checks_required_evidence_event_types(tmp_path, monkeypatch) -> None:
    dataset = tmp_path / "workflow_e2e_cases.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "workflow-missing-event",
                "input": "베트남 E-9 근로자 3명 추가 채용 준비해줘.",
                "expected_intents": ["HIRING"],
                "must_generate_evidence_events": ["not_a_real_event"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(run_evals, "DATASETS_DIR", tmp_path)

    _, issues = run_evals.check_dataset("workflow_e2e_cases", strict=True)

    assert any(
        issue.severity == "ERROR" and "must_generate_evidence_events" in issue.message
        for issue in issues
    )
