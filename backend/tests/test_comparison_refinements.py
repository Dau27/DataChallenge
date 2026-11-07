"""Comparison provenance and review updates remain read-only and provider-free."""
from copy import deepcopy

from backend.app.db import Evaluation
from backend.tests.test_saved_inspection import saved, db_rows


def test_comparison_exposes_saved_hashes_and_only_recorded_model_identifiers(saved):
    client, db, _, _, _ = saved
    with db.transaction() as session:
        row = session.get(Evaluation, "right")
        row.meta = {**row.meta, "prompt_hash": "a" * 64, "schema_hash": "b" * 64,
                    "api_key": "PRIVATE_TEST_VALUE", "raw_request": {"authorization": "PRIVATE_TEST_VALUE"},
                    "generation": {"temperature": 0, "max_output_tokens": 6000, "api_key": "PRIVATE_TEST_VALUE"}}
        row.attempts = [{"response_model": value, "input_tokens": 1, "output_tokens": 1, "latency_ms": 0}
            for value in ("gpt-4.1-mini-2025-04-14", "gpt-4.1-mini-2025-04-14", "TEST-MODEL-2",
                          "https://example.invalid/?token=PRIVATE_TEST_VALUE", "sk-PRIVATE_TEST_VALUE")]
    before = db_rows(db)
    response = client.get("/api/evaluations/compare?left_id=left&right_id=right")
    assert response.status_code == 200
    metadata = response.json()["right"]["metadata"]
    assert metadata["prompt_hash"] == "a" * 64 and metadata["schema_hash"] == "b" * 64
    assert metadata["response_models"] == ["gpt-4.1-mini-2025-04-14", "TEST-MODEL-2"]
    assert metadata["generation"] == {"temperature": 0, "max_output_tokens": 6000}
    assert "PRIVATE_TEST_VALUE" not in response.text
    assert db_rows(db) == before


def test_comparison_omits_malformed_provenance_instead_of_exposing_nested_metadata(saved):
    client, db, _, _, _ = saved
    with db.transaction() as session:
        row = session.get(Evaluation, "right")
        row.meta = {"prompt_hash": {"api_key": "PRIVATE_TEST_VALUE"}, "schema_hash": "invalid hash",
                    "model": {"authorization": "PRIVATE_TEST_VALUE"},
                    "generation": {"temperature": {"api_key": "PRIVATE_TEST_VALUE"}, "reasoning": {"effort": {"api_key": "PRIVATE_TEST_VALUE"}}}}
    before = db_rows(db)
    response = client.get("/api/evaluations/compare?left_id=left&right_id=right")
    assert response.status_code == 200
    metadata = response.json()["right"]["metadata"]
    assert "prompt_hash" not in metadata and "schema_hash" not in metadata and "model" not in metadata
    assert metadata["generation"] == {} and metadata["response_models"] == []
    assert "PRIVATE_TEST_VALUE" not in response.text
    assert db_rows(db) == before


def test_new_comparison_read_after_review_has_new_revision_and_withheld_total(saved):
    client, db, _, _, _ = saved
    original = client.get("/api/evaluations/right").json()
    old = client.get("/api/evaluations/compare?left_id=left&right_id=right").json()
    judgment = deepcopy(original["effective"]["results"]["contact"])
    judgment.update(disposition="needs_review", value=None, review_reason="SYNTHETIC: source unclear")
    appeal = client.post("/api/evaluations/right/appeals", json={"criterion_id": "contact", "comment": "SYNTHETIC review"}).json()["id"]
    decision = client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace", "rationale": "SYNTHETIC missing evidence",
        "judgment": judgment, "expected_updated_at": original["updated_at"]})
    assert decision.status_code == 201
    before = db_rows(db)
    new = client.get("/api/evaluations/compare?left_id=left&right_id=right").json()
    assert new["right"]["id"] == old["right"]["id"]
    assert new["right"]["updated_at"] != old["right"]["updated_at"]
    assert old["right"]["score"]["total"] == "100.00" and new["right"]["score"]["total"] is None
    assert new["total_difference"] is None and not new["total_comparable"]
    assert client.get("/api/evaluations/right").json()["original"] == original["original"]
    assert db_rows(db) == before
