"""Bounded historical saved-run comparisons. No scoring, writes or provider access."""
from collections import Counter
from decimal import Decimal, InvalidOperation, localcontext
import math
import re
from typing import Annotated, Literal

from fastapi import HTTPException
from pydantic import Field, StrictInt, StrictStr, ValidationError, field_validator
from sqlalchemy import func, select

from backend.app.db import ChecklistVersion, Conversation, Evaluation
from backend.app.domain import Checklist, Contract, Criterion, Judgment, canonical_json, validate_judgment
from backend.app.services.saved_results import compare_saved

SELECTOR_FIELDS = ("model", "prompt_version", "schema_version", "evidence_validation_version")
PROVENANCE_FIELDS = ("provider", *SELECTOR_FIELDS, "scoring_version", "mode")
STATUSES = ("matched", "missing_left", "missing_right", "missing_both", "failed", "pending",
            "unresolved", "incompatible", "no_numeric_total", "invalid")
STATES = {"queued", "running", "succeeded", "failed", "interrupted"}
POLICY = "Latest matching (created_at DESC, id DESC) per exact source revision; no successful fallback."
SCOPE_POLICY = "Every saved source revision in the one selected dataset, ordered by source_id, revision, id. Oversized scopes are refused; no partial aggregates."
NOTICE = "Historical saved-result differences, not evaluator accuracy. Higher operator scores do not establish a better evaluator. Cached reuse is not an independent assessment."
Identifier = Annotated[StrictStr, Field(min_length=1, max_length=150)]
_PRIVATE = re.compile(r"[a-z][a-z0-9+.-]*://|(?:data|javascript|vbscript|mailto):|[a-z]:[\\/]|(?:sk|nvapi)-[A-Za-z0-9_-]+|bearer\s+|(?:api[_-]?key|token|password|authorization|secret)[\"']?\s*[:=]", re.I)


def safe_identifier(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 150:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in value) or _PRIVATE.search(value):
        return None
    return value


class CohortSelector(Contract):
    checklist_id: Annotated[StrictInt, Field(gt=0)]
    model: Identifier | None = None
    prompt_version: Identifier | None = None
    schema_version: Identifier | None = None
    evidence_validation_version: Identifier | None = None

    @field_validator(*SELECTOR_FIELDS)
    @classmethod
    def recorded_identifier(cls, value):
        if value is not None and safe_identifier(value) is None:
            raise ValueError("Use a nonblank recorded identifier without URLs or credential material")
        return value


class CohortCompareRequest(Contract):
    dataset_group_id: Identifier
    left: CohortSelector
    right: CohortSelector
    basis: Literal["original", "effective"] = "effective"
    limit: Annotated[StrictInt, Field(ge=1, le=200)] = 200

    @field_validator("dataset_group_id")
    @classmethod
    def dataset_identifier(cls, value):
        if safe_identifier(value) is None:
            raise ValueError("Use a recorded dataset identifier without URLs or credential material")
        return value


def selector_view(selector):
    # Omission is wildcard; an explicit null means unknown. Never erase this distinction.
    return selector.model_dump(exclude_unset=True)


def _metadata_value(meta, key):
    return safe_identifier(meta.get(key)) if isinstance(meta, dict) else None


def _matches(row, selector):
    return row["checklist_id"] == selector.checklist_id and all(
        _metadata_value(row["meta"], key) == getattr(selector, key)
        for key in SELECTOR_FIELDS if key in selector.model_fields_set)


def cohort_options(session):
    """Small provenance projections only; no transcripts, judgments, errors or attempts."""
    datasets = {}
    unavailable_datasets = 0
    for group_id, count in session.execute(select(Conversation.group_id, func.count()).group_by(Conversation.group_id)):
        if safe_identifier(group_id) is None:
            unavailable_datasets += 1
            continue
        datasets[group_id] = {"dataset_group_id": group_id, "source_revision_count": count,
                              "saved_evaluation_count": 0, "checklists": {}}
    query = select(Conversation.group_id, Evaluation.checklist_id, Evaluation.meta).join(
        Evaluation, Evaluation.conversation_id == Conversation.id)
    for group_id, checklist_id, meta in session.execute(query):
        dataset = datasets.get(group_id)
        if dataset is None:
            continue
        dataset["saved_evaluation_count"] += 1
        profile = dataset["checklists"].setdefault(checklist_id, {"checklist_id": checklist_id, "run_count": 0,
            "fields": {key: Counter() for key in SELECTOR_FIELDS}})
        profile["run_count"] += 1
        for key in SELECTOR_FIELDS:
            profile["fields"][key][_metadata_value(meta, key)] += 1
    for dataset in datasets.values():
        profiles = []
        for checklist_id, profile in sorted(dataset["checklists"].items()):
            profile["fields"] = {key: {"values": [{"value": value, "count": count} for value, count in sorted(
                ((value, count) for value, count in counts.items() if value is not None))], "unknown_count": counts[None]}
                for key, counts in profile["fields"].items()}
            profiles.append(profile)
        dataset["checklists"] = profiles
    versions = [{"checklist_id": version.id, "content_hash": version.content_hash}
                for version in session.scalars(select(ChecklistVersion).order_by(ChecklistVersion.id))]
    return {"version": 1, "datasets": [datasets[key] for key in sorted(datasets)], "checklists": versions,
            "selector_fields": list(SELECTOR_FIELDS), "unavailable_dataset_identifiers": unavailable_datasets,
            "unknown_policy": "Absent filter means any recorded value; null means missing, invalid or withheld provenance. Unknown does not establish configuration equality.",
            "selection_policy": POLICY, "scope_policy": SCOPE_POLICY, "notice": NOTICE, "max_pairs": 200}


def _number(value):
    try:
        if value is None or isinstance(value, bool):
            return None
        number = Decimal(str(value))
        return number if number.is_finite() and abs(number.adjusted()) <= 1000 else None
    except (InvalidOperation, ValueError):
        return None


def _summary(values):
    numbers = [number for value in values if (number := _number(value)) is not None]
    if not numbers:
        return {"count": 0, "sum": None, "mean": None}
    with localcontext() as context:
        context.prec = max(60, max(len(number.as_tuple().digits) + abs(number.as_tuple().exponent) for number in numbers) + 10)
        total = sum(numbers, Decimal(0))
        return {"count": len(numbers), "sum": str(total), "mean": str(total / len(numbers))}


def _finite_generation_value(value):
    if value is None:
        return True
    if type(value) not in {int, float}:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _completeness(value):
    return value if isinstance(value, str) and value in {"complete", "needs_review", "incomplete"} else "unknown"


def _provenance(run):
    meta = run.meta if isinstance(run.meta, dict) else {}
    result = {key: _metadata_value(meta, key) for key in PROVENANCE_FIELDS}
    for key in ("prompt_hash", "schema_hash", "request_schema_hash", "checklist_hash"):
        value = meta.get(key)
        result[key] = value if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) else None
    result["unknown_fields"] = [key for key, value in result.items() if value is None]
    generation = meta.get("generation")
    result["generation"] = {}
    if isinstance(generation, dict):
        for key in ("temperature", "max_output_tokens", "top_p"):
            value = generation.get(key)
            if key in generation and _finite_generation_value(value):
                result["generation"][key] = value
        reasoning = generation.get("reasoning")
        if isinstance(reasoning, dict) and isinstance(reasoning.get("effort"), str) and reasoning["effort"] in {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}:
            result["generation"]["reasoning_effort"] = reasoning["effort"]
    result["generation_recorded"] = isinstance(generation, dict)
    attempts = run.attempts if isinstance(run.attempts, list) else []
    result["response_models"] = sorted({value for attempt in attempts if isinstance(attempt, dict)
        and (value := safe_identifier(attempt.get("response_model"))) is not None})
    return result


def _available(run, basis):
    saved = getattr(run, basis) if run is not None else None
    return bool(isinstance(saved, dict) and isinstance(saved.get("results"), dict))


def _side(run, basis, versions, cache_origins):
    if run is None:
        return None
    saved_score = getattr(run, basis + "_score")
    saved_score = saved_score if isinstance(saved_score, dict) else {}
    total = _number(saved_score.get("total"))
    origin = cache_origins.get(run.cached_from)
    cached_from = run.cached_from if isinstance(run.cached_from, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", run.cached_from) else None
    provenance = _provenance(run)
    provenance_conflict = provenance["checklist_hash"] is not None and provenance["checklist_hash"].lower() != versions[run.checklist_id].content_hash.lower()
    coverage_valid = _available(run, basis) and set(getattr(run, basis)["results"]) == {criterion["id"] for criterion in versions[run.checklist_id].snapshot["criteria"]}
    return {"evaluation_id": run.id, "conversation_id": run.conversation_id, "checklist_id": run.checklist_id,
            "checklist_hash": versions[run.checklist_id].content_hash, "created_at": run.created_at, "updated_at": run.updated_at,
            "state": run.state if run.state in STATES else "unknown",
            "completeness": _completeness(saved_score.get("completeness")), "run_completeness": _completeness(run.completeness),
            "original_available": _available(run, "original"), "effective_available": _available(run, "effective"),
            "basis_available": _available(run, basis), "total": str(total) if total is not None else None,
            "criterion_coverage_valid": coverage_valid,
            "total_state": "numeric" if total is not None else "missing" if saved_score.get("total") is None else "invalid",
            "score_reason": safe_identifier(saved_score.get("reason")), "saved_scoring_version": safe_identifier(saved_score.get("scoring_version")),
            "cached": run.cached_from is not None, "cached_from": cached_from,
            "cache_origin_present": origin is not None, "cache_source_matches": origin == run.conversation_id if origin is not None else None,
            "provenance": provenance, "provenance_conflict": provenance_conflict}


def _answer(criterion, run, basis, coverage_valid):
    unavailable = {"disposition": "unavailable", "value": None}
    if criterion is None:
        return {**unavailable, "reason": "criterion_absent"}
    if run is None:
        return {**unavailable, "reason": "missing_run"}
    if run.state != "succeeded" or not _available(run, basis):
        return {**unavailable, "reason": "assessment_unavailable"}
    if not coverage_valid:
        return {**unavailable, "reason": "criterion_coverage_mismatch"}
    try:
        saved = getattr(run, basis)["results"][criterion["id"]]
        judgment = Judgment.model_validate(saved)
        validate_judgment(Criterion.model_validate(criterion), judgment)
    except (KeyError, TypeError, ValueError, ValidationError):
        return {**unavailable, "reason": "invalid_saved_judgment"}
    value = judgment.value
    if not isinstance(value, bool) and value is not None:
        value = format(Decimal(str(value)), "f")
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        if Decimal(value) == 0:
            value = "0"
    return {"disposition": judgment.disposition, "value": value, "reason": None}


def _criterion_template(left_version, right_version):
    maps = [{item["id"]: item for item in version.snapshot["criteria"]} for version in (left_version, right_version)]
    rows = []
    for criterion_id in dict.fromkeys([*maps[0], *maps[1]]):
        a, b = maps[0].get(criterion_id), maps[1].get(criterion_id)
        rows.append({"criterion_id": criterion_id, "left": a, "right": b, "transitions": {}, "point_values": [],
            "answer_comparable_count": 0, "answer_changed_count": 0, "disposition_changed_count": 0,
            "configuration_changed_count": 0, "definition_changed_count": 0, "details_only_count": 0, "unavailable_count": 0})
    return rows


def compare_cohorts(session, request):
    request = CohortCompareRequest.model_validate(request)
    versions = {version.id: version for version in session.scalars(select(ChecklistVersion).where(
        ChecklistVersion.id.in_([request.left.checklist_id, request.right.checklist_id])))}
    if set(versions) != {request.left.checklist_id, request.right.checklist_id}:
        raise HTTPException(404, "Selected checklist version not found")
    try:
        for version in versions.values(): Checklist.model_validate(version.snapshot)
    except (ValidationError, ValueError, TypeError):
        raise HTTPException(409, "A selected saved checklist snapshot is invalid. No comparison was produced.") from None
    source_columns = (Conversation.id, Conversation.source_id, Conversation.group_id, Conversation.revision, Conversation.content_hash)
    sources = list(session.execute(select(*source_columns).where(Conversation.group_id == request.dataset_group_id)
        .order_by(Conversation.source_id, Conversation.revision, Conversation.id).limit(request.limit + 1)).mappings())
    if len(sources) > request.limit:
        count = session.scalar(select(func.count()).select_from(Conversation).where(Conversation.group_id == request.dataset_group_id))
        raise HTTPException(422, f"Dataset has {count} exact source revisions; limit is {request.limit} (maximum 200). No partial comparison was produced. Select a smaller dataset or raise the limit within 200.")
    if not sources:
        raise HTTPException(404, "Selected dataset has no saved source revisions")
    source_ids = [source["id"] for source in sources]
    header_query = select(Evaluation.id, Evaluation.conversation_id, Evaluation.checklist_id, Evaluation.meta).where(
        Evaluation.conversation_id.in_(source_ids), Evaluation.checklist_id.in_(versions)).order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
    selected = [{}, {}]
    for header in session.execute(header_query).mappings():
        for side, selector in zip(selected, (request.left, request.right)):
            if header["conversation_id"] not in side and _matches(header, selector):
                side[header["conversation_id"]] = header["id"]
    ids = set(selected[0].values()) | set(selected[1].values())
    runs = {run.id: run for run in session.scalars(select(Evaluation).where(Evaluation.id.in_(ids)))} if ids else {}
    cached_ids = {run.cached_from for run in runs.values() if run.cached_from}
    cache_origins = dict(session.execute(select(Evaluation.id, Evaluation.conversation_id).where(Evaluation.id.in_(cached_ids))).all()) if cached_ids else {}
    templates = _criterion_template(versions[request.left.checklist_id], versions[request.right.checklist_id])
    pairs, total_differences = [], []
    coverage = {key: 0 for key in STATUSES}
    coverage.update(source_revisions=len(sources), paired=0, cached_pairs=0, same_run_pairs=0, unknown_provenance_pairs=0, provenance_conflict_pairs=0)
    for source in sources:
        a, b = [runs.get(side.get(source["id"])) for side in selected]
        left, right = [_side(run, request.basis, versions, cache_origins) for run in (a, b)]
        reasons, comparison = [], None
        if a is not None and b is not None:
            coverage["paired"] += 1
            try:
                comparison = compare_saved(session, a.id, b.id, request.basis, request.basis)
            except (KeyError, TypeError, ValueError, AttributeError, ArithmeticError, ValidationError):
                reasons.append("INVALID_SAVED_ASSESSMENT")
        criteria = {row["criterion_id"]: row for row in comparison["criteria"]} if comparison else {}
        pair_criteria = []
        for template in templates:
            criterion_id = template["criterion_id"]
            aa, bb = _answer(template["left"], a, request.basis, left["criterion_coverage_valid"] if left else False), _answer(template["right"], b, request.basis, right["criterion_coverage_valid"] if right else False)
            row = criteria.get(criterion_id)
            comparable = bool(row and row["answer_comparable"] and left and right and not left["provenance_conflict"] and not right["provenance_conflict"]
                and aa["disposition"] != "unavailable" and bb["disposition"] != "unavailable")
            scoring_matches = bool(left and right and left["saved_scoring_version"] and left["saved_scoring_version"] == right["saved_scoring_version"])
            point_difference = row["points_difference"] if comparable and row and scoring_matches else None
            transition_key = canonical_json([aa, bb, comparable])
            transition = template["transitions"].setdefault(transition_key, {"left": aa, "right": bb, "answer_comparable": comparable, "count": 0, "conversation_ids": []})
            transition["count"] += 1; transition["conversation_ids"].append(source["id"])
            changes = row["changes"] if row else []
            template["answer_comparable_count"] += int(comparable)
            template["answer_changed_count"] += int(comparable and (aa["disposition"], aa["value"]) != (bb["disposition"], bb["value"]))
            template["disposition_changed_count"] += int(comparable and aa["disposition"] != bb["disposition"])
            template["configuration_changed_count"] += int("configuration" in changes)
            template["definition_changed_count"] += int(bool(row) and any(key not in {"weight", "section_id"} for key in row["configuration_changes"]))
            template["details_only_count"] += int(bool(changes) and set(changes) <= {"explanation", "evidence", "na_reason", "review_reason"} and comparable)
            template["unavailable_count"] += int(aa["disposition"] == "unavailable" or bb["disposition"] == "unavailable")
            if point_difference is not None:
                template["point_values"].append(point_difference)
            pair_criteria.append({"criterion_id": criterion_id, "answer_comparable": comparable, "left": aa, "right": bb,
                "changes": changes, "points_difference": point_difference})
        sides = [side for side in (left, right) if side is not None]
        invalid = any(answer["reason"] in {"invalid_saved_judgment", "criterion_coverage_mismatch"} for row in pair_criteria for answer in (row["left"], row["right"]))
        invalid_total = any(side["total_state"] == "invalid" for side in sides)
        provenance_conflict = any(side["provenance_conflict"] for side in sides)
        unresolved = any(side["completeness"] == "needs_review" for side in sides) or any(
            answer["disposition"] == "needs_review" for row in pair_criteria for answer in (row["left"], row["right"]))
        total_comparable = bool(comparison and comparison["total_comparable"] and left and right
            and left["saved_scoring_version"] and left["saved_scoring_version"] == right["saved_scoring_version"]
            and not invalid and not invalid_total and not provenance_conflict and all(side["state"] == "succeeded" for side in sides) and not unresolved)
        if a is None or b is None:
            status = "missing_both" if a is None and b is None else "missing_left" if a is None else "missing_right"
        elif any(side["state"] in {"failed", "interrupted"} for side in sides): status = "failed"
        elif any(side["state"] in {"queued", "running"} for side in sides): status = "pending"
        elif unresolved: status = "unresolved"
        elif invalid or invalid_total or "INVALID_SAVED_ASSESSMENT" in reasons or any(side["state"] != "succeeded" for side in sides): status = "invalid"
        elif not all(side["basis_available"] for side in sides): status = "invalid"
        elif provenance_conflict or left["checklist_hash"] != right["checklist_hash"] or not left["saved_scoring_version"] or left["saved_scoring_version"] != right["saved_scoring_version"]: status = "incompatible"
        elif not total_comparable: status = "no_numeric_total"
        else: status = "matched"
        coverage[status] += 1
        if any(side["cached"] for side in sides): coverage["cached_pairs"] += 1
        if a is not None and b is not None and a.id == b.id: coverage["same_run_pairs"] += 1
        if any(side["provenance"]["unknown_fields"] for side in sides): coverage["unknown_provenance_pairs"] += 1
        if provenance_conflict: coverage["provenance_conflict_pairs"] += 1
        if a is None: reasons.append("BASELINE_RUN_MISSING")
        if b is None: reasons.append("CANDIDATE_RUN_MISSING")
        if any(side["state"] in {"failed", "interrupted"} for side in sides): reasons.append("EXECUTION_FAILED_OR_INTERRUPTED")
        if any(side["state"] in {"queued", "running"} for side in sides): reasons.append("EXECUTION_PENDING")
        if unresolved: reasons.append("UNRESOLVED_JUDGMENTS")
        if invalid: reasons.append("INVALID_SAVED_JUDGMENT")
        if invalid_total: reasons.append("INVALID_SAVED_TOTAL")
        if provenance_conflict: reasons.append("RECORDED_CHECKLIST_HASH_DIFFERS")
        if any(side["cached"] and not side["cache_origin_present"] for side in sides): reasons.append("CACHE_ORIGIN_UNAVAILABLE")
        if any(side["cache_source_matches"] is False for side in sides): reasons.append("CACHE_SOURCE_REVISION_DIFFERS")
        if any(not side["basis_available"] for side in sides): reasons.append("SAVED_ANSWER_SET_UNAVAILABLE")
        if left and right:
            if left["checklist_hash"] != right["checklist_hash"]: reasons.append("CHECKLIST_SNAPSHOTS_DIFFER")
            if not left["saved_scoring_version"] or left["saved_scoring_version"] != right["saved_scoring_version"]: reasons.append("SCORING_VERSION_UNKNOWN_OR_DIFFERENT")
            if any(side["total"] is None for side in sides): reasons.append("NO_NUMERIC_TOTAL")
        difference = comparison["total_difference"] if total_comparable else None
        if difference is not None: total_differences.append(difference)
        pairs.append({"source": {"conversation_id": source["id"], "source_id": safe_identifier(source["source_id"]) or "Identifier withheld", "revision": source["revision"],
            "content_hash": source["content_hash"], "dataset_group_id": source["group_id"]}, "left": left, "right": right,
            "status": status, "reasons": list(dict.fromkeys(reasons)), "total_comparable": total_comparable,
            "total_difference": difference, "criteria": pair_criteria})
    aggregates = []
    for row in templates:
        aggregates.append({key: value for key, value in row.items() if key not in {"left", "right", "transitions", "point_values"}} | {
            "left_name": row["left"]["name"] if row["left"] else None, "right_name": row["right"]["name"] if row["right"] else None,
            "left_type": row["left"]["answer_type"] if row["left"] else None, "right_type": row["right"]["answer_type"] if row["right"] else None,
            "denominator": len(sources), "transitions": list(row["transitions"].values()), "points_difference": _summary(row["point_values"])})
    return {"version": 1, "dataset_group_id": request.dataset_group_id, "left": selector_view(request.left), "right": selector_view(request.right),
            "basis": request.basis, "limit": request.limit, "selection_policy": POLICY, "scope_policy": SCOPE_POLICY,
            "coverage": coverage, "coverage_policy": "Exclusive status precedence: missing, failed, pending, unresolved, invalid, incompatible, no numeric total, matched. Pair reasons preserve overlapping conditions.",
            "total_difference": _summary(total_differences), "pairs": pairs, "criteria": aggregates, "notice": NOTICE}
