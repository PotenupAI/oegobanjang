import json
from pathlib import Path


def test_source_manifest_has_minimum_mvp_sources() -> None:
    manifest = json.loads(Path("data-pipeline/raw/source_manifest.json").read_text(encoding="utf-8"))
    sources = manifest["sources"]

    assert len(sources) >= 20
    assert {source["source_id"] for source in sources} >= {
        "eps_employer_process_001",
        "eps_allowed_industries_001",
        "gov24_stay_extension_001",
        "law_foreign_worker_act_001",
        "kosha_multilingual_safety_001",
    }


def test_source_manifest_rows_have_metadata_contract() -> None:
    manifest = json.loads(Path("data-pipeline/raw/source_manifest.json").read_text(encoding="utf-8"))
    required = {"source_id", "title", "official_url", "publisher", "source_type", "doc_type", "evidence_grade"}

    for source in manifest["sources"]:
        missing = required - set(source)
        assert not missing, f"{source.get('source_id')} missing {sorted(missing)}"
        assert source["evidence_grade"] in {"A", "B", "C", "D", "E", "F"}
