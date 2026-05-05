from pathlib import Path

from app.agent_runtime.tools.document_check_tool import calculate_missing_documents


def test_calculate_missing_documents_for_new_hiring_e9() -> None:
    result = calculate_missing_documents(
        {
            "case_type": "new_hiring",
            "visa_type": "E-9",
            "held_documents": ["passport", "health_certificate"],
        },
        requirements_path=Path("data-pipeline/seed/document_requirements.csv"),
    )

    assert result["tool_name"] == "calculate_missing_documents"
    assert result["tool_grade"] == "SAFE_CALCULATE"
    assert result["status"] == "SUCCESS"
    assert result["approval_required"] is False
    assert result["output"]["case_type"] == "new_hiring"
    assert result["output"]["visa_type"] == "E-9"
    assert "criminal_record" in result["output"]["missing_documents"]
    assert "passport" not in result["output"]["missing_documents"]
    assert result["risk_flags"] == ["missing_required_documents"]


def test_calculate_missing_documents_requires_case_type() -> None:
    result = calculate_missing_documents(
        {"visa_type": "E-9", "held_documents": []},
        requirements_path=Path("data-pipeline/seed/document_requirements.csv"),
    )

    assert result["status"] == "FAILED"
    assert result["error"] == "case_type is required"


def test_calculate_missing_documents_accepts_db_document_state() -> None:
    result = calculate_missing_documents(
        {
            "case_type": "new_hiring",
            "visa_type": "E-9",
            "db_document_state": {
                "passport": {"status": "verified"},
                "health_certificate": {"status": "submitted"},
                "criminal_record": {"status": "missing"},
            },
        },
        requirements_path=Path("data-pipeline/seed/document_requirements.csv"),
    )

    assert result["status"] == "SUCCESS"
    assert result["input_snapshot"]["document_state_source"] == "db_document_state"
    assert "passport" not in result["output"]["missing_documents"]
    assert "health_certificate" not in result["output"]["missing_documents"]
    assert "criminal_record" in result["output"]["missing_documents"]
