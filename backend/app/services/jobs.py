from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import logging

from sqlalchemy import select

from backend.app.db import ChecklistVersion, Conversation, Evaluation, now
from backend.app.domain import Checklist
from backend.app.services.evaluator import Provider, cache_key, evaluation_metadata
from backend.app.services.scoring import score

log = logging.getLogger(__name__)


class Jobs:
    def __init__(self, db, settings, provider=None):
        self.db, self.settings = db, settings
        self.provider = provider or Provider(settings)
        self.executor = ThreadPoolExecutor(max_workers=settings.concurrency, thread_name_prefix="cqa-eval")

    def recover(self):
        with self.db.transaction() as session:
            for row in session.scalars(select(Evaluation).where(Evaluation.state == "running")):
                row.state, row.error, row.updated_at = "interrupted", "Backend restarted during a provider call; retry explicitly", now()
            queued = list(session.scalars(select(Evaluation.id).where(Evaluation.state == "queued")))
        for evaluation_id in queued:
            self.submit(evaluation_id)

    def create(self, conversation_ids, checklist_id, reuse_cache=True):
        if not self.settings.provider_ready:
            raise ValueError("Missing OPENAI_API_KEY or OPENAI_MODEL. Configure .env and restart; no evaluations were fabricated.")
        output, queued = [], []
        with self.db.transaction() as session:
            version = session.get(ChecklistVersion, checklist_id)
            if not version:
                raise ValueError("Checklist version does not exist")
            checklist = Checklist.model_validate(version.snapshot)
            conversations = [session.get(Conversation, cid) for cid in conversation_ids]
            if any(c is None for c in conversations):
                raise ValueError("One or more conversation revisions do not exist; batch not started")
            for conversation in conversations:
                key = cache_key(conversation.content_hash, checklist, self.settings)
                active = session.scalar(select(Evaluation).where(Evaluation.cache_key == key, Evaluation.conversation_id == conversation.id,
                                        Evaluation.checklist_id == checklist_id, Evaluation.state.in_(["queued", "running"])))
                if active:
                    output.append(active.id)
                    continue
                cached = (session.scalar(select(Evaluation).where(Evaluation.cache_key == key, Evaluation.state == "succeeded")
                          .order_by(Evaluation.created_at.desc())) if reuse_cache else None)
                row = Evaluation(conversation_id=conversation.id, checklist_id=checklist_id, cache_key=key,
                                 meta=evaluation_metadata(self.settings, checklist))
                row.meta["mode"] = self.provider.mode
                if cached and cached.original and cached.original_score:
                    row.state, row.completeness = "succeeded", cached.original_score["completeness"]
                    row.original, row.effective = deepcopy(cached.original), deepcopy(cached.original)
                    row.original_score, row.effective_score = deepcopy(cached.original_score), deepcopy(cached.original_score)
                    row.cached_from = cached.id
                session.add(row)
                session.flush()
                output.append(row.id)
                if row.state == "queued":
                    queued.append(row.id)
        for evaluation_id in queued:
            self.submit(evaluation_id)
        return output

    def retry(self, evaluation_id):
        if not self.settings.provider_ready:
            raise ValueError("Provider is not configured; no request sent")
        with self.db.transaction() as session:
            row = session.get(Evaluation, evaluation_id)
            if not row or row.state not in {"failed", "interrupted"}:
                raise ValueError("Only failed or interrupted evaluations can be retried")
            # A retry must use the same evaluator identity, otherwise create a new evaluation.
            version = session.get(ChecklistVersion, row.checklist_id)
            conversation = session.get(Conversation, row.conversation_id)
            if cache_key(conversation.content_hash, Checklist.model_validate(version.snapshot), self.settings) != row.cache_key:
                raise ValueError("Provider/model/settings changed; create a new evaluation to preserve audit metadata")
            row.state, row.error, row.updated_at = "queued", None, now()
        self.submit(evaluation_id)

    def submit(self, evaluation_id):
        self.executor.submit(self.run, evaluation_id)

    def run(self, evaluation_id):
        with self.db.transaction() as session:
            row = session.get(Evaluation, evaluation_id)
            if not row or row.state != "queued":
                return
            row.state, row.updated_at = "running", now()
            conversation = deepcopy(session.get(Conversation, row.conversation_id).snapshot)
            checklist = Checklist.model_validate(session.get(ChecklistVersion, row.checklist_id).snapshot)

        def record_attempt(update, index=None):
            with self.db.transaction() as session:
                item = session.get(Evaluation, evaluation_id)
                attempts = deepcopy(item.attempts)
                if index is None:
                    index = len(attempts)
                    attempts.append({"number": index + 1, "started_at": now(), **update})
                else:
                    attempts[index].update(update)
                item.attempts, item.updated_at = attempts, now()
            return index

        try:
            assessment = self.provider.evaluate(conversation, checklist, record_attempt)
            calculated = score(checklist, assessment, [m["id"] for m in conversation["transcript"]])
            original = assessment.model_dump(mode="json")
            with self.db.transaction() as session:
                row = session.get(Evaluation, evaluation_id)
                row.original, row.effective = original, deepcopy(original)
                row.original_score, row.effective_score = calculated, deepcopy(calculated)
                row.state, row.completeness, row.error, row.updated_at = "succeeded", calculated["completeness"], None, now()
        except Exception as error:
            # Known errors are purpose-written, safe messages. Never persist arbitrary HTTP/DB error strings.
            from backend.app.services.evaluator import EvaluationFailure
            safe_error = str(error) if isinstance(error, EvaluationFailure) else "Internal evaluation failure; no assessment saved; retry is available"
            log.warning("Evaluation %s failed (%s)", evaluation_id, type(error).__name__)
            with self.db.transaction() as session:
                row = session.get(Evaluation, evaluation_id)
                row.state, row.completeness, row.error, row.updated_at = "failed", "incomplete", safe_error, now()

    def close(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
