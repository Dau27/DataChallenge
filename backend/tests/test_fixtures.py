import json
from pathlib import Path

from backend.app.domain import ImportEnvelope


def test_public_behavioral_fixtures_are_explicitly_synthetic_and_multilingual():
    envelope = ImportEnvelope.model_validate_json(Path("tests/fixtures/semantic_cases.json").read_text(encoding="utf-8"))
    expectations = json.loads(Path("tests/fixtures/semantic_expectations.json").read_text(encoding="utf-8"))
    assert envelope.data.dataset_group_id == "SYNTHETIC_TEST_ONLY"
    assert len(envelope.data.records) == 10
    assert {record.language for record in envelope.data.records} == {"RU", "KZ", "EN"}
    assert all(record.conversation_id.startswith("TEST-") and record.audio_url is None for record in envelope.data.records)
    assert "not independent human labels" in expectations["label_provenance"]
    assert set(expectations["cases"]) == {record.conversation_id for record in envelope.data.records}
