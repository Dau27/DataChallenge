"""Bounded, consistent saved-data selection shared by read-only insight tools."""
from typing import Annotated

from fastapi import HTTPException
from pydantic import Field, StringConstraints, field_validator
from sqlalchemy import exists, func, select
from sqlalchemy.orm import aliased

from backend.app.db import ChecklistVersion, Conversation, Evaluation
from backend.app.domain import Contract
from backend.app.services.saved_results import SavedResultNotFound, version_view


class SavedScope(Contract):
    checklist_id: int = Field(gt=0)
    conversation_ids: list[Annotated[str, StringConstraints(strict=True, min_length=1, max_length=200)]] = Field(max_length=200)

    @field_validator("conversation_ids")
    @classmethod
    def unique_ids(cls, values):
        if any(not value.strip() for value in values) or len(values) != len(set(values)):
            raise ValueError("Select unique, nonblank conversation revision IDs")
        return values


def load_scope(session, checklist_id, conversation_ids):
    """Use latest source revisions and latest runs, never an older successful fallback.

    The caller holds Database.read_snapshot for counts and their exact target set.
    Large transcripts, attempt history and provider metadata are not selected.
    """
    # Also validate direct service calls, not only API input.
    scope = SavedScope(checklist_id=checklist_id, conversation_ids=conversation_ids)
    version = session.get(ChecklistVersion, scope.checklist_id)
    if version is None:
        raise SavedResultNotFound("Checklist version not found")
    columns = (Conversation.id, Conversation.source_id, Conversation.group_id, Conversation.revision,
               Conversation.content_hash, Conversation.created_at,
               Conversation.snapshot["language"].as_string().label("language"),
               Conversation.snapshot["channel"].as_string().label("channel"))
    sources = {row["id"]: dict(row) for row in session.execute(select(*columns).where(Conversation.id.in_(scope.conversation_ids))).mappings()}
    if set(sources) != set(scope.conversation_ids):
        raise SavedResultNotFound("One or more selected conversation revisions were not found")
    newer = aliased(Conversation)
    stale = session.scalar(select(Conversation.id).where(Conversation.id.in_(scope.conversation_ids), exists(
        select(newer.id).where(newer.group_id == Conversation.group_id, newer.source_id == Conversation.source_id,
                               newer.revision > Conversation.revision))).limit(1))
    if stale:
        raise HTTPException(status_code=409, detail="Source revisions changed. Refresh the conversation queue before inspecting this selection.")
    ranked = select(Evaluation.id, func.row_number().over(partition_by=Evaluation.conversation_id,
        order_by=(Evaluation.created_at.desc(), Evaluation.id.desc())).label("position"))\
        .where(Evaluation.conversation_id.in_(scope.conversation_ids), Evaluation.checklist_id == scope.checklist_id).subquery()
    run_columns = (Evaluation.id, Evaluation.conversation_id, Evaluation.checklist_id, Evaluation.state,
                   Evaluation.completeness, Evaluation.created_at, Evaluation.updated_at, Evaluation.original,
                   Evaluation.effective, Evaluation.original_score, Evaluation.effective_score, Evaluation.error)
    runs = {row["conversation_id"]: dict(row) for row in session.execute(select(*run_columns)
        .join(ranked, ranked.c.id == Evaluation.id).where(ranked.c.position == 1)).mappings()}
    ordered = [sources[source_id] for source_id in scope.conversation_ids]
    manifest = [{"conversation_id": source["id"], "content_hash": source["content_hash"],
                 "evaluation_id": runs[source["id"]]["id"] if source["id"] in runs else None,
                 "updated_at": runs[source["id"]]["updated_at"] if source["id"] in runs else None,
                 "state": runs[source["id"]]["state"] if source["id"] in runs else "not_evaluated"} for source in ordered]
    return {"checklist": version_view(version), "sources": ordered, "runs": runs, "manifest": manifest}
