"""Read the coordinator's private copy in SQLite mode=ro, never initialize a DB."""
from contextlib import contextmanager
import hashlib
import json
from itertools import product
from pathlib import Path
import sqlite3

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from backend.app.api_cohorts import router
from backend.app.db import Conversation, Evaluation
from backend.app.services.cohort_comparison import SELECTOR_FIELDS
from backend.app.services.evaluator import Provider
from backend.app.services.saved_results import compare_saved


def fingerprint(path):
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        connection.execute("BEGIN")
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {"schema": hashlib.sha256(repr(connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()).encode()).hexdigest(),
                "tables": {name: hashlib.sha256(repr(connection.execute('SELECT * FROM "'+name+'" ORDER BY 1').fetchall()).encode()).hexdigest() for name in tables}}


def test_actual_saved_copy_matches_exact_pairs_and_preserves_all_rows_schema_and_index(monkeypatch):
    path = Path(__file__).resolve().parents[2] / "local_data/review.sqlite3"
    if not path.is_file(): pytest.skip("Coordinator-provided private saved-data copy is not present")
    attempts = []
    def forbidden(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Hosted provider requests forbidden")
    monkeypatch.setattr(Provider, "request", forbidden)
    before = fingerprint(path)
    engine = create_engine("sqlite://", creator=lambda: sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, check_same_thread=False))
    class ReadOnlyCopy:
        @contextmanager
        def read_snapshot(self):
            with Session(engine) as session:
                session.execute(text("BEGIN")); yield session
    db = ReadOnlyCopy()
    app = FastAPI(); app.state.db = db; app.include_router(router)
    checked_pairs = different_pairs = scenarios_checked = 0
    distinct_pairs = set()
    contract_samples = []
    pair_render_samples = []
    try:
        with TestClient(app) as client:
            options = client.get("/api/insights/cohorts/options").json()
            assert options["version"] == 1 and sum(dataset["saved_evaluation_count"] for dataset in options["datasets"]) == 249
            assert sum(dataset["source_revision_count"] for dataset in options["datasets"]) == 75
            for dataset in options["datasets"]:
                versions = dataset["checklists"]
                if not versions: continue
                scenarios = [({"checklist_id": versions[0]["checklist_id"]}, {"checklist_id": version["checklist_id"]}) for version in versions]
                for version in versions:
                    for field in SELECTOR_FIELDS:
                        values = version["fields"][field]["values"]
                        if len(values) > 1:
                            scenarios.append(({"checklist_id": version["checklist_id"], field: values[0]["value"]},
                                              {"checklist_id": version["checklist_id"], field: values[-1]["value"]}))
                for (left_selector, right_selector), basis in product(scenarios, ("original", "effective")):
                    body = {"dataset_group_id": dataset["dataset_group_id"], "left": left_selector, "right": right_selector, "basis": basis}
                    response = client.post("/api/insights/cohorts/compare", json=body)
                    assert response.status_code == 200
                    result = response.json()
                    contract_samples.append({"request": {**body, "limit": 200}, "response": result})
                    scenarios_checked += 1
                    assert result["coverage"]["source_revisions"] == dataset["source_revision_count"]
                    with db.read_snapshot() as session:
                        for pair in result["pairs"]:
                            source = session.get(Conversation, pair["source"]["conversation_id"])
                            assert source.group_id == dataset["dataset_group_id"] and source.content_hash == pair["source"]["content_hash"]
                            for label, selector in (("left", left_selector), ("right", right_selector)):
                                query = select(Evaluation).where(Evaluation.conversation_id == source.id, Evaluation.checklist_id == selector["checklist_id"])
                                for field in SELECTOR_FIELDS:
                                    if field in selector: query = query.where(Evaluation.meta[field].as_string() == selector[field])
                                expected = session.scalar(query.order_by(Evaluation.created_at.desc(), Evaluation.id.desc()).limit(1))
                                assert (pair[label]["evaluation_id"] if pair[label] else None) == (expected.id if expected else None)
                                if expected:
                                    selected_score = getattr(expected, basis + "_score") or {}
                                    expected_completeness = selected_score.get("completeness")
                                    assert pair[label]["completeness"] == (expected_completeness if expected_completeness in {"complete", "needs_review", "incomplete"} else "unknown")
                            if not pair["left"] or not pair["right"]: continue
                            exact = compare_saved(session, pair["left"]["evaluation_id"], pair["right"]["evaluation_id"], basis, basis)
                            # Only the preview's rendered fields: no explanations, transcript,
                            # raw metadata/errors or recording URLs in this private bridge sample.
                            preview = {"total_comparable": exact["total_comparable"], "total_difference": exact["total_difference"], "criteria": []}
                            for row in exact["criteria"]:
                                cell = {key: row[key] for key in ("criterion_id", "changes", "points_difference")}
                                for side in ("left", "right"):
                                    definition, judgment = row[side]["criterion"], row[side]["judgment"]
                                    cell[side] = {"criterion": {key: definition[key] for key in ("id", "name", "answer_type")} if definition else None,
                                        "judgment": {key: judgment[key] for key in ("disposition", "value", "evidence")} if judgment else None}
                                preview["criteria"].append(cell)
                            pair_render_samples.append(preview)
                            checked_pairs += 1
                            different_pairs += int(pair["left"]["evaluation_id"] != pair["right"]["evaluation_id"])
                            distinct_pairs.add((pair["left"]["evaluation_id"], pair["right"]["evaluation_id"]))
                            assert exact["source"]["id"] == source.id
                            if pair["total_comparable"]:
                                assert pair["total_difference"] == exact["total_difference"] and exact["total_comparable"]
                            original_criteria = {row["criterion_id"]: row for row in exact["criteria"]}
                            for criterion in pair["criteria"]:
                                if criterion["points_difference"] is not None:
                                    assert criterion["points_difference"] == original_criteria[criterion["criterion_id"]]["points_difference"]
            assert checked_pairs > 0 and different_pairs > 0
    finally:
        engine.dispose()
    assert fingerprint(path) == before
    assert not attempts
    (path.parent / "cohort_contract_samples.json").write_text(json.dumps(contract_samples), encoding="utf-8")
    (path.parent / "cohort_pair_render_samples.json").write_text(json.dumps(pair_render_samples), encoding="utf-8")
    (path.parent / "cohort_saved_checks.json").write_text(json.dumps({"datasets": len(options["datasets"]), "source_revisions": 75,
        "saved_evaluations": 249, "scenarios_checked": scenarios_checked, "exact_pair_checks": checked_pairs,
        "different_run_pair_checks": different_pairs, "distinct_run_pairs": len(distinct_pairs), "tables_preserved": len(before["tables"]), "schema_unchanged": True,
        "sqlite_mode": "ro", "provider_attempts": len(attempts)}, indent=2), encoding="utf-8")
