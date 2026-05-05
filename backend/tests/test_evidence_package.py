from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agent_runtime.rag.chunking import build_chunks, write_chunks_jsonl
from app.agent_runtime.rag.evidence_package import (
    ANSWER_EVIDENCE_GRADES,
    build_evidence_package,
)


def _document(
    *,
    source_id: str,
    title: str,
    evidence_grade: str,
    source_type: str = "official_procedure",
    doc_type: str = "procedure",
    content: str = "E-9 고용허가 신청 절차는 담당자 확인 후 진행한다.",
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "title": title,
        "publisher": "MVP seed placeholder",
        "source_type": source_type,
        "url": "https://example.test/source",
        "retrieved_at": "2026-05-03",
        "effective_date": None,
        "doc_type": doc_type,
        "mission_agent": ["workforce_agent"],
        "visa_type": ["E-9"],
        "country": ["ALL"],
        "industry": ["manufacturing"],
        "risk_level": "medium",
        "evidence_grade": evidence_grade,
        "content": content,
    }


def _write_chunk_file(tmp_path: Path, documents: list[dict[str, object]]) -> Path:
    chunk_path = tmp_path / "chunks.jsonl"
    write_chunks_jsonl(build_chunks(documents), chunk_path)
    return chunk_path


def test_build_evidence_package_contains_llm_input_contract(tmp_path: Path) -> None:
    chunk_path = _write_chunk_file(
        tmp_path,
        [
            _document(
                source_id="official_eps_procedure_001",
                title="E-9 고용허가 절차",
                evidence_grade="B",
            )
        ],
    )

    package = build_evidence_package(
        request_id="req_001",
        query="E-9 고용허가 신청 절차",
        case_type="new_hiring",
        chunk_path=chunk_path,
    )

    assert package["status"] == "ready"
    assert package["request_id"] == "req_001"
    assert package["query"] == "E-9 고용허가 신청 절차"
    assert package["case_type"] == "new_hiring"
    assert package["missing_evidence"] == []
    assert package["evidence_policy"] == {
        "answer_evidence_grades": ["A", "B", "E"],
        "excluded_grades": ["C", "D", "F"],
        "synthetic_official_claims_allowed": False,
    }

    assert package["retrieved_chunks"]
    first_chunk = package["retrieved_chunks"][0]
    assert first_chunk["source_id"] == "official_eps_procedure_001"
    assert first_chunk["evidence_grade"] == "B"
    assert first_chunk["doc_type"] == "procedure"
    assert first_chunk["citation"]["source_id"] == "official_eps_procedure_001"

    assert package["citations"] == [first_chunk["citation"]]


def test_build_evidence_package_filters_f_grade_from_official_claims(tmp_path: Path) -> None:
    chunk_path = _write_chunk_file(
        tmp_path,
        [
            _document(
                source_id="synthetic_demo_case_001",
                title="E-9 절차 데모 케이스",
                evidence_grade="F",
                source_type="synthetic_case",
                doc_type="case",
            ),
            _document(
                source_id="message_template_passport_request_ko",
                title="여권 사본 요청 메시지",
                evidence_grade="E",
                source_type="message_template",
                doc_type="template",
                content="여권 사본 제출 안내 메시지 초안입니다.",
            ),
        ],
    )

    package = build_evidence_package(
        request_id="req_002",
        query="여권 사본 제출 안내",
        case_type="document_check",
        chunk_path=chunk_path,
    )

    assert package["status"] == "ready"
    assert {chunk["evidence_grade"] for chunk in package["retrieved_chunks"]} <= ANSWER_EVIDENCE_GRADES
    assert all(chunk["source_id"] != "synthetic_demo_case_001" for chunk in package["retrieved_chunks"])


def test_build_evidence_package_marks_empty_results_as_insufficient_evidence(tmp_path: Path) -> None:
    chunk_path = _write_chunk_file(
        tmp_path,
        [
            _document(
                source_id="official_eps_procedure_001",
                title="E-9 고용허가 절차",
                evidence_grade="B",
            )
        ],
    )

    package = build_evidence_package(
        request_id="req_003",
        query="완전히매칭되지않는질문",
        case_type="new_hiring",
        chunk_path=chunk_path,
    )

    assert package["status"] == "insufficient_evidence"
    assert package["retrieved_chunks"] == []
    assert package["citations"] == []
    assert package["missing_evidence"] == [
        {
            "reason": "no_retrieval_results",
            "query": "완전히매칭되지않는질문",
        }
    ]


def test_build_evidence_package_blocks_missing_required_metadata(tmp_path: Path) -> None:
    chunk_path = tmp_path / "chunks.jsonl"
    chunk_path.write_text(
        json.dumps(
            {
                "chunk_id": "broken_chunk_001",
                "source_id": "broken_source_001",
                "title": "Broken",
                "text": "E-9 고용허가 신청 절차",
                "metadata": {
                    "source_id": "broken_source_001",
                    "title": "Broken",
                    "evidence_grade": "B",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing evidence package metadata"):
        build_evidence_package(
            request_id="req_004",
            query="E-9 고용허가 신청 절차",
            case_type="new_hiring",
            chunk_path=chunk_path,
        )


def test_build_evidence_package_from_rag_eval_cases() -> None:
    dataset_path = Path("evals/datasets/rag_retrieval_cases.jsonl")
    chunk_path = Path("data-pipeline/processed/chunks/all_chunks.jsonl")

    with dataset_path.open("r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    for case in cases:
        package = build_evidence_package(
            request_id=f"req_{case['id']}",
            query=case["input"],
            case_type="new_hiring",
            chunk_path=chunk_path,
            answer_evidence_only=bool(case.get("answer_evidence_only", True)),
        )

        assert package["status"] == "ready"
        retrieved_source_ids = {chunk["source_id"] for chunk in package["retrieved_chunks"]}
        assert retrieved_source_ids & set(case["expected_source_ids"])
