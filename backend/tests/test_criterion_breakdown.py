from copy import deepcopy
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.api_breakdown import router
from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import Checklist, content_hash
from backend.app.services.criterion_breakdown import criterion_breakdown
from backend.app.services.evaluator import Provider
from backend.app.services.saved_results import SavedResultNotFound
from backend.tests.test_saved_inspection import db_rows


def judgment(value=True, disposition="assessed"):
    return {"value": value, "disposition": disposition, "explanation": "SYNTHETIC saved answer",
        "na_reason": "SYNTHETIC no follow-up required" if disposition == "not_applicable" else None,
        "review_reason": "SYNTHETIC missing source" if disposition == "needs_review" else None,
        "evidence": [] if disposition == "needs_review" else [{"kind": "support", "start_message_id": "m1", "end_message_id": "m1"}]}


def answers(binary=True, scale=20, flag=False):
    return {"results": {"binary": judgment(binary), "scale": judgment(scale), "flag": judgment(flag)}}


@pytest.fixture
def sample(tmp_path, monkeypatch):
    monkeypatch.setattr(Provider, "request", lambda *a, **k: pytest.fail("Breakdown must not request inference"))
    db = Database(tmp_path / "breakdown.sqlite3")
    rubric = Checklist.model_validate({"name": "SYNTHETIC breakdown", "sections": [{"id": "quality", "title": "Quality"}], "criteria": [
        {"id": "binary", "name": "Binary rule", "description": "Synthetic binary behavior", "section_id": "quality", "answer_type": "binary", "weight": "10", "na_allowed": True, "na_condition": "No follow-up required", "scale": []},
        {"id": "scale", "name": "Scale rule", "description": "Synthetic scale behavior", "section_id": "quality", "answer_type": "scale", "weight": "20", "na_allowed": True, "na_condition": "No follow-up required", "scale": [{"value": "0", "description": "No"}, {"value": "20", "description": "Yes"}]},
        {"id": "flag", "name": "Flag rule", "description": "Synthetic flag behavior", "section_id": "quality", "answer_type": "flag", "weight": None, "na_allowed": False, "na_condition": None, "scale": []}]})
    with db.transaction() as session:
        session.add(ChecklistVersion(id=1, snapshot=rubric.model_dump(mode="json"), content_hash=content_hash(rubric)))
    def source(cid, group="DEV", revision=1, source_id=None):
        with db.transaction() as session:
            session.add(Conversation(id=cid, group_id=group, source_id=source_id or cid, revision=revision, content_hash="HASH_" + cid,
                snapshot={"language": "EN", "channel": "agent chat", "audio_url": "https://example.invalid/PRIVATE_TEST_LINK", "transcript": [{"id": "m1", "text": "PRIVATE_TEST_TEXT", "speaker": "operator", "timestamp": "TEST"}]}))
    def run(cid, eid=None, original=None, effective=None, state="succeeded", stamp="2026-11-01T00:00:00Z", checklist_id=1):
        with db.transaction() as session:
            session.add(Evaluation(id=eid or "RUN_" + cid, conversation_id=cid, checklist_id=checklist_id, state=state,
                completeness="complete", cache_key="SYNTHETIC", original=original or answers(), effective=effective or original or answers(),
                created_at=stamp, updated_at=stamp))
    yield db, source, run, rubric
    db.engine.dispose()


def read(db, ids, basis="effective"):
    with db.read_snapshot() as session:
        return criterion_breakdown(session, 1, ids, basis)


def buckets(packet, cid="binary", group="DEV"):
    data = next(g for g in packet["groups"] if g["group_id"] == group)
    return {b["key"]: b for b in next(c for c in data["criteria"] if c["criterion_id"] == cid)["buckets"]}


def test_exact_counts_denominators_basis_and_case_targets(sample):
    db, source, run, _ = sample
    for cid in "abcdefg": source(cid)
    run("a", original=answers(flag=True))
    run("b", effective=answers(False, 0, False))
    na = answers(); na["results"]["binary"] = judgment(None, "not_applicable"); na["results"]["scale"] = judgment(None, "not_applicable"); na["results"]["flag"] = judgment(None, "needs_review")
    run("c", original=na)
    pending = {"results": {key: judgment(None, "needs_review") for key in ("binary", "scale", "flag")}}
    run("d", original=pending)
    run("e", state="failed")
    malformed = answers(0, True, None); run("g", original=malformed)
    before = db_rows(db)
    packet = read(db, list("abcdefg"))
    assert packet["total_sources"] == 7 and packet["basis"] == "effective"
    counts = buckets(packet)
    assert {k: b["count"] for k, b in counts.items()} == {"yes": 1, "no": 1, "not_applicable": 1, "needs_review": 1, "unavailable": 3}
    assert counts["yes"]["denominator"] == 7 and counts["yes"]["percentage"] == "14.29"
    assert counts["no"]["cases"] == [{"conversation_id": "b", "source_id": "b", "group_id": "DEV", "revision": 1, "evaluation_id": "RUN_b", "criterion_id": "binary"}]
    assert {k: b["count"] for k, b in buckets(packet, "scale").items()} == {"value:0": 1, "value:20": 1, "not_applicable": 1, "needs_review": 1, "unavailable": 3}
    assert {k: b["count"] for k, b in buckets(packet, "flag").items()} == {"flagged": 1, "clear": 1, "unknown": 5}
    assert packet["groups"][0]["coverage"] == {"not_evaluated": 1, "queued": 0, "running": 0, "succeeded": 5, "failed": 1, "interrupted": 0}
    assert buckets(read(db, list("abcdefg"), "original"))["yes"]["count"] == 2
    assert "PRIVATE_TEST" not in str(packet)
    assert db_rows(db) == before


def test_latest_failure_does_not_fall_back_and_ties_are_deterministic(sample):
    db, source, run, _ = sample
    source("a"); run("a", eid="old", stamp="2026-11-01")
    run("a", eid="failure", state="failed", stamp="2026-11-02")
    assert buckets(read(db, ["a"]))["unavailable"]["count"] == 1
    run("a", eid="zz_latest", state="interrupted", stamp="2026-11-02")
    packet = read(db, ["a"])
    assert packet["manifest"][0]["evaluation_id"] == "zz_latest"
    assert packet["groups"][0]["coverage"]["interrupted"] == 1


def test_group_boundaries_missing_members_and_empty_selection(sample):
    db, source, run, rubric = sample
    source("a"); source("b", group="SYNTHETIC"); run("a"); run("b", original=answers(False))
    packet = read(db, ["a", "b"])
    assert [g["group_id"] for g in packet["groups"]] == ["DEV", "SYNTHETIC"]
    assert buckets(packet)["yes"]["denominator"] == 1
    assert buckets(packet, group="SYNTHETIC")["no"]["count"] == 1
    with db.transaction() as session:
        row = session.get(Evaluation, "RUN_a"); missing = deepcopy(row.effective); del missing["results"]["flag"]; row.effective = missing
    assert buckets(read(db, ["a"]))["unavailable"]["count"] == 1
    assert read(db, [])["groups"] == []
    with pytest.raises(SavedResultNotFound): read(db, ["missing"])
    with pytest.raises(ValueError): read(db, ["a"], "invalid")


def test_api_is_read_only_bounded_and_rejects_stale_revisions(sample):
    db, source, run, _ = sample
    source("a", source_id="same"); run("a")
    app = FastAPI(); app.state.db = db; app.include_router(router)
    with TestClient(app) as client:
        before = db_rows(db)
        body = {"checklist_id": 1, "conversation_ids": ["a"]}
        response = client.post("/api/insights/breakdown", json=body)
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        assert client.post("/api/insights/breakdown", json={**body, "conversation_ids": ["a", "a"]}).status_code == 422
        assert client.post("/api/insights/breakdown", json={**body, "conversation_ids": [str(i) for i in range(201)]}).status_code == 422
        assert db_rows(db) == before
        source("new", revision=2, source_id="same")
        assert client.post("/api/insights/breakdown", json=body).status_code == 409


def test_equivalent_signed_zero_anchor_and_pending_jobs_remain_distinct(sample):
    db, source, run, _ = sample
    source("zero"); source("queued"); source("running")
    run("zero", original=answers(scale=0)); run("queued", state="queued"); run("running", state="running")
    with db.transaction() as session:
        version = session.get(ChecklistVersion, 1)
        changed = deepcopy(version.snapshot); changed["criteria"][1]["scale"][0]["value"] = "-0.00"
        version.snapshot = changed
    packet = read(db, ["zero", "queued", "running"])
    assert buckets(packet, "scale")["value:0"]["count"] == 1
    assert buckets(packet, "scale")["unavailable"]["count"] == 2
    assert packet["groups"][0]["coverage"]["queued"] == packet["groups"][0]["coverage"]["running"] == 1


@pytest.mark.parametrize("kind", ["extra_criterion", "missing_criterion", "unconfigured_anchor", "boolean_anchor", "invalid_na"])
def test_incompatible_or_malformed_answers_never_become_passes(sample, kind):
    db, source, run, _ = sample
    source("a")
    value = answers()
    if kind == "extra_criterion": value["results"]["extra"] = judgment(True)
    elif kind == "missing_criterion": del value["results"]["binary"]
    elif kind == "unconfigured_anchor": value["results"]["scale"] = judgment(5)
    elif kind == "boolean_anchor": value["results"]["scale"] = judgment(True)
    else: value["results"]["scale"] = judgment(20, "not_applicable")
    run("a", original=value)
    packet = read(db, ["a"])
    assert buckets(packet, "scale")["unavailable"]["count"] == 1
    assert buckets(packet, "scale")["value:20"]["count"] == 0
    if kind in {"extra_criterion", "missing_criterion"}:
        assert buckets(packet)["yes"]["count"] == 0
        assert buckets(packet, "flag")["unknown"]["count"] == 1
