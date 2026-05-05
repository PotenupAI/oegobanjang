from pathlib import Path

from app.agent_runtime.langchain_runtime.documents import chunk_to_document, load_policy_documents
from app.agent_runtime.langchain_runtime.vectorstore import build_persistent_index


def test_chunk_to_document_preserves_required_metadata() -> None:
    document = chunk_to_document(
        {
            "chunk_id": "chunk_001",
            "text": "EPS 고용허가 절차 안내",
            "metadata": {
                "source_id": "eps_employer_process_001",
                "title": "사업주 고용절차",
                "publisher": "EPS",
                "evidence_grade": "B",
                "chunk_type": "procedure",
                "ignored": "not-preserved",
            },
        }
    )

    assert document.page_content == "EPS 고용허가 절차 안내"
    assert document.metadata["source_id"] == "eps_employer_process_001"
    assert document.metadata["title"] == "사업주 고용절차"
    assert document.metadata["publisher"] == "EPS"
    assert document.metadata["evidence_grade"] == "B"
    assert document.metadata["chunk_type"] == "procedure"
    assert "ignored" not in document.metadata


def test_load_policy_documents_from_existing_chunks() -> None:
    documents = load_policy_documents("data-pipeline/processed/chunks/all_chunks.jsonl")

    assert documents
    assert all("source_id" in document.metadata for document in documents[:10])
    assert all("evidence_grade" in document.metadata for document in documents[:10])


def test_build_persistent_index_writes_manifest_and_documents(tmp_path: Path) -> None:
    manifest = build_persistent_index(
        chunk_path="data-pipeline/processed/chunks/all_chunks.jsonl",
        output_dir=tmp_path,
    )

    assert manifest["document_count"] > 0
    assert "source_id" in manifest["metadata_fields"]
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "documents.jsonl").exists()
