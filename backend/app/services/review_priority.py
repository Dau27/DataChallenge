"""Descriptive review reasons over saved results; no risk scoring or decisions."""
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import select, tuple_

from backend.app.db import Appeal, Conversation, Evaluation
from backend.app.services.insights_common import load_scope


LABELS = {
    "open_appeal": "Open appeal", "needs_review": "Unresolved or unavailable judgment",
    "critical_true": "Recorded critical finding", "critical_unknown": "Critical status unknown",
    "failed": "Failed evaluation", "interrupted": "Interrupted evaluation",
    "not_evaluated": "Not evaluated", "in_progress": "Evaluation in progress",
}


def _date_key(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()
    except (ValueError, AttributeError, OverflowError):
        return float("inf")


def review_priority(session, checklist_id, conversation_ids):
    scope = load_scope(session, checklist_id, conversation_ids)
    criteria = {c["id"]: c for c in scope["checklist"]["snapshot"]["criteria"]}
    flag_ids = [cid for cid, c in criteria.items() if c["answer_type"] == "flag"]
    identities = [(s["group_id"], s["source_id"]) for s in scope["sources"]]
    appeals = {}
    if identities:
        query = select(Appeal.id.label("appeal_id"), Appeal.criterion_id, Appeal.created_at,
                       Evaluation.id.label("evaluation_id"), Conversation.id.label("conversation_id"),
                       Conversation.group_id, Conversation.source_id).join(Evaluation, Evaluation.id == Appeal.evaluation_id)\
            .join(Conversation, Conversation.id == Evaluation.conversation_id).where(
                Appeal.status == "open", Evaluation.checklist_id == checklist_id,
                tuple_(Conversation.group_id, Conversation.source_id).in_(identities))\
            .order_by(Appeal.created_at, Appeal.id)
        for row in session.execute(query).mappings():
            appeals.setdefault((row["group_id"], row["source_id"]), []).append(dict(row))
    items = []
    counts = Counter({code: 0 for code in LABELS})
    for source in scope["sources"]:
        run = scope["runs"].get(source["id"])
        state = run["state"] if run else "not_evaluated"
        assessment = run.get("effective") if run and state == "succeeded" else None
        results = assessment.get("results") if isinstance(assessment, dict) else {}
        if not isinstance(results, dict):
            results = {}
        reasons = []
        def target(cid):
            return {"conversation_id": source["id"], "evaluation_id": run["id"] if run else None,
                    "criterion_id": cid, "criterion_name": criteria.get(cid, {}).get("name", cid)}
        def add(code, targets, since):
            reasons.append({"code": code, "label": LABELS[code], "since": since, "targets": targets})
            counts[code] += 1
        pending = appeals.get((source["group_id"], source["source_id"]), [])
        if pending:
            add("open_appeal", [{**{k: row[k] for k in ("appeal_id", "conversation_id", "evaluation_id", "criterion_id")},
                                 "criterion_name": criteria.get(row["criterion_id"], {}).get("name", row["criterion_id"])}
                                for row in pending], min((row["created_at"] for row in pending), key=_date_key))
        since = run["updated_at"] if run else source["created_at"]
        unresolved = [cid for cid in criteria if isinstance(results.get(cid), dict) and results[cid].get("disposition") == "needs_review"]
        unavailable = [cid for cid in criteria if not isinstance(results.get(cid), dict)
                       or results[cid].get("disposition") not in {"assessed", "not_applicable", "needs_review"}]
        if run and state == "succeeded" and (unresolved or unavailable or run.get("completeness") != "complete"):
            add("needs_review", [target(cid) for cid in dict.fromkeys(unresolved + unavailable)] or [target(None)], since)
        flags = {"true": 0, "false": 0, "unknown": 0}
        flag_targets = {"true": [], "unknown": []}
        for cid in flag_ids:
            judgment = results.get(cid)
            value = judgment.get("value") if isinstance(judgment, dict) and judgment.get("disposition") == "assessed" else None
            status = "true" if value is True else "false" if value is False else "unknown"
            flags[status] += 1
            if status in flag_targets:
                flag_targets[status].append(target(cid))
        for status, code in (("true", "critical_true"), ("unknown", "critical_unknown")):
            if flag_targets[status]:
                add(code, flag_targets[status], since)
        if state in {"failed", "interrupted", "not_evaluated"}:
            add(state, [target(None)], since)
        elif state in {"queued", "running"}:
            add("in_progress", [target(None)], since)
        dates = [r["since"] for r in reasons if r["since"]]
        items.append({"conversation_id": source["id"], "source_id": source["source_id"], "group_id": source["group_id"],
                      "evaluation_id": run["id"] if run else None, "state": state, "reasons": reasons,
                      "flag_counts": flags, "configured_flags": len(flag_ids),
                      "oldest_reason_at": min(dates, key=_date_key) if dates else since})
    return {"checklist_id": checklist_id, "basis": "effective", "manifest": scope["manifest"],
            "counts": dict(counts), "items": items,
            "notice": "Reasons describe saved states, not a risk score or operator penalty. Unknown critical status is not a clean result."}
