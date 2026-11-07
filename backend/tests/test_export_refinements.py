"""Flat and selected-run exports use saved snapshots with Provider.request forbidden."""
from copy import deepcopy
import csv
import io
import json

import pytest

from backend.app.db import Evaluation
from backend.app.services.exports import batch_csv_report, csv_report, export_batch, export_packet, json_report, simple_csv_report
from backend.app.services.saved_results import SavedResultNotFound
from backend.tests.conftest import full_assessment
from backend.tests.test_saved_inspection import saved, db_rows
from backend.tests.test_workflow import synthetic_payload


def csv_rows(body):
    return list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))


def test_standalone_manifest_uses_exact_sanitized_saved_identity(saved):
    client, db, _, cid, _ = saved
    from backend.app.db import Conversation
    with db.transaction() as session:
        source = session.get(Conversation, cid)
        source.source_id = '=FORMULA_SOURCE sk-EXPORT-TEST https://example.invalid/private-organizer'
        run = session.get(Evaluation, "left")
        run.meta = {**run.meta, "api_key": "PRIVATE_MANIFEST_TOKEN"}
    before = db_rows(db)
    with db.read_snapshot() as session:
        packet = export_packet(session, "left", client.app.state.settings, True)
    manifest = packet["manifest"]
    assert manifest["schema_version"] == 1 and manifest["generated_at"] and manifest["selected_run_count"] == 1
    assert manifest["answer_sets"] == ["original", "effective"] and manifest["source_excerpts_included"] is True
    assert manifest["runs"] == [{"evaluation_id": "left", "updated_at": packet["evaluation"]["updated_at"],
        "conversation_id": cid, "source_id": packet["source"]["source_id"], "group_id": packet["source"]["group_id"],
        "revision": packet["source"]["revision"], "source_hash": packet["source"]["content_hash"],
        "checklist_id": packet["evaluation"]["checklist"]["id"], "checklist_hash": packet["evaluation"]["checklist"]["content_hash"]}]
    assert "sk-EXPORT-TEST" not in json.dumps(manifest) and "private-organizer" not in json.dumps(manifest)
    assert "PRIVATE_MANIFEST_TOKEN" not in json.dumps(manifest) and "audio_url" not in manifest
    archive = csv_rows(csv_report(packet))
    context = json.loads(next(r["data_json"] for r in archive if r["record_type"] == "evaluation"))
    assert context["manifest"] == manifest
    assert next(r["source_id"] for r in archive if r["record_type"] == "evaluation").startswith("'=")
    assert csv_rows(simple_csv_report(packet))[0]["source_id"].startswith("'=")
    with db.read_snapshot() as session:
        batch = export_batch(session, ["left"], client.app.state.settings)
    row = csv_rows(batch_csv_report(batch))[0]
    assert row["record_type"] == "batch_manifest" and row["data_json"].startswith("{")
    assert json.loads(row["data_json"])["runs"][0]["source_id"] == batch["reports"][0]["source"]["source_id"]
    assert db_rows(db) == before


def test_simple_csv_retains_typed_answers_null_totals_flags_and_unicode(saved):
    client, db, checklist, _, add = saved
    assessment = full_assessment(checklist)
    na = next(c for c in checklist.criteria if c.na_allowed)
    assessment.results[na.id].disposition = "not_applicable"
    assessment.results[na.id].value = None
    assessment.results[na.id].na_reason = "SYNTHETIC N/A condition"
    assessment.results["contact"].disposition = "needs_review"
    assessment.results["contact"].value = None
    assessment.results["contact"].review_reason = "SYNTHETIC missing basis"
    assessment.results["contact"].explanation = '=HYPERLINK("bad"); Қазақша, Русский\nNew line'
    add("flat", assessment=assessment)
    before = db_rows(db)
    with db.read_snapshot() as session:
        packet = export_packet(session, "flat", client.app.state.settings)
    rows = csv_rows(simple_csv_report(packet))
    assert len(rows) == 2 * len(checklist.criteria)
    assert {r["basis"] for r in rows} == {"original", "effective"}
    contact = next(r for r in rows if r["basis"] == "effective" and r["criterion_id"] == "contact")
    assert contact["answer_label"] == "Needs review" and contact["value_json"] == "null"
    assert contact["total"] == "" and contact["total_availability"] == "unavailable" and contact["total_reason"] == "UNRESOLVED_CRITERIA"
    assert contact["explanation"].startswith("'=") and "Қазақша" in contact["explanation"]
    assert all(r["source_excerpts"] == "" and r["source_excerpts_included"] == "false" for r in rows)
    excluded = next(r for r in rows if r["criterion_id"] == na.id)
    assert excluded["answer_label"] == "N/A" and excluded["value_json"] == "null" and excluded["raw_points"] == ""
    flag = next(r for r in rows if r["answer_type"] == "flag")
    assert flag["answer_label"] == "No" and flag["value_json"] == "false" and flag["weight"] == "" and flag["raw_points"] == ""
    scale = next(r for r in rows if r["answer_type"] == "scale")
    assert isinstance(json.loads(scale["value_json"]), (int, float)) and not isinstance(json.loads(scale["value_json"]), bool)
    assert contact["evaluation_updated_at"] == packet["evaluation"]["updated_at"]
    assert contact["content_hash"] == packet["source"]["content_hash"] and contact["checklist_hash"] == packet["evaluation"]["checklist"]["content_hash"]
    assert db_rows(db) == before


def test_selected_batch_freezes_exact_order_and_dataset_namespace(saved):
    client, db, checklist, _, _ = saved
    payload = synthetic_payload(); payload["data"]["dataset_group_id"] = "OTHER_SYNTHETIC_GROUP"
    other = client.post("/api/import/json", json=payload).json()["conversation_ids"][0]
    with db.transaction() as session:
        session.get(Evaluation, "right").conversation_id = other
    before = db_rows(db)
    with db.read_snapshot() as session:
        packet = export_batch(session, ["right", "left"], client.app.state.settings)
    assert [r["evaluation"]["id"] for r in packet["reports"]] == ["right", "left"]
    assert [r["evaluation_id"] for r in packet["manifest"]["runs"]] == ["right", "left"]
    assert {r["group_id"] for r in packet["manifest"]["runs"]} == {"SYNTHETIC_TEST_ONLY", "OTHER_SYNTHETIC_GROUP"}
    assert len({r["source_id"] for r in packet["manifest"]["runs"]}) == 1
    assert packet["manifest"]["selected_run_count"] == 2 and packet["manifest"]["generated_at"]
    assert "build_id" not in packet["manifest"]
    assert json.loads(json_report(packet))["reports"][0]["evaluation"]["id"] == "right"
    archive = csv_rows(batch_csv_report(packet))
    assert archive[0]["record_type"] == "batch_manifest"
    assert json.loads(archive[0]["data_json"]) == packet["manifest"]
    assert [r["evaluation_id"] for r in archive if r["record_type"] == "evaluation"] == ["right", "left"]
    flat = csv_rows(simple_csv_report(packet))
    assert len(flat) == 4 * len(checklist.criteria)
    assert [r["evaluation_id"] for r in flat[:2 * len(checklist.criteria)]] == ["right"] * (2 * len(checklist.criteria))
    assert {r["selected_run_count"] for r in flat} == {"2"}
    assert {r["generated_at"] for r in flat} == {packet["manifest"]["generated_at"]}
    assert db_rows(db) == before


@pytest.mark.parametrize("ids", [[], ["left", "left"], [""], [" "], ["x" * 201], [None], [str(i) for i in range(101)]])
def test_selected_batch_invalid_selection_is_rejected_without_writes(saved, ids):
    client, db, _, _, _ = saved
    before = db_rows(db)
    with db.read_snapshot() as session, pytest.raises(ValueError):
        export_batch(session, ids, client.app.state.settings)
    assert db_rows(db) == before


def test_selected_batch_missing_run_is_all_or_nothing_and_accepts_maximum(saved):
    client, db, _, _, add = saved
    before = db_rows(db)
    with db.read_snapshot() as session, pytest.raises(SavedResultNotFound):
        export_batch(session, ["left", "absent"], client.app.state.settings)
    assert db_rows(db) == before
    ids = ["left", "right"] + [add(f"MAX_{i}") for i in range(98)]
    before = db_rows(db)
    with db.read_snapshot() as session:
        packet = export_batch(session, ids, client.app.state.settings)
    assert packet["manifest"]["selected_run_count"] == 100
    assert [r["evaluation"]["id"] for r in packet["reports"]] == ids
    assert db_rows(db) == before


@pytest.mark.parametrize("format", ["json", "csv", "simple_csv"])
def test_selected_batch_keeps_excerpts_explicit_and_redacts_every_format(saved, format):
    client, db, _, _, _ = saved
    with db.transaction() as session:
        row = session.get(Evaluation, "left"); original = deepcopy(row.original)
        original["results"]["contact"]["explanation"] = "sk-EXPORT-TEST https://example.invalid/private-organizer https://other.invalid/?token=PRIVATE_TOKEN"
        row.original = original
    before = db_rows(db)
    with db.read_snapshot() as session:
        excluded = export_batch(session, ["left"], client.app.state.settings)
        included = export_batch(session, ["left"], client.app.state.settings, True)
    assert "source_excerpts" not in excluded["reports"][0]
    assert included["reports"][0]["source_excerpts"]
    serializer = {"json": json_report, "csv": batch_csv_report, "simple_csv": simple_csv_report}[format]
    content = serializer(included).decode("utf-8-sig")
    assert "sk-EXPORT-TEST" not in content and "private-organizer" not in content and "PRIVATE_TOKEN" not in content
    assert "[REDACTED" in content and "SYNTHETIC TEST:" in content
    if format == "simple_csv":
        assert any(r["source_excerpts"] for r in csv_rows(serializer(included)))
        assert all(not r["source_excerpts"] for r in csv_rows(serializer(excluded)))
    assert db_rows(db) == before


def test_batch_read_snapshot_does_not_mix_a_concurrent_review(saved):
    client, db, _, _, _ = saved
    current = client.get("/api/evaluations/right").json()
    with db.read_snapshot() as session:
        old = export_batch(session, ["left", "right"], client.app.state.settings)
        appeal = client.post("/api/evaluations/right/appeals", json={"criterion_id": "contact", "comment": "Concurrent export TEST"}).json()["id"]
        replacement = deepcopy(current["effective"]["results"]["contact"]); replacement["value"] = False
        assert client.post(f"/api/appeals/{appeal}/decision", json={"action": "replace", "judgment": replacement,
            "rationale": "Concurrent synthetic review", "expected_updated_at": current["updated_at"]}).status_code == 201
        session.expire_all()
        consistent = export_batch(session, ["left", "right"], client.app.state.settings)
        assert [r["evaluation"] for r in consistent["reports"]] == [r["evaluation"] for r in old["reports"]]
        assert consistent["manifest"]["runs"] == old["manifest"]["runs"]
    assert client.get("/api/evaluations/right").json()["effective_score"]["total"] == "90.00"
