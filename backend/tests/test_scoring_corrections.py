"""Replay audit corrections against labeled synthetic saved outputs, never live inference.

These verify review/scoring/preservation behavior, not model semantic accuracy.
"""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal

from fastapi.testclient import TestClient
import httpx
import pytest

from backend.app.domain import Checklist
from backend.app.main import create_app
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import client_and_calls, evaluate_one, response_for, synthetic_payload


def judgment(value=None, *, disposition="assessed", reason=None, message="m0002"):
    return {"disposition": disposition, "value": value, "explanation": "SYNTHETIC source-grounded correction",
            "na_reason": reason if disposition == "not_applicable" else None,
            "review_reason": reason if disposition == "needs_review" else None,
            "evidence": [{"kind": "context" if disposition == "needs_review" else "support",
                          "start_message_id": message, "end_message_id": message}]}


def save_decision(client, result, appeal, replacement):
    return client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace",
        "rationale": "SYNTHETIC agent review; not independent human validation", "judgment": replacement,
        "expected_updated_at": result["updated_at"]})


def appeal_for(client, result, criterion_id):
    response = client.post(f"/api/evaluations/{result['id']}/appeals", json={
        "criterion_id": criterion_id, "comment": "SYNTHETIC saved answer requires source correction"})
    assert response.status_code == 201
    return response.json()["id"]


def deny_request(*args, **kwargs):
    pytest.fail("A saved-result correction must not send a model request")


def test_necessary_details_and_correct_next_step_recompute_without_replacing_original(tmp_path, monkeypatch):
    def historical_output(payload):
        import json
        checklist = Checklist.model_validate(json.loads(payload["input"])["saved_checklist"])
        result = full_assessment(checklist).model_dump(mode="json")
        result["results"]["needs"] = judgment(disposition="not_applicable", reason="SYNTHETIC erroneous sufficiency")
        result["results"]["identification"] = judgment(disposition="not_applicable", reason="General guidance only")
        result["results"]["consultation"] = judgment(10)
        return httpx.Response(200, json=response_for(result))

    client, calls, settings = client_and_calls(tmp_path, historical_output)
    with client:
        payload = synthetic_payload(language="KZ")
        messages = payload["data"]["records"][0]["transcript"]
        messages[0]["text"] = "SYNTHETIC: облигацияны сатып алу өтінімі қабылданбады."
        messages[1]["text"] = "Сәлеметсіз бе, мен Айыммын. Тикер мен қате хабарламасын жіберіңіз, тексеруге жолдаймын."
        result = evaluate_one(client, client.post("/api/import/json", json=payload).json()["conversation_ids"][0])
        assert result["original_score"]["total"] == "84.62"
    monkeypatch.setattr("backend.app.services.evaluator.Provider.request", deny_request)
    paused = replace(settings, api_key="", budget_limit_usd=Decimal("0"))
    with TestClient(create_app(paused)) as client:
        for criterion_id, replacement, expected in [("needs", judgment(True), "87.50"), ("consultation", judgment(20), "100.00")]:
            appeal = appeal_for(client, result, criterion_id)
            assert save_decision(client, result, appeal, replacement).status_code == 201
            result = client.get(f"/api/evaluations/{result['id']}").json()
            assert result["effective_score"]["total"] == expected
            assert result["original_score"]["total"] == "84.62"
        before_restart = deepcopy(result)
        assert all(a["status"] == "decided" for a in result["appeals"])
    with TestClient(create_app(paused)) as client:
        restored = client.get(f"/api/evaluations/{result['id']}").json()
        for field in ("original", "original_score", "effective", "effective_score", "attempts", "reviews", "appeals"):
            assert restored[field] == before_restart[field]
        assert restored["effective"]["results"]["needs"]["na_reason"] is None
        assert len(restored["reviews"]) == 2 and len(calls) == 1


def test_unclear_introduction_retracts_credit_keeps_appeal_open_and_can_later_resolve(tmp_path, monkeypatch):
    client, calls, settings = client_and_calls(tmp_path)
    with client:
        payload = synthetic_payload(language="RU", channel="voice call")
        payload["data"]["records"][0]["transcript"][1]["text"] = "Компания [неразборчиво]. Здравствуйте, чем могу помочь?"
        imported = client.post("/api/import/json", json=payload)
        assert imported.status_code == 200, imported.text
        result = evaluate_one(client, imported.json()["conversation_ids"][0])
        # Simulate a retained historical positive, independent of the current prompt.
        appeal = appeal_for(client, result, "contact")
        assert save_decision(client, result, appeal, judgment(True)).status_code == 201
        result = client.get(f"/api/evaluations/{result['id']}").json()
        appeal = appeal_for(client, result, "contact")
    monkeypatch.setattr("backend.app.services.evaluator.Provider.request", deny_request)
    paused = replace(settings, api_key="", budget_limit_usd=Decimal("0"))
    with TestClient(create_app(paused)) as client:
        pending = judgment(disposition="needs_review", reason="Opening ASR is unintelligible; recording review is required.")
        for invalid in ("", "none", "/none/", "N/A"):
            broken = {**pending, "review_reason": invalid}
            assert save_decision(client, result, appeal, broken).status_code == 422
        original, original_score = deepcopy(result["original"]), deepcopy(result["original_score"])
        assert save_decision(client, result, appeal, pending).status_code == 201
        result = client.get(f"/api/evaluations/{result['id']}").json()
        assert result["effective_score"]["total"] is None
        assert result["effective_score"]["reason"] == "UNRESOLVED_CRITERIA"
        assert result["completeness"] == "needs_review"
        assert result["effective"]["results"]["contact"]["value"] is None
        assert next(a for a in result["appeals"] if a["id"] == appeal)["status"] == "open"
        assert client.get("/api/conversations?checklist_id=1").json()[0]["pending_appeals"] == 1
        body = {"action": "confirm", "rationale": "SYNTHETIC invalid confirmation", "judgment": None, "expected_updated_at": result["updated_at"]}
        assert client.post(f"/api/appeals/{appeal}/decision", json=body).status_code == 422
    with TestClient(create_app(paused)) as client:
        restored = client.get(f"/api/evaluations/{result['id']}").json()
        assert restored["effective_score"]["total"] is None and restored["reviews"] == result["reviews"]
        assert restored["original"] == original and restored["original_score"] == original_score
        # Later qualified resolution is simulated only; the real audited call remains unverified.
        assert save_decision(client, restored, appeal, judgment(False)).status_code == 201
        final = client.get(f"/api/evaluations/{result['id']}").json()
        assert final["effective_score"]["total"] == original_score["total"]
        assert final["effective_score"]["completeness"] == "complete"
        assert len(final["reviews"]) == 3
        assert final["reviews"][1]["judgment"]["disposition"] == "needs_review"
        assert client.get("/api/conversations?checklist_id=1").json()[0]["pending_appeals"] == 0
    assert len(calls) == 1
