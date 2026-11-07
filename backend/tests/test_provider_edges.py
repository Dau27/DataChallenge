import httpx
import pytest

from backend.app.config import Settings
from backend.app.domain import Checklist, content_hash
from backend.app.services.evaluator import Provider, cache_key, output_schema
from backend.tests.test_workflow import client_and_calls, evaluate_one, import_one, response_for


def test_exhausted_credit_does_not_trigger_repair_or_automatic_retry(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, lambda _: httpx.Response(429, json={"error": {
        "code": "credit_balance_exhausted", "type": "insufficient_quota", "message": "PRIVATE provider message"}}))
    with client:
        result = evaluate_one(client, import_one(client))
        assert result["state"] == "failed" and len(calls) == 1
        assert result["attempts"][0]["error_code"] == "credit_balance_exhausted"
        assert "quota/billing" in result["error"] and "PRIVATE" not in result["error"]
        assert result["original"] is None


@pytest.mark.parametrize("code", ["organization_spend_limit_exceeded", "project_spend_limit_exceeded", "organization_usage_limit_exceeded"])
def test_other_nonretryable_provider_limits_require_action(tmp_path, code):
    client, calls, _ = client_and_calls(tmp_path, lambda _: httpx.Response(429, json={"error": {"code": code}}))
    with client:
        result = evaluate_one(client, import_one(client))
        assert len(calls) == 1 and code in result["error"]


def test_provider_access_route_reports_verified_structured_response(tmp_path):
    client, _, settings = client_and_calls(tmp_path, lambda _: httpx.Response(200, json=response_for({"ok": True})))
    with client:
        assert client.get("/api/access").json()["provider_verified"] is False
        assert client.post("/api/access/check-provider").json()["succeeded"] is True
        assert client.get("/api/access").json()["provider_verified"] is True
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get("/api/access").json()["provider_verified"] is True
    from dataclasses import replace
    with TestClient(create_app(replace(settings, api_key="sk-OTHER-TEST-KEY"))) as changed:
        assert changed.get("/api/access").json()["provider_verified"] is False


def test_refusal_and_token_limit_do_not_save_assessments(tmp_path):
    for status in ["refused", "incomplete"]:
        def handler(_, state=status):
            body = {"status": "incomplete", "usage": {"input_tokens": 20, "output_tokens": 10}, "output": []}
            if state == "refused":
                body.update(status="completed", output=[{"content": [{"type": "refusal", "refusal": "PRIVATE refusal text"}]}])
            return httpx.Response(200, json=body)
        client, calls, _ = client_and_calls(tmp_path / status, handler)
        with client:
            result = evaluate_one(client, import_one(client))
            assert result["state"] == "failed" and len(calls) == 1
            assert result["original"] is None and "PRIVATE" not in result["error"]


def test_long_retry_after_defers_without_retrying_early(tmp_path):
    client, calls, _ = client_and_calls(tmp_path, lambda _: httpx.Response(429, headers={"retry-after": "1728"}, json={"error": {"code": "rate_limit_exceeded"}}))
    with client:
        result = evaluate_one(client, import_one(client))
        assert result["state"] == "failed" and len(calls) == 1
        assert result["attempts"][0]["retry_after_seconds"] == 1728
        assert "Defer this job" in result["error"]


@pytest.mark.parametrize("change", ["description", "name", "na_condition", "section", "weight", "scale", "remove", "rename_id", "model", "generation", "audio_hash"])
def test_every_evaluation_relevant_change_invalidates_cache(checklist, tmp_path, change):
    from dataclasses import replace
    settings = Settings(database_path=tmp_path / "test.sqlite3", api_key="sk-TEST", model="TEST_MODEL")
    source_hash = "TEST_CONTENT_HASH"
    before = cache_key(source_hash, checklist, settings)
    if change == "description": checklist.criteria[0].description = "Substantively changed TEST definition"
    if change == "name": checklist.criteria[0].name = "Changed TEST name"
    if change == "na_condition": checklist.criteria[1].na_condition = "Changed TEST applicability rule"
    if change == "section": checklist.criteria[0].section_id = checklist.sections[1].id
    if change == "weight": checklist.criteria[0].weight += 1
    if change == "scale": checklist.criteria[3].scale[0].description = "Changed TEST anchor"
    if change == "remove": checklist.criteria.pop()
    if change == "rename_id": checklist.criteria[0].id = "TEST_NEW_ID"
    if change == "model": settings = replace(settings, model="TEST_OTHER_MODEL")
    if change == "generation": settings = replace(settings, max_output_tokens=2048)
    if change == "audio_hash": source_hash = "TEST_CHANGED_SOURCE_AUDIO_HASH"
    assert before != cache_key(source_hash, checklist, settings)


def test_generated_schema_follows_removed_and_renamed_criteria(checklist):
    checklist.criteria.pop()
    checklist.criteria[0].id = "CUSTOM_TEST_ID"
    schema = output_schema(checklist)["properties"]["results"]
    assert "CUSTOM_TEST_ID" in schema["properties"]
    assert "contact" not in schema["properties"] and "critical_errors" not in schema["properties"]
    assert set(schema["required"]) == set(schema["properties"])


def test_model_schema_constrains_choices_and_source_evidence(checklist):
    properties = output_schema(checklist, ["m0001", "m0002"])["properties"]["results"]["properties"]
    contact = properties["contact"]["properties"]
    branches = contact["decision"]["anyOf"]
    assert {next(iter(b["properties"])) for b in branches} == {"assessed_value", "needs_review_reason"}
    assert branches[0]["properties"]["assessed_value"]["type"] == "boolean"
    assert contact["evidence"]["minItems"] == 1
    assert contact["evidence"]["items"]["properties"]["start_message_id"]["enum"] == ["m0001", "m0002"]
    assert properties["dialogue_management"]["properties"]["decision"]["anyOf"][0]["properties"]["assessed_value"]["enum"] == [10.0, 7.0, 4.0, 0.0]
