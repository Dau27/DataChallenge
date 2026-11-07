from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import logging

from sqlalchemy import select

from backend.app.db import BudgetReservation, ChecklistVersion, Conversation, Evaluation, now
from backend.app.domain import Checklist
from backend.app.services.evaluator import Provider, cache_key, evaluation_metadata, output_schema
from backend.app.domain import content_hash
from backend.app.services.scoring import score
from backend.app.services.budget import Budget, BudgetError, evaluation_bound, rate_for

log = logging.getLogger(__name__)


class Jobs:
    def __init__(self, db, settings, provider=None):
        self.db, self.settings = db, settings
        self.provider = provider or Provider(settings)
        self.budget = Budget(db, settings)
        self.executor = ThreadPoolExecutor(max_workers=settings.concurrency, thread_name_prefix="cqa-eval")

    def recover(self):
        with self.db.transaction() as session:
            for row in session.scalars(select(Evaluation).where(Evaluation.state == "running")):
                row.state, row.error, row.updated_at = "interrupted", "Backend restarted during a provider call; retry explicitly", now()
            queued = list(session.scalars(select(Evaluation.id).where(Evaluation.state == "queued")))
        self.budget.recover()
        for evaluation_id in queued:
            self.submit(evaluation_id)

    def plan(self, session, conversation_ids, checklist_id, reuse_cache=True):
        version = session.get(ChecklistVersion, checklist_id)
        if not version:
            raise ValueError("Checklist version does not exist")
        checklist = Checklist.model_validate(version.snapshot)
        plan = []
        for cid in conversation_ids:
            conversation = session.get(Conversation, cid)
            if not conversation:
                raise ValueError("One or more conversation revisions do not exist; batch not started")
            key = cache_key(conversation.content_hash, checklist, self.settings)
            active = session.scalar(select(Evaluation).where(Evaluation.cache_key == key, Evaluation.conversation_id == cid,
                                    Evaluation.checklist_id == checklist_id, Evaluation.state.in_(["queued", "running"])))
            cached = (session.scalar(select(Evaluation).where(Evaluation.cache_key == key, Evaluation.state == "succeeded")
                      .order_by(Evaluation.created_at.desc())) if reuse_cache and not active else None)
            if cached and not (cached.original and cached.original_score):
                cached = None
            amount = evaluation_bound(self.settings, conversation.snapshot, checklist) if not (active or cached) else 0
            plan.append((conversation, key, active, cached, amount))
        return checklist, plan

    def preview(self, conversation_ids, checklist_id, reuse_cache=True):
        with self.db.sessions() as session:
            status = self.budget.status(session)
            amount, cached_count, active_count, new_count, reason = None, 0, 0, len(conversation_ids), None
            try:
                _, plan = self.plan(session, conversation_ids, checklist_id, reuse_cache)
                amount = sum(p[4] for p in plan)
                cached_count, active_count = sum(bool(p[3]) for p in plan), sum(bool(p[2]) for p in plan)
                new_count = sum(not (p[2] or p[3]) for p in plan)
                if new_count:
                    self.budget.check(session, amount)
            except BudgetError as error:
                reason = str(error)
            return {"required_reservation_usd": str(amount) if amount is not None else None,
                    "cached": cached_count, "active": active_count, "new_evaluations": new_count,
                    "affordable": reason is None, "blocked_reason": reason, "budget": status}

    def create(self, conversation_ids, checklist_id, reuse_cache=True):
        if not self.settings.provider_ready:
            raise ValueError("Missing OPENAI_API_KEY or OPENAI_MODEL. Configure .env and restart; no evaluations were fabricated.")
        output, queued = [], []
        with self.db.transaction() as session:
            checklist, plan = self.plan(session, conversation_ids, checklist_id, reuse_cache)
            total = sum(item[4] for item in plan)
            if any(not (item[2] or item[3]) for item in plan):
                self.budget.check(session, total)
            for conversation, key, active, cached, amount in plan:
                if active:
                    output.append(active.id)
                    continue
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
                    self.budget.reserve(session, "evaluation", row.id, amount, 4)
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
            if row.meta.get("rate") != rate_for(self.settings):
                raise ValueError("Cost rates changed; create a new evaluation to preserve per-attempt cost provenance")
            self.budget.reserve(session, "evaluation", row.id,
                                evaluation_bound(self.settings, conversation.snapshot, Checklist.model_validate(version.snapshot)),
                                4, attempt_offset=len(row.attempts))
            row.state, row.error, row.updated_at = "queued", None, now()
        self.submit(evaluation_id)

    def submit(self, evaluation_id):
        self.executor.submit(self.run, evaluation_id)

    def run(self, evaluation_id):
        refused = False
        reservation_id = None
        with self.db.transaction() as session:
            row = session.get(Evaluation, evaluation_id)
            if not row or row.state != "queued":
                return
            row.state, row.updated_at = "running", now()
            source = session.get(Conversation, row.conversation_id)
            conversation = deepcopy(source.snapshot)
            checklist = Checklist.model_validate(session.get(ChecklistVersion, row.checklist_id).snapshot)
            entry = session.scalar(select(BudgetReservation).where(BudgetReservation.source_id == row.id,
                                   BudgetReservation.kind == "evaluation", BudgetReservation.state == "reserved")
                                   .order_by(BudgetReservation.created_at.desc()))
            if not entry or cache_key(source.content_hash, checklist, self.settings) != row.cache_key:
                row.state, row.error = "interrupted", "No compatible live budget reservation; retry or create a new evaluation"
                refused = True
            if entry:
                reservation_id = entry.id
            if not refused:
                row.meta = {**row.meta, "request_schema_hash": content_hash(output_schema(checklist, [m["id"] for m in conversation["transcript"]]))}
        if refused:
            if reservation_id:
                self.budget.settle(reservation_id)
            return
        record_attempt = self.budget.recorder(reservation_id)

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
            safe_error = str(error) if isinstance(error, (EvaluationFailure, BudgetError)) else "Internal evaluation failure; no assessment saved; retry is available"
            log.warning("Evaluation %s failed (%s)", evaluation_id, type(error).__name__)
            with self.db.transaction() as session:
                row = session.get(Evaluation, evaluation_id)
                row.state, row.completeness, row.error, row.updated_at = "failed", "incomplete", safe_error, now()
        finally:
            self.budget.settle(reservation_id)

    def close(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
