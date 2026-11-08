"""Read-only saved-result inspection. No job creation or provider access."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
import re
import math
from sqlalchemy import select

from backend.app.db import Appeal, ChecklistVersion, Conversation, Evaluation, Review
from backend.app.domain import canonical_json
from backend.app.services.evaluator import usage_summary


class SavedResultNotFound(LookupError):
    pass


def summary(evaluation):
    return {"id": evaluation.id, "conversation_id": evaluation.conversation_id, "checklist_id": evaluation.checklist_id,
            "state": evaluation.state, "completeness": evaluation.completeness, "cached_from": evaluation.cached_from,
            "total": evaluation.effective_score.get("total") if evaluation.effective_score else None,
            "error": evaluation.error, "created_at": evaluation.created_at, "updated_at": evaluation.updated_at}


def summary_columns():
    """Read list/detail headers without materializing judgments, metadata or attempts."""
    return (Evaluation.id, Evaluation.conversation_id, Evaluation.checklist_id, Evaluation.state,
            Evaluation.completeness, Evaluation.cached_from, Evaluation.effective_score["total"].as_string().label("total"),
            Evaluation.error, Evaluation.created_at, Evaluation.updated_at)


def saved_summaries(session, conversation_id=None):
    query = select(*summary_columns()).order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
    if conversation_id:
        query = query.where(Evaluation.conversation_id == conversation_id)
    return [dict(row) for row in session.execute(query).mappings()]


def version_view(version):
    return {"id": version.id, "content_hash": version.content_hash, "snapshot": version.snapshot, "created_at": version.created_at}


def columns(row):
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def evaluation_snapshot(session, evaluation_id):
    row = session.get(Evaluation, evaluation_id)
    if row is None:
        raise SavedResultNotFound("Evaluation not found")
    return deepcopy({**summary(row), "original": row.original, "original_score": row.original_score,
        "effective": row.effective, "effective_score": row.effective_score,
        "checklist": version_view(session.get(ChecklistVersion, row.checklist_id)), "metadata": row.meta, "attempts": row.attempts,
        "usage": usage_summary(row.attempts, row.meta.get("rate", {})),
        "appeals": [columns(a) for a in session.scalars(select(Appeal).where(Appeal.evaluation_id == row.id).order_by(Appeal.created_at, Appeal.id))],
        "reviews": [columns(r) for r in session.scalars(select(Review).where(Review.evaluation_id == row.id).order_by(Review.id))]})


def source_view(conversation):
    return {"id": conversation.id, "source_id": conversation.source_id, "group_id": conversation.group_id,
            "revision": conversation.revision, "content_hash": conversation.content_hash,
            "language": conversation.snapshot["language"], "channel": conversation.snapshot["channel"],
            "message_count": len(conversation.snapshot["transcript"])}


def numeric_difference(left, right):
    if left is None or right is None:
        return None
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
        if not a.is_finite() or not b.is_finite():
            return None
        with localcontext() as context:
            context.prec = max(50, len(str(left)) + len(str(right)) + 5)
            return str(b - a)
    except InvalidOperation:
        return None


def _safe_generation_value(value):
    if value is None:
        return True
    if type(value) not in {int, float}:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _side(snapshot, basis):
    score = snapshot[basis + "_score"]
    # Only evaluation provenance belongs here; arbitrary stored metadata is not a credential channel.
    keys = {"provider", "model", "prompt_version", "schema_version", "scoring_version", "checklist_hash",
            "evidence_validation_version", "mode"}
    metadata = {key: value for key, value in snapshot["metadata"].items() if key in keys and isinstance(value, (str, type(None)))}
    for key in ("prompt_hash", "schema_hash"):
        value = snapshot["metadata"].get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value):
            metadata[key] = value
    # The provider stores only its response model identifier here. Do not expose arbitrary
    # attempt payloads or nested metadata alongside this narrowly typed provenance field.
    metadata["response_models"] = list(dict.fromkeys(a["response_model"] for a in snapshot["attempts"]
        if isinstance(a.get("response_model"), str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,149}", a["response_model"])
        and not a["response_model"].lower().startswith(("sk-", "nvapi-")) and "://" not in a["response_model"]))
    generation = snapshot["metadata"].get("generation") or {}
    if not isinstance(generation, dict):
        generation = {}
    metadata["generation"] = {key: generation[key] for key in ("temperature", "max_output_tokens", "top_p")
        if key in generation and _safe_generation_value(generation[key])}
    if isinstance(generation.get("reasoning"), dict):
        effort = generation["reasoning"].get("effort")
        if isinstance(effort, str) and effort in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            metadata["generation"]["reasoning"] = {"effort": effort}
    return {"id": snapshot["id"], "basis": basis, "state": snapshot["state"], "error": snapshot["error"],
            "created_at": snapshot["created_at"], "updated_at": snapshot["updated_at"], "cached_from": snapshot["cached_from"],
            "checklist": snapshot["checklist"], "score": score,
            "metadata": metadata,
            "usage": snapshot["usage"], "review_count": len(snapshot["reviews"])}


def compare_saved(session, left_id, right_id, left_basis="effective", right_basis="effective"):
    if left_basis not in {"original", "effective"} or right_basis not in {"original", "effective"}:
        raise ValueError("Select original or effective answers")
    left, right = evaluation_snapshot(session, left_id), evaluation_snapshot(session, right_id)
    if left["conversation_id"] != right["conversation_id"]:
        raise ValueError("Saved-run comparison requires the same conversation revision")
    conversation = session.get(Conversation, left["conversation_id"])
    sides = [_side(left, left_basis), _side(right, right_basis)]
    maps = [{c["id"]: c for c in s["checklist"]["snapshot"]["criteria"]} for s in sides]
    answers = [(s[basis] or {}).get("results", {}) for s, basis in ((left, left_basis), (right, right_basis))]
    points = [{r["criterion_id"]: r for r in (s["score"] or {}).get("criteria", [])} for s in sides]
    rows = []
    scoring_version = (sides[0]["score"] or {}).get("scoring_version")
    scoring_matches = bool(scoring_version and scoring_version == (sides[1]["score"] or {}).get("scoring_version"))
    for cid in dict.fromkeys([*maps[0], *maps[1]]):
        a, b = maps[0].get(cid), maps[1].get(cid)
        ja, jb = answers[0].get(cid), answers[1].get(cid)
        changes = []
        configuration_changes = [k for k in sorted(set(a or {}) | set(b or {}))
            if canonical_json((a or {}).get(k)) != canonical_json((b or {}).get(k))]
        if configuration_changes:
            changes.append("configuration")
        if (ja is None) != (jb is None):
            changes.append("availability")
        elif ja is not None and jb is not None:
            if canonical_json([ja["disposition"], ja["value"]]) != canonical_json([jb["disposition"], jb["value"]]):
                changes.append("answer")
            changes += [key for key in ("explanation", "evidence", "na_reason", "review_reason")
                        if canonical_json(ja.get(key)) != canonical_json(jb.get(key))]
        if canonical_json(points[0].get(cid)) != canonical_json(points[1].get(cid)):
            changes.append("points")
        meaning = lambda c: {k: v for k, v in c.items() if k not in {"weight", "section_id"}}
        comparable = bool(a and b and canonical_json(meaning(a)) == canonical_json(meaning(b)) and ja and jb)
        same_points_rule = bool(a and b and canonical_json(a) == canonical_json(b) and scoring_matches and comparable)
        rows.append({"criterion_id": cid, "change": "added" if a is None else "removed" if b is None else "changed" if changes else "unchanged",
            "changes": changes, "configuration_changes": configuration_changes, "answer_comparable": comparable,
            "points_difference": numeric_difference((points[0].get(cid) or {}).get("raw_points"),
                (points[1].get(cid) or {}).get("raw_points")) if same_points_rule else None,
            "left": {"criterion": a, "judgment": ja, "points": points[0].get(cid)},
            "right": {"criterion": b, "judgment": jb, "points": points[1].get(cid)}})
    totals = [(s["score"] or {}).get("total") for s in sides]
    reason = ("One or both saved assessments are unavailable." if not left[left_basis] or not right[right_basis] else
              "Checklist snapshots differ; total changes are not directly comparable." if left["checklist"]["content_hash"] != right["checklist"]["content_hash"] else
              "Scoring versions differ." if not scoring_matches else
              "One or both saved totals are unavailable." if numeric_difference(*totals) is None else None)
    return {"source": source_view(conversation), "left": sides[0], "right": sides[1], "criteria": rows,
            "total_comparable": reason is None, "total_difference": numeric_difference(*totals) if reason is None else None,
            "notice": reason or "Difference between saved results; this does not establish improved operator behavior or model accuracy."}
