"""Fixed-judgment arithmetic scenarios. Never create or alter a saved result."""
from copy import deepcopy

from pydantic import ValidationError
from sqlalchemy import func, select

from backend.app.db import ChecklistVersion, Conversation, Evaluation
from backend.app.domain import Assessment, Checklist, content_hash
from backend.app.services.checklists import field_issues
from backend.app.services.saved_results import SavedResultNotFound, numeric_difference
from backend.app.services.scoring import score

NOTICE = "Fixed-judgment simulation only. No model evaluation, saved result or checklist is changed."


def _version(session, checklist_id):
    version = session.get(ChecklistVersion, checklist_id)
    if version is None:
        raise SavedResultNotFound("Checklist version not found")
    return version


def preview_runs(session, checklist_id, offset=0, limit=100):
    version = _version(session, checklist_id)
    query = select(Evaluation.id, Evaluation.conversation_id, Evaluation.checklist_id,
        Evaluation.created_at, Evaluation.updated_at, Conversation.source_id, Conversation.group_id,
        Conversation.revision, Conversation.content_hash).join(Conversation, Conversation.id == Evaluation.conversation_id)\
        .where(Evaluation.checklist_id == checklist_id, Evaluation.state == "succeeded")
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    records = session.execute(query.order_by(Evaluation.created_at.desc(), Evaluation.id.desc()).offset(offset).limit(limit)).mappings()
    return {"checklist_id": checklist_id, "checklist_hash": version.content_hash,
        "total": total, "offset": offset, "limit": limit,
        "runs": [{**dict(row), "checklist_hash": version.content_hash} for row in records]}


def weight_preview(session, checklist_id, evaluation_id, basis, draft):
    if basis not in {"original", "effective"}:
        raise ValueError("Select original or effective judgments")
    version = _version(session, checklist_id)
    result = {"eligible": False, "simulation": True, "notice": NOTICE,
              "checklist_id": checklist_id, "checklist_hash": version.content_hash,
              "evaluation_id": evaluation_id, "basis": basis, "reasons": [], "errors": []}
    try:
        candidate = Checklist.model_validate(draft)
    except ValidationError as error:
        return {**result, "reasons": ["Fix the draft's configuration errors before previewing weights."],
                "errors": field_issues(error, draft)}
    try:
        saved = Checklist.model_validate(version.snapshot)
    except ValidationError:
        return {**result, "reasons": ["The saved checklist cannot be validated for this simulation."]}
    if content_hash(version.snapshot) != version.content_hash:
        return {**result, "reasons": ["The saved checklist hash does not match its snapshot."]}
    before, after = saved.model_dump(), candidate.model_dump()
    for snapshot in (before, after):
        for criterion in snapshot["criteria"]:
            criterion.pop("weight", None)
    if before != after:
        return {**result, "reasons": ["Only criterion weights may change. Restore all definitions, types, scales, N/A rules, sections, ordering and other fields to the saved version."]}
    run = session.get(Evaluation, evaluation_id)
    if run is None:
        raise SavedResultNotFound("Evaluation not found")
    if run.checklist_id != checklist_id:
        return {**result, "reasons": ["Select a saved run from this exact checklist version."]}
    if (run.meta or {}).get("checklist_hash", version.content_hash) != version.content_hash:
        return {**result, "reasons": ["The run's recorded checklist hash does not match this saved version."]}
    if run.state != "succeeded":
        return {**result, "reasons": ["Only a successful saved run with recorded judgments can be simulated."]}
    source = session.get(Conversation, run.conversation_id)
    if source is None:
        raise SavedResultNotFound("Conversation revision not found")
    raw = getattr(run, basis)
    recorded_score = getattr(run, basis + "_score")
    if raw is None or recorded_score is None:
        return {**result, "reasons": ["The selected judgment basis or saved score is unavailable."]}
    try:
        # Generic saved-contract validation and source ranges only. A scenario does not
        # rejudge old language, factual correctness or new source-semantic guard rules.
        assessment = Assessment.model_validate(deepcopy(raw))
        message_ids = [m["id"] for m in source.snapshot["transcript"]]
        original = score(saved, assessment, message_ids)
        if original != recorded_score:
            return {**result, "reasons": ["The saved score cannot be reproduced exactly; this run is unavailable for weight simulation."]}
        simulated = score(candidate, assessment, message_ids)
    except (ValidationError, ValueError, KeyError, TypeError):
        return {**result, "reasons": ["The saved judgments or evidence cannot be validated for this simulation."]}
    old_rows = {row["criterion_id"]: row for row in original["criteria"]}
    new_rows = {row["criterion_id"]: row for row in simulated["criteria"]}
    return {**result, "eligible": True, "updated_at": run.updated_at,
        "source": {"id": source.id, "source_id": source.source_id, "group_id": source.group_id,
                   "revision": source.revision, "content_hash": source.content_hash},
        "original_score": original, "simulated_score": simulated,
        "total_difference": numeric_difference(original["total"], simulated["total"]),
        "criteria": [{"criterion_id": c.id, "name": c.name, "answer_type": c.answer_type,
            "disposition": assessment.results[c.id].disposition, "value": assessment.results[c.id].value,
            "original": old_rows[c.id], "simulated": new_rows[c.id]} for c in saved.criteria]}
