from copy import deepcopy
from sqlalchemy import select

from backend.app.db import Appeal, ChecklistVersion, Conversation, Evaluation, Review, now
from backend.app.domain import Assessment, Checklist, Judgment, nonblank, validate_judgment
from backend.app.services.scoring import score


def submit_appeal(db, evaluation_id, criterion_id, comment):
    nonblank(comment)
    with db.transaction() as session:
        evaluation = session.get(Evaluation, evaluation_id)
        if not evaluation or evaluation.state != "succeeded" or not evaluation.original:
            raise ValueError("Appeals require a saved assessment")
        if criterion_id not in evaluation.original["results"]:
            raise ValueError("Criterion is not in this evaluation's immutable checklist")
        appeal = Appeal(evaluation_id=evaluation_id, criterion_id=criterion_id, comment=comment)
        session.add(appeal)
        session.flush()
        return appeal.id


def decide(db, appeal_id, action, rationale, judgment, expected_updated_at):
    nonblank(rationale)
    with db.transaction() as session:
        appeal = session.get(Appeal, appeal_id)
        if not appeal or appeal.status != "open":
            raise ValueError("Appeal is missing or already decided")
        evaluation = session.get(Evaluation, appeal.evaluation_id)
        if evaluation.updated_at != expected_updated_at:
            raise ValueError("Evaluation changed during review; refresh before deciding")
        checklist = Checklist.model_validate(session.get(ChecklistVersion, evaluation.checklist_id).snapshot)
        conversation = session.get(Conversation, evaluation.conversation_id)
        criterion = next(c for c in checklist.criteria if c.id == appeal.criterion_id)
        # Rebuild from the immutable original and ordered audit history, never from a cached final result.
        effective = deepcopy(evaluation.original)
        for previous in session.scalars(select(Review).where(Review.evaluation_id == evaluation.id).order_by(Review.id)):
            effective["results"][previous.criterion_id] = deepcopy(previous.judgment)
        if action == "confirm":
            if judgment is not None:
                raise ValueError("Confirm does not accept a replacement judgment")
            replacement = Judgment.model_validate(effective["results"][criterion.id])
            if replacement.disposition == "needs_review":
                raise ValueError("An unresolved criterion cannot be confirmed; supply a supported replacement")
        elif action == "replace" and judgment is not None:
            replacement = judgment
        else:
            raise ValueError("Replace requires a complete validated judgment")
        # A correction may retract an unsupported answer when the source cannot establish it.
        # Preserve that missing basis instead of forcing No/N/A or retaining an invented Yes.
        message_ids = [m["id"] for m in conversation.snapshot["transcript"]]
        validate_judgment(criterion, replacement, message_ids)
        effective["results"][criterion.id] = replacement.model_dump(mode="json")
        calculated = score(checklist, Assessment.model_validate(effective), message_ids)
        review = Review(appeal_id=appeal.id, evaluation_id=evaluation.id, criterion_id=criterion.id,
                        action=action, rationale=rationale, judgment=replacement.model_dump(mode="json"), resulting_score=calculated)
        session.add(review)
        appeal.status = "open" if replacement.disposition == "needs_review" else "decided"
        evaluation.effective, evaluation.effective_score = effective, calculated
        evaluation.completeness, evaluation.updated_at = calculated["completeness"], now()
        session.flush()
        return review.id
