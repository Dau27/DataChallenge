"""Latest saved summaries and pending review targets; never load assessment history."""
from sqlalchemy import exists, func, select
from sqlalchemy.orm import aliased

from backend.app.db import Appeal, ChecklistVersion, Conversation, Evaluation
from backend.app.services.saved_results import summary_columns
from backend.app.services.search import search_messages
from backend.app.services.transcript_index import narrow_sources


def conversation_queue(session, checklist_id=None, latest_only=True, q="", speaker="all"):
    sources = select(Conversation)
    if latest_only:
        newer = aliased(Conversation)
        sources = sources.where(~exists(select(newer.id).where(
            newer.group_id == Conversation.group_id, newer.source_id == Conversation.source_id,
            newer.revision > Conversation.revision)))
    sources = narrow_sources(session, sources, q, speaker)
    source_ids = sources.with_only_columns(Conversation.id).subquery()
    records = list(session.scalars(sources.order_by(Conversation.group_id, Conversation.source_id, Conversation.revision.desc())))

    ranked = select(Evaluation.id.label("evaluation_id"),
        func.row_number().over(partition_by=Evaluation.conversation_id,
            order_by=(Evaluation.created_at.desc(), Evaluation.id.desc())).label("position")).join(
                source_ids, Evaluation.conversation_id == source_ids.c.id)
    if checklist_id is not None:
        ranked = ranked.where(Evaluation.checklist_id == checklist_id)
    ranked = ranked.subquery()
    winning = select(*summary_columns(), Evaluation.effective_score["flags"].label("flags")).join(
        ranked, ranked.c.evaluation_id == Evaluation.id).where(ranked.c.position == 1)
    latest = {row["conversation_id"]: dict(row) for row in session.execute(winning).mappings()}

    pending_query = select(Appeal.id.label("appeal_id"), Appeal.criterion_id, Evaluation.id.label("evaluation_id"),
        Evaluation.checklist_id, Conversation.id.label("conversation_id"), Conversation.group_id, Conversation.source_id).join(
            Evaluation, Evaluation.id == Appeal.evaluation_id).join(Conversation, Conversation.id == Evaluation.conversation_id).where(
                Appeal.status == "open").order_by(Appeal.created_at, Appeal.id)
    if checklist_id is not None:
        pending_query = pending_query.where(Evaluation.checklist_id == checklist_id)
    appeals = list(session.execute(pending_query).mappings())
    needed_versions = {row["checklist_id"] for row in latest.values()} | {row["checklist_id"] for row in appeals}
    versions = {row.id: {c["id"]: c["name"] for c in row.snapshot["criteria"]}
                for row in session.execute(select(ChecklistVersion.id, ChecklistVersion.snapshot).where(ChecklistVersion.id.in_(needed_versions)))}

    pending = {}
    for appeal in appeals:
        identity = (appeal["group_id"], appeal["source_id"]) if latest_only else appeal["conversation_id"]
        pending.setdefault(identity, []).append({"appeal_id": appeal["appeal_id"], "conversation_id": appeal["conversation_id"],
            "evaluation_id": appeal["evaluation_id"], "criterion_id": appeal["criterion_id"],
            "criterion_name": versions[appeal["checklist_id"]][appeal["criterion_id"]]})

    items = []
    for source in records:
        matches, match_count = search_messages(source.snapshot["transcript"], q, speaker)
        if (q.strip() or speaker != "all") and not match_count:
            continue
        saved = latest.get(source.id)
        flags = [{"evaluation_id": saved["id"], "criterion_id": cid, "criterion_name": versions[saved["checklist_id"]][cid]}
                 for cid, value in (saved["flags"] or {}).items() if value is True] if saved else []
        identity = (source.group_id, source.source_id) if latest_only else source.id
        targets = pending.get(identity, [])
        items.append({"id": source.id, "group_id": source.group_id, "source_id": source.source_id, "revision": source.revision,
            "content_hash": source.content_hash, "language": source.snapshot["language"], "channel": source.snapshot["channel"],
            "message_count": len(source.snapshot["transcript"]), "audio_available": bool(source.snapshot["audio_url"]),
            "evaluation": {key: value for key, value in saved.items() if key != "flags"} if saved else None,
            "created_at": source.created_at, "pending_appeals": len(targets), "pending_review_targets": targets,
            "critical_findings": flags, "search_matches": matches, "search_total_matches": match_count})
    return items
