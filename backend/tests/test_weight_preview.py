from copy import deepcopy
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy import select

from backend.app.api_weight_preview import router
from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import Assessment, Checklist, content_hash
from backend.app.services.evaluator import Provider
from backend.app.services.scoring import score
from backend.app.services.weight_preview import preview_runs, weight_preview
from backend.tests.conftest import full_assessment


def judgment(value=True, disposition="assessed"):
    return {"disposition": disposition, "value": value, "explanation": "SYNTHETIC saved judgment",
        "na_reason": "The synthetic applicability condition holds" if disposition == "not_applicable" else None,
        "review_reason": "SYNTHETIC missing authoritative source" if disposition == "needs_review" else None,
        "evidence": [{"kind": "context", "start_message_id": "m0001", "end_message_id": "m0001"}]}


@pytest.fixture
def saved(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Weight preview must never call a provider or HTTP transport")
    monkeypatch.setattr(Provider, "request", forbidden)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", forbidden)
    db = Database(tmp_path / "weights.sqlite3")
    criteria = [{"id": name, "name": name, "description": "SYNTHETIC custom rule " + name,
        "section_id": "s", "answer_type": "binary", "weight": "10", "na_allowed": True,
        "na_condition": "SYNTHETIC applicability condition", "scale": []} for name in ("a", "b", "c")]
    criteria[2].update(answer_type="scale", scale=[{"value": n, "description": "SYNTHETIC anchor"} for n in (0, .5, 1)])
    criteria.append({**criteria[0], "id": "f", "name": "Flag", "answer_type": "flag", "weight": None, "na_allowed": False, "na_condition": None})
    checklist = Checklist.model_validate({"name": "SYNTHETIC weights", "sections": [{"id": "s", "title": "Synthetic"}], "criteria": criteria})
    assessment = Assessment.model_validate({"results": {"a": judgment(), "b": judgment(False), "c": judgment(.5), "f": judgment(False)}})
    with db.transaction() as session:
        version = ChecklistVersion(snapshot=checklist.model_dump(mode="json"), content_hash=content_hash(checklist))
        source = Conversation(id="SOURCE", group_id="SYNTHETIC_TEST_ONLY", source_id="TEST_SOURCE", revision=1, content_hash="HASH",
            snapshot={"language": "EN", "channel": "agent chat", "audio_url": "https://example.invalid/PRIVATE_RECORDING", "transcript": [
                {"id": "m0001", "speaker": "client", "timestamp": "00:00", "text": "SYNTHETIC client"},
                {"id": "m0002", "speaker": "operator", "timestamp": "00:01", "text": "SYNTHETIC operator"}]})
        session.add_all([version, source]); session.flush()
        session.add(Evaluation(id="RUN", conversation_id="SOURCE", checklist_id=version.id, state="succeeded", completeness="complete", cache_key="TEST",
            original=assessment.model_dump(mode="json"), effective=assessment.model_dump(mode="json"), original_score=score(checklist, assessment), effective_score=score(checklist, assessment),
            meta={"checklist_hash": version.content_hash}, updated_at="2026-11-07T01:00:00Z"))
    return db, checklist


def simulate(saved, draft=None, basis="effective"):
    db, checklist = saved
    with db.read_snapshot() as session:
        return weight_preview(session, 1, "RUN", basis, draft or checklist.model_dump(mode="json"))


def test_weight_scenario_and_identity_are_read_only(saved):
    db, checklist = saved
    with db.sessions() as session:
        before = {row.id: (deepcopy(row.original), deepcopy(row.effective), deepcopy(row.original_score), deepcopy(row.effective_score), row.updated_at) for row in session.scalars(select(Evaluation))}
    unchanged = simulate(saved)
    assert unchanged["eligible"] and unchanged["original_score"] == unchanged["simulated_score"]
    draft = checklist.model_dump(mode="json"); draft["criteria"][0]["weight"] = "20"
    result = simulate(saved, draft)
    assert result["original_score"]["total"] == "50.00"
    assert result["simulated_score"]["total"] == "62.50" and result["total_difference"] == "12.50"
    assert result["simulated_score"]["applicable_weight"] == "40"
    assert result["criteria"][-1]["original"]["raw_points"] is None
    assert result["source"]["content_hash"] == "HASH" and result["updated_at"] == "2026-11-07T01:00:00Z"
    assert "PRIVATE_RECORDING" not in json.dumps(result) and "SYNTHETIC client" not in json.dumps(result)
    with db.sessions() as session:
        after = {row.id: (row.original, row.effective, row.original_score, row.effective_score, row.updated_at) for row in session.scalars(select(Evaluation))}
    assert before == after


@pytest.mark.parametrize("change", ["name", "description", "order", "sections", "scale", "na_condition", "na_allowed", "source_notes", "source", "initial_version_label", "remove", "add", "type"])
def test_nonweight_changes_are_not_scenarios(saved, change):
    _, checklist = saved
    draft = checklist.model_dump(mode="json")
    if change == "name": draft["name"] = "Changed title"
    elif change == "description": draft["criteria"][0]["description"] = "Changed meaning"
    elif change == "order": draft["criteria"].reverse()
    elif change == "sections": draft["sections"][0]["title"] = "Changed section"
    elif change == "scale": draft["criteria"][2]["scale"][0]["description"] = "Changed anchor"
    elif change == "na_condition": draft["criteria"][0]["na_condition"] = "Changed condition"
    elif change == "na_allowed": draft["criteria"][0].update(na_allowed=False, na_condition=None)
    elif change == "source_notes": draft["source_notes"] = ["Changed note"]
    elif change == "source": draft["source"] = {"title": "Changed source"}
    elif change == "initial_version_label": draft["initial_version_label"] = "Changed label"
    elif change == "remove": draft["criteria"].pop()
    elif change == "add": draft["criteria"].append({**draft["criteria"][0], "id": "added"})
    else: draft["criteria"][2].update(answer_type="binary", scale=[])
    result = simulate(saved, draft)
    assert not result["eligible"] and "Only criterion weights" in result["reasons"][0]


def test_invalid_weight_has_field_error(saved):
    _, checklist = saved
    draft = checklist.model_dump(mode="json"); draft["criteria"][0]["weight"] = "-1"
    result = simulate(saved, draft)
    assert not result["eligible"] and result["errors"][0]["location"] == ["criteria", 0, "weight"]


@pytest.mark.parametrize("state", ["not_applicable", "needs_review", "all_na", "unknown_flag"])
def test_applicability_uncertainty_and_basis_are_preserved(saved, state):
    db, checklist = saved
    with db.transaction() as session:
        run = session.get(Evaluation, "RUN"); raw = deepcopy(run.effective)
        if state == "all_na":
            for cid in ("a", "b", "c"): raw["results"][cid] = judgment(None, "not_applicable")
        elif state == "unknown_flag": raw["results"]["f"] = judgment(None, "needs_review")
        else: raw["results"]["a"] = judgment(None, state)
        run.effective = raw; run.effective_score = score(checklist, Assessment.model_validate(raw))
    draft = checklist.model_dump(mode="json"); draft["criteria"][0]["weight"] = "100"
    result = simulate(saved, draft)
    assert result["eligible"] and simulate(saved, draft, "original")["original_score"]["total"] == "50.00"
    if state == "not_applicable":
        assert result["original_score"]["total"] == result["simulated_score"]["total"] == "25.00"
        assert result["simulated_score"]["applicable_weight"] == "20"
    else:
        assert result["original_score"]["total"] is result["simulated_score"]["total"] is None
        assert result["total_difference"] is None


@pytest.mark.parametrize("problem", ["other_version", "recorded_hash", "version_hash", "failed", "missing_basis", "score_mismatch", "bad_evidence"])
def test_mismatched_or_unreplayable_runs_refused(saved, problem):
    db, _ = saved
    with db.transaction() as session:
        run = session.get(Evaluation, "RUN")
        if problem == "other_version":
            version = session.get(ChecklistVersion, 1)
            new = ChecklistVersion(snapshot=deepcopy(version.snapshot), content_hash=version.content_hash); session.add(new); session.flush(); run.checklist_id = new.id
        elif problem == "recorded_hash": run.meta = {"checklist_hash": "wrong"}
        elif problem == "version_hash": session.get(ChecklistVersion, 1).content_hash = "wrong"
        elif problem == "failed": run.state = "failed"
        elif problem == "missing_basis": run.effective = None
        elif problem == "score_mismatch": run.effective_score = {**run.effective_score, "total": "99.00"}
        else:
            raw = deepcopy(run.effective); raw["results"]["a"]["evidence"][0]["end_message_id"] = "MISSING"; run.effective = raw
    assert not simulate(saved)["eligible"]


def test_legacy_record_without_new_source_guard_is_not_rejudged(saved, checklist):
    db, _ = saved
    assessment = full_assessment(checklist, message_id="m0001")
    with db.transaction() as session:
        version = session.get(ChecklistVersion, 1); version.snapshot = checklist.model_dump(mode="json"); version.content_hash = content_hash(checklist)
        run = session.get(Evaluation, "RUN"); run.meta = {}  # Original foreign-key snapshot remains authoritative.
        run.original = assessment.model_dump(mode="json"); run.original_score = score(checklist, assessment)
    with db.read_snapshot() as session:
        result = weight_preview(session, 1, "RUN", "original", checklist.model_dump(mode="json"))
    assert result["eligible"] and result["original_score"] == result["simulated_score"]


def test_http_pagination_no_store_and_no_side_effects(saved):
    db, checklist = saved
    with db.transaction() as session:
        first = session.get(Evaluation, "RUN")
        session.add(Evaluation(id="RUN2", conversation_id=first.conversation_id, checklist_id=1, state="succeeded", completeness="complete", cache_key="TEST2",
            original=deepcopy(first.original), effective=deepcopy(first.effective), original_score=deepcopy(first.original_score), effective_score=deepcopy(first.effective_score), meta=deepcopy(first.meta)))
    app = FastAPI(); app.state.db = db; app.include_router(router)
    with TestClient(app) as client:
        page = client.get('/api/insights/weight-preview/runs?checklist_id=1&limit=1')
        assert page.status_code == 200 and page.headers["cache-control"] == "no-store"
        packet = page.json(); assert packet["total"] == 2 and len(packet["runs"]) == 1
        second = client.get('/api/insights/weight-preview/runs?checklist_id=1&limit=1&offset=1').json()
        assert second["runs"][0]["id"] != packet["runs"][0]["id"]
        assert "original" not in packet["runs"][0] and "snapshot" not in packet["runs"][0]
        response = client.post('/api/insights/weight-preview', json={"checklist_id": 1, "evaluation_id": "RUN", "basis": "effective", "draft": checklist.model_dump(mode="json")})
        assert response.status_code == 200 and response.json()["eligible"] and response.headers["cache-control"] == "no-store"
        assert client.get('/api/insights/weight-preview/runs?checklist_id=1&limit=201').status_code == 422
    with db.sessions() as session:
        assert len(list(session.scalars(select(Evaluation)))) == 2 and len(list(session.scalars(select(ChecklistVersion)))) == 1
