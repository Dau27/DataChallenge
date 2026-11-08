"""Distributions of saved judgments, with exact-case membership and no regrading."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from pydantic import ValidationError

from backend.app.domain import Checklist, Judgment, validate_judgment
from backend.app.services.insights_common import load_scope


def _number(value):
    number = Decimal(str(value))
    return "0" if number == 0 else format(number.normalize(), "f")


def _buckets(criterion):
    if criterion.answer_type == "flag":
        return [("flagged", "Flagged"), ("clear", "Not flagged"), ("unknown", "Unknown")]
    values = ([("yes", "Yes"), ("no", "No")] if criterion.answer_type == "binary" else
              [("value:" + _number(anchor.value), _number(anchor.value)) for anchor in criterion.scale])
    return values + [("not_applicable", "N/A"), ("needs_review", "Needs review"), ("unavailable", "Unavailable")]


def _bucket(criterion, run, basis, criterion_ids):
    unavailable = "unknown" if criterion.answer_type == "flag" else "unavailable"
    if not run or run["state"] != "succeeded":
        return unavailable
    saved = run.get(basis)
    if not isinstance(saved, dict) or not isinstance(saved.get("results"), dict) or set(saved["results"]) != criterion_ids:
        return unavailable
    try:
        judgment = Judgment.model_validate(saved["results"][criterion.id])
        validate_judgment(criterion, judgment)
    except (ValidationError, ValueError, TypeError, KeyError):
        return unavailable
    if criterion.answer_type == "flag":
        return "unknown" if judgment.disposition != "assessed" else "flagged" if judgment.value else "clear"
    if judgment.disposition != "assessed":
        return judgment.disposition
    return ("yes" if judgment.value else "no") if criterion.answer_type == "binary" else "value:" + _number(judgment.value)


def criterion_breakdown(session, checklist_id, conversation_ids, basis="effective"):
    if basis not in {"original", "effective"}:
        raise ValueError("Select original or effective judgments")
    scope = load_scope(session, checklist_id, conversation_ids)
    checklist = Checklist.model_validate(scope["checklist"]["snapshot"])
    criterion_ids = {criterion.id for criterion in checklist.criteria}
    grouped = defaultdict(list)
    for source in scope["sources"]:
        grouped[source["group_id"]].append(source)
    groups = []
    for group_id, sources in grouped.items():
        coverage = {state: 0 for state in ("not_evaluated", "queued", "running", "succeeded", "failed", "interrupted")}
        for source in sources:
            run = scope["runs"].get(source["id"])
            coverage[run["state"] if run else "not_evaluated"] += 1
        rows = []
        for criterion in checklist.criteria:
            buckets = {key: {"key": key, "label": label, "count": 0, "denominator": len(sources), "cases": []}
                       for key, label in _buckets(criterion)}
            for source in sources:
                run = scope["runs"].get(source["id"])
                bucket = buckets[_bucket(criterion, run, basis, criterion_ids)]
                bucket["count"] += 1
                bucket["cases"].append({"conversation_id": source["id"], "source_id": source["source_id"],
                    "group_id": group_id, "revision": source["revision"], "evaluation_id": run["id"] if run else None,
                    "criterion_id": criterion.id})
            for bucket in buckets.values():
                bucket["percentage"] = str((100 * Decimal(bucket["count"]) / len(sources)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            rows.append({"criterion_id": criterion.id, "name": criterion.name, "answer_type": criterion.answer_type,
                "weight": str(criterion.weight) if criterion.weight is not None else None,
                "assessed_count": sum(bucket["count"] for key, bucket in buckets.items()
                    if key in {"yes", "no", "flagged", "clear"} or key.startswith("value:")),
                "buckets": list(buckets.values())})
        groups.append({"group_id": group_id, "total_sources": len(sources), "coverage": coverage, "criteria": rows})
    return {"checklist_id": checklist_id, "checklist_hash": scope["checklist"]["content_hash"], "basis": basis,
        "total_sources": len(scope["sources"]), "selection_policy": "Latest run per selected latest source revision; no fallback after failure",
        "manifest": scope["manifest"], "groups": groups}
