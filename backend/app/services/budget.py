"""Persistent shared spending reservations. All money is Decimal; default ceiling is zero."""
from copy import deepcopy
from decimal import Decimal
import json

from sqlalchemy import select

from backend.app.db import AccessCheck, BudgetReservation, BudgetState, Evaluation, now
from backend.app.domain import canonical_json, content_hash
from backend.app.services.evaluator import evaluation_payload

ZERO = Decimal("0")


class BudgetError(ValueError):
    pass


def money(value):
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError("Budget amounts must be finite and nonnegative")
    return result


def rate_for(settings):
    if settings.input_rate is None or settings.output_rate is None or not settings.rate_source:
        raise BudgetError("Identified input/output cost rates are required before paid requests")
    return {"input_usd_per_million": str(settings.input_rate), "output_usd_per_million": str(settings.output_rate),
            "source": settings.rate_source}


def cost(input_tokens, output_tokens, rate):
    return (money(input_tokens) * money(rate["input_usd_per_million"]) +
            money(output_tokens) * money(rate["output_usd_per_million"])) / Decimal(1_000_000)


def request_bound(settings, payload, attempts=2, repair=False):
    # Match Provider.request's byte bound. Reserve 8192 extra UTF-8 bytes for its
    # bounded 1500-character repair feedback plus framing on every possible attempt.
    rate = rate_for(settings)
    upper = len(canonical_json(payload).encode("utf-8")) + 4096 + (8192 if repair else 0)
    return attempts * cost(upper, payload["max_output_tokens"], rate)


def evaluation_bound(settings, conversation, checklist):
    payload = evaluation_payload(settings, conversation, checklist)
    if len(canonical_json(payload)) > settings.max_input_characters:
        raise BudgetError("Full request exceeds the input safeguard; no request will be sent")
    return request_bound(settings, payload, attempts=4, repair=True)


def attempt_accounting(attempts, rate):
    total, unknown = ZERO, False
    for attempt in attempts:
        known = type(attempt.get("input_tokens")) is int and type(attempt.get("output_tokens")) is int
        total += cost(attempt["input_tokens"] if known else attempt["input_token_upper_bound"],
                      attempt["output_tokens"] if known else attempt["max_output_tokens"], rate)
        unknown |= not known
    return total, unknown


class Budget:
    def __init__(self, db, settings):
        self.db, self.settings = db, settings
        self.bootstrap_error = None
        with db.transaction() as session:
            if session.get(BudgetState, 1) is not None:
                return
            path = settings.budget_baseline_path
            if path and path.exists():
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    if set(raw) != {"schema_version", "opening_usd", "coverage", "provenance"} or raw["schema_version"] != 1:
                        raise ValueError("Invalid baseline format")
                    if set(raw["coverage"]) != {"evaluations", "access_checks"}:
                        raise ValueError("Invalid coverage")
                    if not all(isinstance(raw["coverage"][key], dict) for key in ("evaluations", "access_checks")):
                        raise ValueError("Invalid coverage maps")
                    if not isinstance(raw["provenance"], str) or not raw["provenance"].strip():
                        raise ValueError("Missing provenance")
                    state = BudgetState(id=1, opening_usd=str(money(raw["opening_usd"])),
                                        coverage=raw["coverage"], provenance=raw["provenance"])
                    reason = self.history_error(session, state)
                    if reason:
                        raise ValueError(reason)
                    session.add(state)
                except (ValueError, TypeError, KeyError, OSError, ArithmeticError):
                    self.bootstrap_error = "Historical budget baseline is invalid; paid requests are paused"
            elif any(row.attempts for row in session.scalars(select(Evaluation))) or session.scalar(select(AccessCheck.identity_hash).limit(1)):
                self.bootstrap_error = "Recorded provider history needs a reviewed budget baseline; paid requests are paused"
            else:
                session.add(BudgetState(id=1, opening_usd="0", coverage={"evaluations": {}, "access_checks": {}},
                                        provenance="Fresh database; no recorded provider attempts"))

    def history_error(self, session, state):
        """No historical request can silently disappear or be counted twice."""
        reservations = list(session.scalars(select(BudgetReservation).order_by(BudgetReservation.created_at, BudgetReservation.id)))
        grouped = {}
        for reservation in reservations:
            grouped.setdefault(reservation.source_id, []).append(reservation)
        try:
            covered_amount = ZERO
            for evaluation in session.scalars(select(Evaluation)):
                baseline = state.coverage["evaluations"].get(evaluation.id)
                cursor = 0
                if baseline:
                    cursor = baseline["attempt_count"]
                    if (type(cursor) is not int or cursor < 0 or cursor > len(evaluation.attempts)
                            or content_hash(evaluation.attempts[:cursor]) != baseline["attempts_hash"]
                            or content_hash(evaluation.meta) != baseline["metadata_hash"]):
                        return "Historical evaluation accounting changed; reconcile the budget baseline"
                    declared = money(baseline["accounted_usd"])
                    covered_amount += declared
                    rates = evaluation.meta.get("rate", {})
                    if rates.get("input_usd_per_million") is not None and rates.get("output_usd_per_million") is not None:
                        minimum = ZERO
                        for attempt in evaluation.attempts[:cursor]:
                            if type(attempt.get("input_tokens")) is int and type(attempt.get("output_tokens")) is int:
                                minimum += cost(attempt["input_tokens"], attempt["output_tokens"], rates)
                            elif attempt.get("input_token_upper_bound") is not None and attempt.get("max_output_tokens") is not None:
                                minimum += cost(attempt["input_token_upper_bound"], attempt["max_output_tokens"], rates)
                            elif declared == 0:
                                return "Unknown historical usage cannot be booked as free"
                        if declared < minimum:
                            return "Historical baseline understates saved usage/reservations"
                for entry in sorted((r for r in grouped.get(evaluation.id, []) if r.kind == "evaluation"), key=lambda r: (r.attempt_offset, r.created_at)):
                    if entry.attempt_offset != cursor or evaluation.attempts[cursor:cursor + len(entry.attempts)] != entry.attempts:
                        return "Evaluation attempts do not match the shared budget ledger"
                    cursor += len(entry.attempts)
                if cursor != len(evaluation.attempts):
                    return "Unaccounted provider attempts need a reviewed budget baseline"
            if covered_amount > money(state.opening_usd):
                return "Historical opening amount is below its covered usage/reservations"
            for check in session.scalars(select(AccessCheck)):
                digest = content_hash(check.report)
                if digest != state.coverage["access_checks"].get(check.identity_hash) and not any(
                        r.kind == "access_check" and r.report_hash == digest for r in grouped.get(check.identity_hash, [])):
                    return "Unaccounted access-check usage needs a reviewed budget baseline"
        except (KeyError, TypeError, ValueError, ArithmeticError):
            return "Historical budget coverage is invalid; paid requests are paused"
        return None

    def status(self, session=None):
        if session is None:
            with self.db.sessions() as current:
                return self.status(current)
        state = session.get(BudgetState, 1)
        reason = self.bootstrap_error or (self.history_error(session, state) if state else "Budget baseline is unavailable")
        opening = money(state.opening_usd) if state else ZERO
        settled, held = ZERO, ZERO
        for entry in session.scalars(select(BudgetReservation)):
            if entry.state == "reserved":
                held += max(money(entry.reserved_usd), attempt_accounting(entry.attempts, entry.rate)[0])
            else:
                settled += money(entry.accounted_usd)
        accounted = opening + settled
        available = max(ZERO, self.settings.budget_limit_usd - accounted - held - self.settings.budget_overhead_usd)
        if not reason and self.settings.budget_limit_usd == 0:
            reason = "Paid requests are paused by the zero spending limit"
        if not reason and accounted + held + self.settings.budget_overhead_usd > self.settings.budget_limit_usd:
            reason = "Recorded estimates and reservations exceed the shared spending limit"
        if not reason and (self.settings.input_rate is None or self.settings.output_rate is None or not self.settings.rate_source):
            reason = "Identified input/output cost rates are required before paid requests"
        return {"limit_usd": str(self.settings.budget_limit_usd), "opening_accounted_usd": str(opening),
                "accounted_usd": str(accounted), "reserved_usd": str(held),
                "overhead_usd": str(self.settings.budget_overhead_usd), "available_usd": str(available),
                "ready": not reason, "blocked_reason": reason, "estimate_only": True}

    def check(self, session, amount):
        status = self.status(session)
        if status["blocked_reason"]:
            raise BudgetError(status["blocked_reason"])
        if amount > money(status["available_usd"]):
            raise BudgetError(f"Shared spending limit: reserve ${amount:.6f}, available ${money(status['available_usd']):.6f}. No request sent")

    def reserve(self, session, kind, source_id, amount, max_attempts, attempt_offset=0):
        self.check(session, amount)
        entry = BudgetReservation(kind=kind, source_id=source_id, reserved_usd=str(amount), rate=rate_for(self.settings),
                                  max_attempts=max_attempts, attempt_offset=attempt_offset)
        session.add(entry)
        session.flush()
        return entry.id

    def recorder(self, reservation_id):
        def record(update, index=None):
            with self.db.transaction() as session:
                entry = session.get(BudgetReservation, reservation_id)
                if entry is None or entry.state != "reserved":
                    raise BudgetError("A live budget reservation is required; no request sent")
                attempts = deepcopy(entry.attempts)
                if index is None:
                    self.check(session, ZERO)
                    if entry.rate != rate_for(self.settings):
                        raise BudgetError("Cost rates changed since reservation; no request sent")
                    if len(attempts) >= entry.max_attempts:
                        raise BudgetError("Reserved request-attempt limit reached; no request sent")
                    bound = cost(update["input_token_upper_bound"], update["max_output_tokens"], entry.rate)
                    used_bounds = sum((cost(a["input_token_upper_bound"], a["max_output_tokens"], entry.rate) for a in attempts), ZERO)
                    if used_bounds + bound > money(entry.reserved_usd):
                        raise BudgetError("Request exceeds its reserved cost bound; no request sent")
                    local_index = len(attempts)
                    attempts.append({"number": entry.attempt_offset + local_index + 1, "started_at": now(), **update})
                else:
                    local_index = len(attempts) - 1 if index == -1 else index - entry.attempt_offset
                    attempts[local_index].update(update)
                entry.attempts, entry.updated_at = attempts, now()
                if entry.kind == "evaluation":
                    evaluation = session.get(Evaluation, entry.source_id)
                    evaluation.attempts = evaluation.attempts[:entry.attempt_offset] + deepcopy(attempts)
                    evaluation.updated_at = now()
                return entry.attempt_offset + local_index
        record.budget_guarded = True
        return record

    def settle(self, reservation_id, report=None):
        with self.db.transaction() as session:
            entry = session.get(BudgetReservation, reservation_id)
            if entry is None or entry.state != "reserved":
                return
            amount, unknown = attempt_accounting(entry.attempts, entry.rate)
            entry.accounted_usd, entry.state, entry.updated_at = str(amount), "unknown" if unknown else "settled", now()
            if report is not None:
                entry.report_hash = content_hash(report)
                session.merge(AccessCheck(identity_hash=entry.source_id, report=report))

    def recover(self):
        with self.db.sessions() as session:
            entries = list(session.scalars(select(BudgetReservation).where(BudgetReservation.state == "reserved")
                                          .order_by(BudgetReservation.created_at)))
            latest = {r.source_id: r.id for r in entries if r.kind == "evaluation"}
            ids = [r.id for r in entries if r.kind == "access_check" or not (e := session.get(Evaluation, r.source_id))
                   or e.state != "queued" or latest.get(r.source_id) != r.id]
        for reservation_id in ids:
            self.settle(reservation_id)
