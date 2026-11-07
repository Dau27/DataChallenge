"""Saved-data features must work with no provider and a zero inference budget."""
from copy import deepcopy
import csv
import io
import json

from fastapi.testclient import TestClient
import pytest

from backend.app.config import Settings
from backend.app.db import Evaluation, ChecklistVersion
from backend.app.domain import Checklist, content_hash
from backend.app.main import create_app
from backend.app.services.evaluator import Provider
from backend.app.services.scoring import score
from backend.app.services.saved_results import evaluation_snapshot
from backend.tests.conftest import full_assessment
from backend.tests.test_workflow import import_one, synthetic_payload


@pytest.fixture
def saved(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Saved inspection attempted provider inference")
    monkeypatch.setattr(Provider, "request", forbidden)
    app = create_app(Settings(database_path=tmp_path / "saved.sqlite3", api_key="sk-EXPORT-TEST",
                              model="UNUSED", organizer_url="https://example.invalid/private-organizer"))
    with TestClient(app) as client:
        cid = import_one(client)
        with app.state.db.sessions() as session:
            checklist = Checklist.model_validate(session.get(ChecklistVersion, 1).snapshot)

        def add(run_id, rubric=checklist, assessment=None, state="succeeded"):
            assessment = assessment or full_assessment(rubric)
            result = assessment.model_dump(mode="json") if state == "succeeded" else None
            calculated = score(rubric, assessment) if result else None
            with app.state.db.transaction() as session:
                version = session.query(ChecklistVersion).filter_by(content_hash=content_hash(rubric)).first()
                if not version:
                    version = ChecklistVersion(content_hash=content_hash(rubric), snapshot=rubric.model_dump(mode="json"))
                    session.add(version); session.flush()
                session.add(Evaluation(id=run_id, conversation_id=cid, checklist_id=version.id, cache_key="TEST_ONLY",
                    state=state, completeness=calculated["completeness"] if calculated else "incomplete",
                    original=result, effective=deepcopy(result), original_score=calculated, effective_score=deepcopy(calculated),
                    meta={"model": "SAVED_TEST_MODEL", "prompt_version": "SAVED_TEST_PROMPT", "generation": {"temperature": 0}},
                    attempts=[], error="Saved failure" if not result else None))
            return run_id

        add("left"); add("right")
        yield client, app.state.db, checklist, cid, add


def db_rows(db):
    with db.engine.connect() as connection:
        tables = connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").scalars()
        return {name: list(connection.exec_driver_sql(f'SELECT * FROM "{name}" ORDER BY 1').tuples()) for name in tables}


def test_comparison_preserves_rows_and_compares_reviewed_to_original(saved):
    client, db, checklist, cid, _ = saved
    original = client.get("/api/evaluations/right").json()
    judgment = deepcopy(original["effective"]["results"]["contact"])
    judgment.update(value=False, explanation="Reviewed synthetic contact failure")
    appeal = client.post("/api/evaluations/right/appeals", json={"criterion_id": "contact", "comment": "TEST review"}).json()["id"]
    response = client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace", "rationale": "TEST reviewer",
        "judgment": judgment, "expected_updated_at": original["updated_at"]})
    assert response.status_code == 201, response.text
    before = db_rows(db)
    response = client.get("/api/evaluations/compare", params={"left_id": "right", "right_id": "right", "left_basis": "original"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source"]["id"] == cid and "audio_url" not in data["source"]
    assert data["total_comparable"] and data["total_difference"] == "-10.00"
    contact = next(r for r in data["criteria"] if r["criterion_id"] == "contact")
    assert contact["left"]["judgment"]["value"] is True
    assert contact["right"]["judgment"]["value"] is False
    assert set(contact["changes"]) == {"answer", "explanation", "points"}
    assert contact["points_difference"] == "-10"
    assert data["right"]["review_count"] == 1
    assert data["left"]["metadata"]["model"] == "SAVED_TEST_MODEL"
    assert client.get("/api/evaluations/right").json()["original"] == original["original"]
    assert db_rows(db) == before


def test_comparison_rejects_other_revisions_and_invalid_requests(saved):
    client, db, _, _, _ = saved
    source = synthetic_payload()
    source["data"]["records"][0]["transcript"][0]["text"] = "Changed revision"
    other = client.post("/api/import/json", json=source).json()["conversation_ids"][0]
    with db.transaction() as session:
        session.get(Evaluation, "right").conversation_id = other
    before = db_rows(db)
    assert client.get("/api/evaluations/compare?left_id=left&right_id=right").status_code == 422
    assert client.get("/api/evaluations/compare?left_id=left&right_id=absent").status_code == 404
    assert client.get("/api/evaluations/compare?left_id=left&right_id=left&left_basis=bad").status_code == 422
    assert db_rows(db) == before


def test_comparison_reports_changed_added_removed_rules_without_total_delta(saved):
    client, _, checklist, _, add = saved
    draft = checklist.model_dump(mode="json")
    draft["criteria"][0]["weight"] = "11"
    draft["criteria"][-1]["id"] = "new_flag"
    changed = Checklist.model_validate(draft)
    add("changed", changed)
    data = client.get("/api/evaluations/compare?left_id=left&right_id=changed").json()
    assert not data["total_comparable"] and data["total_difference"] is None
    rows = {r["criterion_id"]: r for r in data["criteria"]}
    assert rows["contact"]["answer_comparable"] and rows["contact"]["points_difference"] is None
    assert rows["contact"]["configuration_changes"] == ["weight"]
    assert rows["new_flag"]["change"] == "added"
    assert rows[checklist.criteria[-1].id]["change"] == "removed"
    # A scale's meaning changing also makes its answers incomparable.
    scale = next(c for c in draft["criteria"] if c["answer_type"] == "scale")
    scale["scale"][-1]["description"] = "Different rule"
    add("scale", Checklist.model_validate(draft))
    rows = client.get("/api/evaluations/compare?left_id=left&right_id=scale").json()["criteria"]
    assert not next(r for r in rows if r["criterion_id"] == scale["id"])["answer_comparable"]


def test_comparison_retains_nulls_flags_and_failed_run(saved):
    client, db, checklist, _, add = saved
    unresolved = full_assessment(checklist)
    unresolved.results["contact"].disposition = "needs_review"
    unresolved.results["contact"].value = None
    unresolved.results["contact"].review_reason = "Missing source basis"
    add("unresolved", assessment=unresolved); add("failed", state="failed")
    before = db_rows(db)
    data = client.get("/api/evaluations/compare?left_id=left&right_id=unresolved").json()
    assert not data["total_comparable"] and data["right"]["score"]["total"] is None
    flag = next(r for r in data["criteria"] if r["left"]["criterion"]["answer_type"] == "flag")
    assert flag["points_difference"] is None
    data = client.get("/api/evaluations/compare?left_id=left&right_id=failed").json()
    assert data["right"]["state"] == "failed" and data["right"]["score"] is None
    assert all(r["right"]["judgment"] is None for r in data["criteria"])
    assert db_rows(db) == before


def test_comparison_requires_known_matching_scoring_versions(saved):
    client, db, _, _, _ = saved
    for version in ("OTHER_SCORING", None):
        with db.transaction() as session:
            run = session.get(Evaluation, "right")
            calculated = deepcopy(run.effective_score)
            calculated["scoring_version"] = version
            run.effective_score = calculated
            if version is None:
                left = session.get(Evaluation, "left")
                calculated = deepcopy(left.effective_score); calculated.pop("scoring_version")
                left.effective_score = calculated
        response = client.get("/api/evaluations/compare?left_id=left&right_id=right").json()
        assert response["total_difference"] is None
        assert all(r["points_difference"] is None for r in response["criteria"])


def test_saved_report_snapshot_does_not_mix_a_concurrent_review(saved):
    client, db, _, _, _ = saved
    original = client.get("/api/evaluations/right").json()
    with db.read_snapshot() as session:
        assert evaluation_snapshot(session, "right")["reviews"] == []
        appeal = client.post("/api/evaluations/right/appeals", json={"criterion_id": "contact", "comment": "Concurrent TEST"}).json()["id"]
        replacement = deepcopy(original["effective"]["results"]["contact"]); replacement["value"] = False
        assert client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace", "judgment": replacement,
            "rationale": "Concurrent synthetic review", "expected_updated_at": original["updated_at"]}).status_code == 201
        session.expire_all()
        consistent = evaluation_snapshot(session, "right")
        assert consistent["reviews"] == [] and consistent["effective_score"] == original["effective_score"]
    updated = client.get("/api/evaluations/right").json()
    assert len(updated["reviews"]) == 1 and updated["effective_score"]["total"] == "90.00"


@pytest.mark.parametrize("format", ["json", "csv"])
def test_exports_preserve_saved_types_history_and_rows(saved, format):
    client, db, checklist, cid, add = saved
    assessment = full_assessment(checklist)
    na = next(c for c in checklist.criteria if c.na_allowed)
    assessment.results[na.id].disposition = "not_applicable"
    assessment.results[na.id].value = None
    assessment.results[na.id].na_reason = "SYNTHETIC condition met"
    assessment.results["contact"].explanation = '=HYPERLINK("bad"); Қазақша, Русский\nUnicode'
    add("exported", assessment=assessment)
    original = client.get("/api/evaluations/exported").json()
    replacement = deepcopy(original["effective"]["results"]["contact"])
    replacement.update(disposition="needs_review", value=None, review_reason="SYNTHETIC missing basis")
    appeal = client.post("/api/evaluations/exported/appeals", json={"criterion_id": "contact", "comment": "+TEST appeal"}).json()["id"]
    assert client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace", "rationale": "@TEST review", "judgment": replacement,
        "expected_updated_at": original["updated_at"]}).status_code == 201
    expected = client.get("/api/evaluations/exported").json()
    before = db_rows(db)
    response = client.get(f"/api/evaluations/exported/export?format={format}")
    assert response.status_code == 200, response.text
    assert 'attachment; filename="cqa-exported.' + format in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
    if format == "json":
        packet = response.json(); exported = packet["evaluation"]
        assert packet["source"]["id"] == cid
        assert "source_excerpts" not in packet and "audio_url" not in packet["source"]
        for key in ("original", "effective", "original_score", "effective_score", "checklist", "appeals", "reviews", "usage"):
            assert exported[key] == expected[key]
        assert exported["effective_score"]["total"] is None
        assert exported["original"]["results"][na.id]["value"] is None
    else:
        rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
        assert {r["record_type"] for r in rows} == {"evaluation", "score", "criterion", "appeal", "review"}
        contact = next(r for r in rows if r["record_type"] == "criterion" and r["basis"] == "original" and r["criterion_id"] == "contact")
        assert contact["explanation"].startswith("'=")
        assert json.loads(contact["data_json"])["judgment"] == expected["original"]["results"]["contact"]
        effective = next(r for r in rows if r["record_type"] == "criterion" and r["basis"] == "effective" and r["criterion_id"] == "contact")
        assert effective["value_json"] == "null"
        assert next(r for r in rows if r["record_type"] == "score" and r["basis"] == "effective")["total"] == ""
        assert json.loads(next(r for r in rows if r["record_type"] == "review")["data_json"])["resulting_score"] == expected["reviews"][0]["resulting_score"]
        assert "Қазақша" in response.content.decode("utf-8-sig")
    assert db_rows(db) == before


@pytest.mark.parametrize("format", ["json", "csv"])
def test_exports_excerpts_are_opt_in_and_secrets_are_redacted(saved, format):
    client, db, _, cid, _ = saved
    from backend.app.db import Conversation
    with db.transaction() as session:
        source = session.get(Conversation, cid)
        snapshot = deepcopy(source.snapshot)
        snapshot["audio_url"] = "https://example.invalid/recording?signature=PRIVATE_TEST"
        snapshot["transcript"][0]["text"] = "Қазақша original source " + snapshot["audio_url"]
        source.snapshot = snapshot
        run = session.get(Evaluation, "left")
        original = deepcopy(run.original)
        original["results"]["contact"]["explanation"] = "sk-EXPORT-TEST https://example.invalid/private-organizer https://other.invalid/?token=PRIVATE_TEST"
        run.original = original
        run.meta = {**run.meta, "api_key": "PRIVATE_TEST", "generation": {"temperature": 0, "authorization": "PRIVATE_TEST"}}
    before = db_rows(db)
    response = client.get(f"/api/evaluations/left/export?format={format}&include_excerpts=true")
    assert response.status_code == 200
    assert "PRIVATE_TEST" not in response.text and "sk-EXPORT-TEST" not in response.text and "private-organizer" not in response.text
    assert "Қазақша original source" in response.content.decode("utf-8-sig")
    if format == "json":
        assert response.json()["source_excerpts"][0]["messages"][0]["id"] == "m0001"
        assert response.json()["export_policy"]["redacted_string_occurrences"] > 0
    else:
        assert any(r["record_type"] == "excerpt" for r in csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert db_rows(db) == before


def test_failed_export_and_parameter_errors(saved):
    client, db, _, _, add = saved
    add("failed_export", state="failed")
    before = db_rows(db)
    data = client.get("/api/evaluations/failed_export/export").json()
    assert data["evaluation"]["original"] is None and data["evaluation"]["effective_score"] is None
    assert client.get("/api/evaluations/absent/export").status_code == 404
    assert client.get("/api/evaluations/left/export?format=pdf").status_code == 422
    assert client.get("/api/evaluations/left/export?include_excerpts=bad").status_code == 422
    assert db_rows(db) == before


@pytest.mark.parametrize("text,query", [("ҚАЗАҚША ӘҢГІМЕ", "қазақша"), ("ПривеТ", "ПРИВЕТ"), ("Hello [.*]", "[.*]"),
                                     ("И\u0306 test", "й"), ("Straße İ", "STRASSE")])
def test_literal_unicode_search_returns_exact_message_revision(saved, text, query):
    client, db, _, _, _ = saved
    payload = synthetic_payload(source_id="SEARCH_TEST")
    payload["data"]["records"][0]["transcript"][1]["text"] = text
    cid = client.post("/api/import/json", json=payload).json()["conversation_ids"][0]
    before = db_rows(db)
    response = client.get("/api/conversations", params={"q": query, "speaker": "operator", "checklist_id": 1})
    assert response.status_code == 200, response.text
    assert [r["id"] for r in response.json()] == [cid]
    match = response.json()[0]["search_matches"][0]
    assert {k: v for k, v in match.items() if k != "highlights"} == {"id": "m0002", "speaker": "operator", "timestamp": "00:00", "snippet": text}
    assert match["highlights"] and all(0 <= span["start"] < span["end"] <= len(text) for span in match["highlights"])
    assert client.get("/api/conversations", params={"q": query, "speaker": "client"}).json() == []
    assert db_rows(db) == before


def test_search_latest_revision_namespace_roles_and_limits(saved):
    client, db, _, _, _ = saved
    source = synthetic_payload(source_id="SEARCH_REVISIONS")
    record = source["data"]["records"][0]
    record["transcript"] = [{"timestamp": "00:00", "speaker": role, "text": "UNIQUE_SEARCH_PHRASE " + str(i)}
                            for i, role in enumerate(["operator"] * 7 + ["bot", "system", "client"])]
    old = client.post("/api/import/json", json=source).json()["conversation_ids"][0]
    source["data"]["dataset_group_id"] = "SECOND_TEST_GROUP"
    other = client.post("/api/import/json", json=source).json()["conversation_ids"][0]
    source["data"]["dataset_group_id"] = "SYNTHETIC_TEST_ONLY"
    record["transcript"][0]["text"] = "LATEST_ONLY_SOURCE"
    record["transcript"] = record["transcript"][:1]
    latest = client.post("/api/import/json", json=source).json()["conversation_ids"][0]
    before = db_rows(db)
    rows = client.get("/api/conversations?q=UNIQUE_SEARCH_PHRASE&speaker=operator").json()
    assert [r["id"] for r in rows] == [other]
    assert rows[0]["search_total_matches"] == 7 and len(rows[0]["search_matches"]) == 5
    assert {r["id"] for r in client.get("/api/conversations?q=UNIQUE_SEARCH_PHRASE&latest_only=false").json()} == {old, other}
    for role, mid in (("bot", "m0008"), ("system", "m0009"), ("client", "m0010")):
        rows = client.get("/api/conversations", params={"q": "UNIQUE_SEARCH_PHRASE", "speaker": role}).json()
        assert rows[0]["search_matches"][0]["id"] == mid
    assert client.get("/api/conversations?q=LATEST_ONLY_SOURCE").json()[0]["id"] == latest
    assert client.get("/api/conversations", params={"q": "x" * 201}).status_code == 422
    assert client.get("/api/conversations?speaker=admin").status_code == 422
    assert len(client.get("/api/conversations?q=%20%20").json()) == 3
    assert db_rows(db) == before
