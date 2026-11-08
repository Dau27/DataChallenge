"""Cohort-only synthetic coverage; fixtures are not model judgments."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from backend.app.api_cohorts import router
from backend.app.db import ChecklistVersion, Conversation, Database, Evaluation
from backend.app.domain import Checklist, content_hash
from backend.app.services.cohort_comparison import CohortCompareRequest, cohort_options, compare_cohorts
from backend.app.services.evaluator import Provider
from backend.app.services.scoring import score
from backend.tests.conftest import full_assessment
from backend.tests.test_saved_inspection import db_rows


@pytest.fixture
def cohort(tmp_path, checklist, monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError("Cohorts cannot invoke a provider")
    monkeypatch.setattr(Provider, "request", forbidden)
    db = Database(tmp_path / "cohort.sqlite3")
    with db.transaction() as session:
        session.add(ChecklistVersion(id=1, content_hash=content_hash(checklist), snapshot=checklist.model_dump(mode="json")))

    def source(cid="source", group="DEV", source_id=None, revision=1):
        snapshot = {"language": "KZ", "channel": "agent chat", "audio_url": "https://example.invalid/private-recording",
            "transcript": [{"id": "m0001", "speaker": "operator", "timestamp": "00:00", "text": f"SYNTHETIC COHORT TEST ONLY {cid} revision {revision} — Ә Ғ Қ Ң Ө Ұ Ү Һ І"}]}
        with db.transaction() as session:
            session.add(Conversation(id=cid, group_id=group, source_id=source_id or cid, revision=revision,
                content_hash=content_hash(snapshot), snapshot=snapshot))
        return cid

    def version(rubric, version_id=2):
        with db.transaction() as session:
            session.add(ChecklistVersion(id=version_id, content_hash=content_hash(rubric), snapshot=rubric.model_dump(mode="json")))
        return version_id

    def add(run_id, cid="source", model="A", state="succeeded", rubric=checklist, version_id=1,
            assessment=None, effective=None, meta=None, created="2026-11-08T00:00:00.000200+00:00", cached_from=None):
        original = assessment or full_assessment(rubric)
        final = effective or original
        calculated = score(rubric, original, ["m0001"]) if state == "succeeded" else None
        final_score = score(rubric, final, ["m0001"]) if state == "succeeded" else None
        metadata = {"model": model, "provider": "SYNTHETIC", "mode": "TEST/MOCK", "prompt_version": "p1", "schema_version": "s1",
            "evidence_validation_version": "e1", "scoring_version": calculated["scoring_version"] if calculated else "SYNTHETIC",
            "prompt_hash": "a"*64, "schema_hash": "b"*64, "checklist_hash": content_hash(rubric), "generation": {"temperature": 0}}
        if meta is not None: metadata = meta
        with db.transaction() as session:
            session.add(Evaluation(id=run_id, conversation_id=cid, checklist_id=version_id, cache_key="SYNTHETIC_COHORT_TEST_ONLY",
                state=state, completeness=final_score["completeness"] if final_score else "incomplete", cached_from=cached_from,
                original=original.model_dump(mode="json") if calculated else None, original_score=calculated,
                effective=final.model_dump(mode="json") if final_score else None, effective_score=final_score,
                meta=metadata, attempts=[], error="NEVER EXPOSE RAW SAVED ERROR https://example.invalid/token=PRIVATE" if state != "succeeded" else None,
                created_at=created, updated_at=created))
        return run_id

    def compare(left=None, right=None, **kwargs):
        body = {"dataset_group_id": "DEV", "left": left or {"checklist_id": 1, "model": "A"},
                "right": right or {"checklist_id": 1, "model": "B"}, **kwargs}
        with db.read_snapshot() as session: return compare_cohorts(session, body)

    yield SimpleNamespace(db=db, source=source, version=version, add=add, compare=compare, checklist=checklist)
    db.engine.dispose()


def test_exact_revisions_and_dataset_isolation_account_for_missing_both_sides(cohort):
    cohort.source("old", source_id="SAME", revision=1); cohort.source("new", source_id="SAME", revision=2)
    cohort.source("none"); cohort.source("other", group="OTHER", source_id="SAME")
    cohort.add("a", "old", "A"); cohort.add("b", "new", "B"); cohort.add("foreign", "other", "B")
    before = db_rows(cohort.db)
    result = cohort.compare()
    assert result["coverage"]["source_revisions"] == 3
    assert result["coverage"]["missing_left"] == result["coverage"]["missing_right"] == result["coverage"]["missing_both"] == 1
    assert result["coverage"]["paired"] == 0
    assert {pair["source"]["dataset_group_id"] for pair in result["pairs"]} == {"DEV"}
    assert {pair["source"]["conversation_id"] for pair in result["pairs"]} == {"old", "new", "none"}
    assert "foreign" not in str(result) and db_rows(cohort.db) == before


def test_latest_matching_key_retains_a_failed_run_instead_of_successful_fallback(cohort):
    cohort.source()
    cohort.add("A_old", model="A", created="2026-11-08T00:00:00.000100+00:00")
    cohort.add("A_a", model="A"); cohort.add("A_z", model="A", state="failed"); cohort.add("B", model="B")
    result = cohort.compare(); pair = result["pairs"][0]
    assert pair["left"]["evaluation_id"] == "A_z" and pair["right"]["evaluation_id"] == "B"
    assert pair["status"] == "failed" and not pair["total_comparable"]
    assert "EXECUTION_FAILED_OR_INTERRUPTED" in pair["reasons"]
    assert result["total_difference"] == {"count": 0, "sum": None, "mean": None}
    assert "NEVER EXPOSE" not in str(result) and "example.invalid" not in str(result)


def test_absent_null_and_exact_filters_remain_distinct_without_current_defaults(cohort):
    cohort.source(); cohort.add("A", meta={}); cohort.add("B", model="B")
    any_value = cohort.compare(left={"checklist_id": 1})
    unknown = cohort.compare(left={"checklist_id": 1, "model": None, "prompt_version": None})
    exact = cohort.compare(left={"checklist_id": 1, "model": "A"})
    assert any_value["left"] == {"checklist_id": 1}
    assert unknown["left"]["model"] is None
    assert any_value["pairs"][0]["left"]["evaluation_id"] == "B"
    assert unknown["pairs"][0]["left"]["evaluation_id"] == "A"
    assert exact["pairs"][0]["left"] is None
    assert unknown["pairs"][0]["left"]["provenance"]["model"] is None


def test_answer_disposition_na_and_flag_transitions_keep_their_own_point_denominators(cohort):
    cohort.source()
    a = full_assessment(cohort.checklist); b = full_assessment(cohort.checklist)
    a.results["needs"].disposition = "not_applicable"; a.results["needs"].value = None
    a.results["needs"].na_reason = "SYNTHETIC request already clear"
    a.results["consultation"].value = 0
    b.results["critical_errors"].value = True
    cohort.add("A", assessment=a); cohort.add("B", model="B", assessment=b)
    result = cohort.compare(); rows = {row["criterion_id"]: row for row in result["criteria"]}
    assert rows["needs"]["disposition_changed_count"] == 1 and rows["needs"]["points_difference"]["count"] == 0
    assert rows["needs"]["transitions"][0]["left"]["disposition"] == "not_applicable"
    assert Decimal(rows["consultation"]["points_difference"]["sum"]) == Decimal("20")
    assert rows["critical_errors"]["answer_changed_count"] == 1 and rows["critical_errors"]["points_difference"]["count"] == 0
    assert "accuracy" in result["notice"] and "independent" in result["notice"]


def test_unresolved_totals_stay_null_and_other_answer_transitions_remain_inspectable(cohort):
    cohort.source()
    a = full_assessment(cohort.checklist); a.results["critical_errors"].disposition = "needs_review"
    a.results["critical_errors"].value = None; a.results["critical_errors"].review_reason = "SYNTHETIC missing policy basis"
    cohort.add("A", assessment=a); cohort.add("B", model="B")
    result = cohort.compare(); pair = result["pairs"][0]
    assert pair["status"] == "unresolved" and pair["left"]["total"] is None
    assert pair["total_difference"] is None and not pair["total_comparable"]
    critical = next(row for row in result["criteria"] if row["criterion_id"] == "critical_errors")
    assert critical["transitions"][0]["left"]["disposition"] == "needs_review"
    assert critical["transitions"][0]["left"]["value"] is None
    assert critical["points_difference"]["count"] == 0
    assert all(row["denominator"] == 1 for row in result["criteria"])


def test_original_effective_basis_is_exact_and_same_run_or_cache_is_disclosed(cohort):
    cohort.source()
    reviewed = full_assessment(cohort.checklist); reviewed.results["contact"].value = False
    cohort.add("A", effective=reviewed); cohort.add("B", model="B", cached_from="A")
    original = cohort.compare(basis="original"); final = cohort.compare(basis="effective")
    assert original["pairs"][0]["total_difference"] == "0.00"
    assert final["pairs"][0]["total_difference"] == "10.00"
    cached = final["pairs"][0]["right"]
    assert cached["cached"] and cached["cached_from"] == "A" and cached["cache_origin_present"] and cached["cache_source_matches"]
    assert final["coverage"]["cached_pairs"] == 1
    same = cohort.compare(right={"checklist_id": 1, "model": "A"})
    assert same["coverage"]["same_run_pairs"] == 1


def test_definition_weight_and_scoring_mismatches_do_not_mix_numeric_aggregates(cohort):
    cohort.source()
    modified = cohort.checklist.model_copy(deep=True)
    modified.criteria[0].description += " SYNTHETIC changed definition"
    modified.criteria[1].weight = Decimal("12")
    cohort.version(modified)
    cohort.add("A"); cohort.add("B", model="B", rubric=modified, version_id=2)
    result = cohort.compare(right={"checklist_id": 2})
    assert result["coverage"]["incompatible"] == 1 and result["total_difference"]["count"] == 0
    rows = {row["criterion_id"]: row for row in result["criteria"]}
    assert rows["contact"]["definition_changed_count"] == 1 and rows["contact"]["answer_comparable_count"] == 0
    assert rows["needs"]["answer_comparable_count"] == 1 and rows["needs"]["points_difference"]["count"] == 0
    assert rows["empathy"]["points_difference"]["count"] == 1
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "B"); calculated = deepcopy(run.effective_score); calculated.pop("scoring_version"); run.effective_score = calculated
    unknown_scoring = cohort.compare(right={"checklist_id": 2})
    assert all(row["points_difference"]["count"] == 0 for row in unknown_scoring["criteria"])


def test_detail_only_and_equivalent_scale_numbers_do_not_become_answer_changes(cohort):
    cohort.source()
    different = full_assessment(cohort.checklist)
    different.results["consultation"].value = 20
    different.results["contact"].explanation = "SYNTHETIC explanation changed, same answer"
    cohort.add("A"); cohort.add("B", model="B", assessment=different)
    result = cohort.compare(); rows = {row["criterion_id"]: row for row in result["criteria"]}
    assert rows["consultation"]["answer_changed_count"] == 0
    assert rows["contact"]["details_only_count"] == 1 and rows["contact"]["answer_changed_count"] == 0


def test_missing_reason_preserves_failure_even_when_the_other_side_is_missing(cohort):
    cohort.source(); cohort.add("A", state="failed")
    pair = cohort.compare()["pairs"][0]
    assert pair["status"] == "missing_right"
    assert set(pair["reasons"]) >= {"CANDIDATE_RUN_MISSING", "EXECUTION_FAILED_OR_INTERRUPTED", "SAVED_ANSWER_SET_UNAVAILABLE"}


@pytest.mark.parametrize("state", ["queued", "running", "interrupted"])
def test_non_success_states_never_contribute_zero_or_fabricated_answers(cohort, state):
    cohort.source(); cohort.add("A", state=state); cohort.add("B", model="B")
    result = cohort.compare()
    assert result["pairs"][0]["status"] == ("failed" if state == "interrupted" else "pending")
    assert result["total_difference"]["count"] == 0
    assert all(row["unavailable_count"] == 1 for row in result["criteria"])


def test_options_and_results_withhold_arbitrary_metadata_errors_urls_and_credentials(cohort):
    cohort.source()
    meta = {"model": "sk-TEST-ONLY", "prompt_version": "https://example.invalid/signed?token=PRIVATE",
            "schema_version": 123, "evidence_validation_version": "ok", "api_key": "PRIVATE-KEY", "nested": {"private": "NO"}}
    cohort.add("A", meta=meta); cohort.add("B", model="B")
    with cohort.db.read_snapshot() as session: options = cohort_options(session)
    profile = options["datasets"][0]["checklists"][0]
    assert profile["fields"]["model"]["unknown_count"] == 1 and profile["fields"]["schema_version"]["unknown_count"] == 1
    result = cohort.compare(left={"checklist_id": 1, "model": None})
    rendered = str([options, result])
    for private in ("sk-TEST-ONLY", "example.invalid", "PRIVATE-KEY", "signed?", "private-recording", "nested", "NEVER EXPOSE RAW"):
        assert private not in rendered
    assert result["pairs"][0]["left"]["provenance"]["model"] is None


@pytest.mark.parametrize("change", [
    {"limit": 201}, {"limit": 0}, {"limit": True}, {"limit": "10"}, {"basis": "draft"}, {"dataset_group_id": " "},
    {"dataset_group_id": "D"*151}, {"sql": "SELECT secret"}, {"left": {"checklist_id": True}},
    {"left": {"checklist_id": "1"}}, {"left": {"checklist_id": 1, "model": 3}},
    {"left": {"checklist_id": 1, "model": "M"*151}}, {"left": {"checklist_id": 1, "provider": "NO"}},
])
def test_request_contract_is_strict_and_bounded(change):
    body = {"dataset_group_id": "DEV", "left": {"checklist_id": 1}, "right": {"checklist_id": 1}, **change}
    with pytest.raises(ValidationError): CohortCompareRequest.model_validate(body)


def test_oversized_dataset_is_refused_without_silent_truncation(cohort):
    for i in range(3): cohort.source(f"s{i}")
    with pytest.raises(HTTPException) as error: cohort.compare(limit=2)
    assert error.value.status_code == 422 and "3 exact source revisions" in error.value.detail and "No partial" in error.value.detail


def test_read_only_routes_validate_and_retain_single_snapshot_results(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    app = FastAPI(); app.state.db = cohort.db; app.include_router(router)
    before = db_rows(cohort.db)
    with TestClient(app) as client:
        options = client.get("/api/insights/cohorts/options")
        assert options.status_code == 200 and options.headers["cache-control"] == "no-store"
        body = {"dataset_group_id": "DEV", "left": {"checklist_id": 1, "model": "A"}, "right": {"checklist_id": 1, "model": "B"}}
        response = client.post("/api/insights/cohorts/compare", json=body)
        assert response.status_code == 200 and response.json()["coverage"]["matched"] == 1
        assert response.headers["cache-control"] == "no-store"
        assert client.post("/api/insights/cohorts/compare", json={**body, "limit": 201}).status_code == 422
        assert client.post("/api/insights/cohorts/compare", json={**body, "dataset_group_id": "ABSENT"}).status_code == 404
        assert client.post("/api/insights/cohorts/compare", json={**body, "left": {"checklist_id": 999}}).status_code == 404
    assert db_rows(cohort.db) == before


def test_no_applicable_scored_weight_is_not_misclassified_as_an_unresolved_answer(cohort):
    cohort.source()
    rubric = cohort.checklist.model_copy(deep=True); rubric.criteria = [rubric.criteria[1]]
    cohort.version(rubric)
    answer = full_assessment(rubric); answer.results["needs"].disposition = "not_applicable"
    answer.results["needs"].value = None; answer.results["needs"].na_reason = "SYNTHETIC condition applies"
    cohort.add("A", rubric=rubric, version_id=2, assessment=answer)
    cohort.add("B", model="B", rubric=rubric, version_id=2, assessment=answer)
    result = cohort.compare(left={"checklist_id": 2, "model": "A"}, right={"checklist_id": 2, "model": "B"})
    assert result["coverage"]["no_numeric_total"] == 1 and result["coverage"]["unresolved"] == 0
    assert result["pairs"][0]["left"]["score_reason"] == "NO_APPLICABLE_SCORED_WEIGHT"
    assert result["criteria"][0]["answer_comparable_count"] == 1 and result["criteria"][0]["points_difference"]["count"] == 0


def test_added_removed_and_type_changed_definitions_remain_separate_from_answer_changes(cohort):
    cohort.source()
    rubric = cohort.checklist.model_copy(deep=True)
    rubric.criteria = rubric.criteria[1:]
    rubric.criteria[0].name = "SYNTHETIC renamed needs"
    added = rubric.criteria[0].model_copy(deep=True); added.id = "new_rule"; rubric.criteria.append(added)
    rubric.criteria[-2].answer_type = "binary"; rubric.criteria[-2].weight = Decimal("0")
    cohort.version(rubric)
    cohort.add("A"); cohort.add("B", model="B", rubric=rubric, version_id=2)
    result = cohort.compare(right={"checklist_id": 2, "model": "B"})
    rows = {row["criterion_id"]: row for row in result["criteria"]}
    assert rows["contact"]["right_name"] is None and rows["new_rule"]["left_name"] is None
    assert rows["needs"]["definition_changed_count"] == 1 and rows["needs"]["answer_changed_count"] == 0
    assert rows["critical_errors"]["left_type"] == "flag" and rows["critical_errors"]["right_type"] == "binary"
    assert rows["critical_errors"]["answer_comparable_count"] == 0


@pytest.mark.parametrize("invalid_total", ["NaN", "Infinity", "1e1000001", True])
def test_invalid_saved_totals_are_not_zeroes_or_aggregate_numbers(cohort, invalid_total):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "A"); calculated = deepcopy(run.effective_score); calculated["total"] = invalid_total; run.effective_score = calculated
    result = cohort.compare(); pair = result["pairs"][0]
    assert pair["left"]["total_state"] == "invalid" and pair["left"]["total"] is None
    assert pair["status"] == "invalid" and "INVALID_SAVED_TOTAL" in pair["reasons"]
    assert result["total_difference"]["count"] == 0


def test_invalid_saved_judgments_stay_unavailable_and_leave_originals_untouched(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "A"); original = deepcopy(run.original)
        final = deepcopy(run.effective); final["results"]["critical_errors"]["value"] = "false"; run.effective = final
    result = cohort.compare(); critical = next(row for row in result["criteria"] if row["criterion_id"] == "critical_errors")
    assert result["coverage"]["invalid"] == 1
    assert critical["transitions"][0]["left"] == {"disposition": "unavailable", "value": None, "reason": "invalid_saved_judgment"}
    with cohort.db.read_snapshot() as session: assert session.get(Evaluation, "A").original == original


def test_invalid_checklist_snapshot_returns_a_safe_refusal(cohort):
    cohort.source()
    with cohort.db.transaction() as session:
        version = session.get(ChecklistVersion, 1); snapshot = deepcopy(version.snapshot); snapshot["criteria"] = None; version.snapshot = snapshot
    with pytest.raises(HTTPException) as error: cohort.compare()
    assert error.value.status_code == 409 and "snapshot is invalid" in error.value.detail


def test_read_snapshot_does_not_mix_a_concurrent_review_revision_into_its_pairs(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.read_snapshot() as snapshot:
        snapshot.execute(select(Evaluation.id)).all()
        with cohort.db.transaction() as writer:
            run = writer.get(Evaluation, "A"); final = full_assessment(cohort.checklist); final.results["contact"].value = False
            run.effective = final.model_dump(mode="json"); run.effective_score = score(cohort.checklist, final, ["m0001"])
            run.updated_at = "2026-11-09T00:00:00+00:00"
        before_review = compare_cohorts(snapshot, {"dataset_group_id": "DEV", "left": {"checklist_id": 1, "model": "A"}, "right": {"checklist_id": 1, "model": "B"}})
        assert before_review["pairs"][0]["total_difference"] == "0.00"
        assert before_review["pairs"][0]["left"]["updated_at"] != "2026-11-09T00:00:00+00:00"
    after_review = cohort.compare()
    assert after_review["pairs"][0]["total_difference"] == "10.00"


def test_two_hundred_pairs_work_and_a_two_hundred_first_revision_is_refused(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        source = session.get(Conversation, "source")
        originals = [session.get(Evaluation, run_id) for run_id in ("A", "B")]
        for i in range(1, 200):
            session.add(Conversation(id=f"s{i}", group_id="DEV", source_id=f"SYNTHETIC_{i:03}", revision=1,
                content_hash=source.content_hash, snapshot=deepcopy(source.snapshot)))
        session.flush()
        for i in range(1, 200):
            for run in originals:
                values = {column.name: deepcopy(getattr(run, column.name)) for column in Evaluation.__table__.columns if column.name not in {"id", "conversation_id"}}
                session.add(Evaluation(id=f"{run.id}_{i}", conversation_id=f"s{i}", **values))
    result = cohort.compare()
    assert len(result["pairs"]) == result["coverage"]["matched"] == result["total_difference"]["count"] == 200
    assert all(row["denominator"] == 200 and sum(cell["count"] for cell in row["transitions"]) == 200 for row in result["criteria"])
    cohort.source("s201")
    with pytest.raises(HTTPException) as error: cohort.compare()
    assert error.value.status_code == 422 and "201 exact source revisions" in error.value.detail


def test_conflicting_recorded_checklist_provenance_is_visible_and_not_aggregated(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "B"); meta = deepcopy(run.meta); meta["checklist_hash"] = "c"*64; run.meta = meta
    result = cohort.compare()
    assert result["coverage"]["incompatible"] == result["coverage"]["provenance_conflict_pairs"] == 1
    assert "RECORDED_CHECKLIST_HASH_DIFFERS" in result["pairs"][0]["reasons"]
    assert result["total_difference"]["count"] == 0
    assert all(row["answer_comparable_count"] == row["points_difference"]["count"] == 0 for row in result["criteria"])


@pytest.mark.parametrize("private", ["file:///C:/private", "javascript:alert(1)", "data:text/plain,PRIVATE", 'C:\\private\\file', '{"api_key":"PRIVATE"}'])
def test_private_identifier_material_is_withheld_in_options(cohort, private):
    cohort.source(); cohort.add("A", meta={"model": private})
    with cohort.db.read_snapshot() as session: options = cohort_options(session)
    model = options["datasets"][0]["checklists"][0]["fields"]["model"]
    assert model == {"values": [], "unknown_count": 1}


@pytest.mark.parametrize("unresolved_basis", ["original", "effective"])
def test_selected_basis_completeness_is_independent_of_current_effective_workflow(cohort, unresolved_basis):
    cohort.source()
    resolved = full_assessment(cohort.checklist)
    unresolved = full_assessment(cohort.checklist)
    unresolved.results["critical_errors"].disposition = "needs_review"; unresolved.results["critical_errors"].value = None
    unresolved.results["critical_errors"].review_reason = "SYNTHETIC unavailable reference"
    cohort.add("A", assessment=unresolved if unresolved_basis == "original" else resolved,
        effective=unresolved if unresolved_basis == "effective" else resolved)
    cohort.add("B", model="B")
    original = cohort.compare(basis="original"); effective = cohort.compare(basis="effective")
    for result, basis in ((original, "original"), (effective, "effective")):
        expected = "needs_review" if basis == unresolved_basis else "complete"
        assert result["pairs"][0]["left"]["completeness"] == expected
        assert result["pairs"][0]["status"] == ("unresolved" if expected == "needs_review" else "matched")
        assert result["pairs"][0]["total_comparable"] is (expected == "complete")
    assert original["pairs"][0]["left"]["run_completeness"] == effective["pairs"][0]["left"]["run_completeness"]


@pytest.mark.parametrize("mismatch", ["extra", "missing"])
def test_answer_coverage_must_match_its_own_saved_checklist_exactly(cohort, mismatch):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "A"); final = deepcopy(run.effective)
        if mismatch == "extra": final["results"]["unconfigured"] = deepcopy(final["results"]["contact"])
        else: final["results"].pop("contact")
        run.effective = final
    result = cohort.compare()
    assert result["coverage"]["invalid"] == 1 and not result["pairs"][0]["left"]["criterion_coverage_valid"]
    assert all(row["answer_comparable_count"] == row["points_difference"]["count"] == 0 for row in result["criteria"])
    assert result["total_difference"]["count"] == 0


def test_equivalent_hex_hash_case_is_not_a_provenance_conflict(cohort):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "B"); meta = deepcopy(run.meta); meta["checklist_hash"] = meta["checklist_hash"].upper(); run.meta = meta
    result = cohort.compare()
    assert result["coverage"]["matched"] == 1 and result["coverage"]["provenance_conflict_pairs"] == 0


@pytest.mark.parametrize("generation", [{"reasoning": {"effort": []}}, {"reasoning": {"effort": {}}}, {"max_output_tokens": 10**400}])
def test_malformed_generation_metadata_is_withheld_without_crashing(cohort, generation):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "A"); meta = deepcopy(run.meta); meta["generation"] = generation; run.meta = meta
    before = db_rows(cohort.db)
    result = cohort.compare()
    assert result["pairs"][0]["left"]["provenance"]["generation"] == {}
    assert db_rows(cohort.db) == before


@pytest.mark.parametrize("completeness", [[], {}])
def test_malformed_saved_completeness_stays_unknown_without_crashing(cohort, completeness):
    cohort.source(); cohort.add("A"); cohort.add("B", model="B")
    with cohort.db.transaction() as session:
        run = session.get(Evaluation, "A"); saved_score = deepcopy(run.effective_score); saved_score["completeness"] = completeness; run.effective_score = saved_score
    before = db_rows(cohort.db)
    result = cohort.compare()
    assert result["pairs"][0]["left"]["completeness"] == "unknown"
    assert db_rows(cohort.db) == before
